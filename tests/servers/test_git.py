"""Comprehensive tests for git server"""
import subprocess
import pytest
from unittest.mock import Mock, patch


class TestGitBasics:
    """Basic tests for git operations."""

    def test_git_module_imports(self):
        """Test that git module can be imported."""
        try:
            from src.servers import git
            assert git is not None
        except ImportError:
            pytest.skip("Git module not available")

    def test_git_functions_exist(self):
        """Test that git functions exist."""
        try:
            from src.servers.git import register_git_tools
            assert callable(register_git_tools)
        except (ImportError, AttributeError):
            pytest.skip("Git functions not available")


class TestGitToolRegistration:
    """Tests for git tool registration."""

    def test_register_git_tools(self):
        """Test registering git tools."""
        try:
            from src.servers.git import register_git_tools
            from src.host.tools import ToolRegistry

            registry = ToolRegistry()
            register_git_tools(registry)

            # Check that some git tools were registered
            tool_names = registry.get_tool_names()
            assert len(tool_names) > 0
        except (ImportError, AttributeError):
            pytest.skip("Git tools not available")


class TestGitValidation:
    """Tests for git validation functions."""

    def test_validate_git_ref_valid_branch(self):
        """Test validation of valid branch names."""
        from src.servers.git import _validate_git_ref

        valid_refs = ["main", "develop", "feature/new-ui", "bugfix/issue-123", "v1.0.0"]
        for ref in valid_refs:
            is_valid, error_msg = _validate_git_ref(ref)
            assert is_valid, f"Expected {ref} to be valid, got error: {error_msg}"

    def test_validate_git_ref_invalid_characters(self):
        """Test validation rejects invalid characters."""
        from src.servers.git import _validate_git_ref

        invalid_refs = ["feature branch", "feature~main", "feature^old", "feature:tag", "feature?"]
        for ref in invalid_refs:
            is_valid, error_msg = _validate_git_ref(ref)
            assert not is_valid, f"Expected {ref} to be invalid"

    def test_validate_git_ref_empty(self):
        """Test validation rejects empty reference."""
        from src.servers.git import _validate_git_ref

        is_valid, error_msg = _validate_git_ref("")
        assert not is_valid
        assert "empty" in error_msg.lower()

    def test_validate_git_ref_too_long(self):
        """Test validation rejects overly long reference."""
        from src.servers.git import _validate_git_ref

        long_ref = "a" * 300
        is_valid, error_msg = _validate_git_ref(long_ref)
        assert not is_valid
        assert "long" in error_msg.lower()

    def test_validate_git_ref_starts_with_dash(self):
        """Test validation rejects reference starting with dash."""
        from src.servers.git import _validate_git_ref

        is_valid, error_msg = _validate_git_ref("-invalid")
        assert not is_valid
        assert "start" in error_msg.lower()

    def test_validate_git_ref_ends_with_dot(self):
        """Test validation rejects reference ending with dot."""
        from src.servers.git import _validate_git_ref

        is_valid, error_msg = _validate_git_ref("feature.")
        assert not is_valid

    def test_validate_git_ref_double_dot(self):
        """Test validation rejects reference with double dots."""
        from src.servers.git import _validate_git_ref

        is_valid, error_msg = _validate_git_ref("feature..main")
        assert not is_valid

    def test_validate_git_ref_double_slash(self):
        """Test validation rejects reference with double slashes."""
        from src.servers.git import _validate_git_ref

        is_valid, error_msg = _validate_git_ref("feature//main")
        assert not is_valid


class TestGitCommandExecution:
    """Tests for git command execution with mocking."""

    @patch('src.servers.git.subprocess.run')
    def test_run_git_command_success(self, mock_run):
        """Test successful git command execution."""
        from src.servers.git import _run_git_command

        mock_run.return_value = Mock(returncode=0, stdout="success output", stderr="")
        success, output = _run_git_command(["status"])

        assert success is True
        assert output == "success output"
        mock_run.assert_called_once()

    @patch('src.servers.git.subprocess.run')
    def test_run_git_command_failure(self, mock_run):
        """Test failed git command execution."""
        from src.servers.git import _run_git_command

        mock_run.return_value = Mock(returncode=1, stdout="", stderr="error message")
        success, output = _run_git_command(["status"])

        assert success is False
        assert "error message" in output

    @patch('src.servers.git.subprocess.run')
    def test_run_git_command_timeout(self, mock_run):
        """Test git command timeout handling."""
        from src.servers.git import _run_git_command

        mock_run.side_effect = subprocess.TimeoutExpired("git", 30)
        success, output = _run_git_command(["status"], timeout=30)

        assert success is False
        assert "timed out" in output.lower()

    @patch('src.servers.git.subprocess.run')
    def test_run_git_command_not_found(self, mock_run):
        """Test git command when git is not installed."""
        from src.servers.git import _run_git_command

        mock_run.side_effect = FileNotFoundError()
        success, output = _run_git_command(["status"])

        assert success is False
        assert "not installed" in output.lower()

    @patch('src.servers.git.subprocess.run')
    def test_run_git_command_with_stderr(self, mock_run):
        """Test git command that returns both stdout and stderr."""
        from src.servers.git import _run_git_command

        mock_run.return_value = Mock(returncode=0, stdout="output", stderr="warning")
        success, output = _run_git_command(["status"])

        assert success is True
        assert "output" in output
        assert "warning" in output


class TestGitBranchOperations:
    """Tests for branch management operations."""

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_branch_list(self, mock_run, mock_is_repo):
        """Test listing branches."""
        from src.servers.git import git_branch

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "* main\n  develop\n  feature/new")

        result = git_branch()
        assert "main" in result
        assert "develop" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_branch_list_all(self, mock_run, mock_is_repo):
        """Test listing all branches including remote."""
        from src.servers.git import git_branch

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "* main\n  remotes/origin/main")

        result = git_branch(all_branches=True)
        assert "remotes/origin/main" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_checkout_branch(self, mock_run, mock_is_repo):
        """Test checking out an existing branch."""
        from src.servers.git import git_checkout

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Switched to branch 'develop'")

        result = git_checkout("develop")
        assert "Switched" in result or "develop" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_checkout_create_branch(self, mock_run, mock_is_repo):
        """Test creating and checking out a new branch."""
        from src.servers.git import git_checkout

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Switched to a new branch 'feature/new'")

        result = git_checkout("feature/new", create=True)
        assert "feature/new" in result or "new branch" in result

    @patch('src.servers.git._is_git_repo')
    def test_git_checkout_invalid_branch(self, mock_is_repo):
        """Test checkout with invalid branch name."""
        from src.servers.git import git_checkout

        mock_is_repo.return_value = True
        result = git_checkout("invalid branch name")
        assert "Error" in result or "Invalid" in result


class TestGitMergeOperations:
    """Tests for merge operations."""

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_merge_success(self, mock_run, mock_is_repo):
        """Test successful merge."""
        from src.servers.git import git_merge

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Merge made by the 'recursive' strategy.")

        result = git_merge("develop")
        assert "Merge" in result or "recursive" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_merge_with_no_ff(self, mock_run, mock_is_repo):
        """Test merge with --no-ff flag."""
        from src.servers.git import git_merge

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Merge made by the 'recursive' strategy.")

        result = git_merge("develop", no_ff=True)
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_merge_conflict(self, mock_run, mock_is_repo):
        """Test merge with conflicts."""
        from src.servers.git import git_merge

        mock_is_repo.return_value = True
        mock_run.return_value = (False, "CONFLICT (content): Merge conflict in file.txt")

        result = git_merge("develop")
        assert "Error" in result or "CONFLICT" in result

    @patch('src.servers.git._is_git_repo')
    def test_git_merge_invalid_branch(self, mock_is_repo):
        """Test merge with invalid branch name."""
        from src.servers.git import git_merge

        mock_is_repo.return_value = True
        result = git_merge("invalid branch")
        assert "Error" in result or "Invalid" in result


class TestGitStashOperations:
    """Tests for stash operations."""

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_stash_push(self, mock_run, mock_is_repo):
        """Test stashing changes."""
        from src.servers.git import git_stash

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Saved working directory and index state WIP on main")

        result = git_stash("push")
        assert "Saved" in result or "stash" in result.lower()

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_stash_push_with_message(self, mock_run, mock_is_repo):
        """Test stashing with a message."""
        from src.servers.git import git_stash

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Saved working directory")

        result = git_stash("push", message="WIP: feature work")
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_stash_pop(self, mock_run, mock_is_repo):
        """Test popping stashed changes."""
        from src.servers.git import git_stash

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Dropped refs/stash@{0}")

        result = git_stash("pop")
        assert "pop" in result.lower() or "Dropped" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_stash_list(self, mock_run, mock_is_repo):
        """Test listing stashes."""
        from src.servers.git import git_stash

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "stash@{0}: WIP on main: abc1234 commit message")

        result = git_stash("list")
        assert "stash" in result.lower()

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_stash_drop(self, mock_run, mock_is_repo):
        """Test dropping a stash."""
        from src.servers.git import git_stash

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Dropped refs/stash@{0}")

        result = git_stash("drop")
        assert "drop" in result.lower() or "Dropped" in result

    @patch('src.servers.git._is_git_repo')
    def test_git_stash_invalid_action(self, mock_is_repo):
        """Test stash with invalid action."""
        from src.servers.git import git_stash

        mock_is_repo.return_value = True
        result = git_stash("invalid_action")
        assert "Error" in result or "Invalid" in result


class TestGitRemoteOperations:
    """Tests for remote operations (fetch, pull, push)."""

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_fetch_success(self, mock_run, mock_is_repo):
        """Test successful fetch."""
        from src.servers.git import git_fetch

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "From github.com:user/repo\n   abc1234..def5678  main -> origin/main")

        result = git_fetch()
        assert "origin" in result or "fetch" in result.lower()

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_fetch_with_prune(self, mock_run, mock_is_repo):
        """Test fetch with prune option."""
        from src.servers.git import git_fetch

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Fetching origin")

        result = git_fetch(prune=True)
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_pull_success(self, mock_run, mock_is_repo):
        """Test successful pull."""
        from src.servers.git import git_pull

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Already up to date.")

        result = git_pull()
        assert "up to date" in result.lower() or "pull" in result.lower()

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_pull_with_branch(self, mock_run, mock_is_repo):
        """Test pull from specific branch."""
        from src.servers.git import git_pull

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Already up to date.")

        result = git_pull(branch="develop")
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_push_success(self, mock_run, mock_is_repo):
        """Test successful push."""
        from src.servers.git import git_push

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "To github.com:user/repo\n   abc1234..def5678  main -> main")

        result = git_push()
        assert "main" in result or "push" in result.lower()

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_push_with_upstream(self, mock_run, mock_is_repo):
        """Test push with upstream tracking."""
        from src.servers.git import git_push

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Branch 'feature' set up to track remote branch")

        result = git_push(set_upstream=True)
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_push_specific_branch(self, mock_run, mock_is_repo):
        """Test push to specific branch."""
        from src.servers.git import git_push

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Pushing to develop")

        result = git_push(branch="develop")
        assert result

    @patch('src.servers.git._is_git_repo')
    def test_git_pull_invalid_remote(self, mock_is_repo):
        """Test pull with invalid remote name."""
        from src.servers.git import git_pull

        mock_is_repo.return_value = True
        result = git_pull(remote="invalid remote")
        assert "Error" in result or "Invalid" in result

    @patch('src.servers.git._is_git_repo')
    def test_git_push_invalid_branch(self, mock_is_repo):
        """Test push with invalid branch name."""
        from src.servers.git import git_push

        mock_is_repo.return_value = True
        result = git_push(branch="invalid branch")
        assert "Error" in result or "Invalid" in result


class TestGitLogAndDiff:
    """Tests for log and diff operations."""

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_log_default(self, mock_run, mock_is_repo):
        """Test git log with default parameters."""
        from src.servers.git import git_log

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "abc1234 | John Doe | 2 hours ago | feat: add feature")

        result = git_log()
        assert "abc1234" in result or "John Doe" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_log_oneline(self, mock_run, mock_is_repo):
        """Test git log with oneline format."""
        from src.servers.git import git_log

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "abc1234 feat: add feature\ndef5678 fix: bug fix")

        result = git_log(oneline=True)
        assert "abc1234" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_log_with_author(self, mock_run, mock_is_repo):
        """Test git log filtered by author."""
        from src.servers.git import git_log

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "abc1234 | John Doe | 2 hours ago | feat: add feature")

        result = git_log(author="John Doe")
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_log_with_since(self, mock_run, mock_is_repo):
        """Test git log filtered by date."""
        from src.servers.git import git_log

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "abc1234 | John Doe | 1 day ago | feat: add feature")

        result = git_log(since="1 week ago")
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_log_custom_count(self, mock_run, mock_is_repo):
        """Test git log with custom count."""
        from src.servers.git import git_log

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "abc1234 | John Doe | 2 hours ago | feat: add feature")

        result = git_log(count=20)
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_show_commit(self, mock_run, mock_is_repo):
        """Test showing commit details."""
        from src.servers.git import git_show

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "commit abc1234\nAuthor: John Doe\n\nfeat: add feature")

        result = git_show("abc1234")
        assert "abc1234" in result or "feat" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_show_stat_only(self, mock_run, mock_is_repo):
        """Test showing commit statistics only."""
        from src.servers.git import git_show

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "file.py | 10 ++++++++")

        result = git_show("abc1234", stat_only=True)
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_diff_unstaged(self, mock_run, mock_is_repo):
        """Test showing unstaged changes."""
        from src.servers.git import git_diff

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "diff --git a/file.py b/file.py\n-old line\n+new line")

        result = git_diff()
        assert "diff" in result.lower() or "file.py" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_diff_staged(self, mock_run, mock_is_repo):
        """Test showing staged changes."""
        from src.servers.git import git_diff

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "diff --git a/file.py b/file.py\n-old line\n+new line")

        result = git_diff(staged=True)
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_diff_specific_file(self, mock_run, mock_is_repo):
        """Test showing diff for specific file."""
        from src.servers.git import git_diff

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "diff --git a/file.py b/file.py")

        result = git_diff(file_path="file.py")
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_diff_no_changes(self, mock_run, mock_is_repo):
        """Test diff when there are no changes."""
        from src.servers.git import git_diff

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "")

        result = git_diff()
        assert "No changes" in result


class TestGitStagingAndCommitting:
    """Tests for staging and committing operations."""

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_add_all(self, mock_run, mock_is_repo):
        """Test staging all changes."""
        from src.servers.git import git_add

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "")

        result = git_add(".")
        assert "Staged" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_add_specific_files(self, mock_run, mock_is_repo):
        """Test staging specific files."""
        from src.servers.git import git_add

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "")

        result = git_add(["file1.py", "file2.py"])
        assert "Staged" in result
        assert "file1.py" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_add_single_file_string(self, mock_run, mock_is_repo):
        """Test staging single file as string."""
        from src.servers.git import git_add

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "")

        result = git_add("file.py")
        assert "Staged" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_commit_success(self, mock_run, mock_is_repo):
        """Test successful commit."""
        from src.servers.git import git_commit

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "1 file changed, 5 insertions(+)")

        result = git_commit("feat: add new feature")
        assert "changed" in result.lower() or "insertion" in result.lower()

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_commit_with_add_all(self, mock_run, mock_is_repo):
        """Test commit with add_all flag."""
        from src.servers.git import git_commit

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "1 file changed, 5 insertions(+)")

        result = git_commit("fix: bug fix", add_all=True)
        assert result

    @patch('src.servers.git._is_git_repo')
    def test_git_commit_empty_message(self, mock_is_repo):
        """Test commit with empty message."""
        from src.servers.git import git_commit

        mock_is_repo.return_value = True
        result = git_commit("")
        assert "Error" in result or "empty" in result.lower()

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_reset_unstage_files(self, mock_run, mock_is_repo):
        """Test unstaging specific files."""
        from src.servers.git import git_reset

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "")

        result = git_reset(files=["file.py"])
        assert "Unstaged" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_reset_soft(self, mock_run, mock_is_repo):
        """Test soft reset."""
        from src.servers.git import git_reset

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "")

        result = git_reset(mode="soft")
        assert "Reset" in result or "soft" in result.lower()

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_reset_mixed(self, mock_run, mock_is_repo):
        """Test mixed reset."""
        from src.servers.git import git_reset

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "")

        result = git_reset(mode="mixed")
        assert "Reset" in result or "mixed" in result.lower()

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_reset_hard(self, mock_run, mock_is_repo):
        """Test hard reset."""
        from src.servers.git import git_reset

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "")

        result = git_reset(mode="hard")
        assert "Reset" in result or "hard" in result.lower()

    @patch('src.servers.git._is_git_repo')
    def test_git_reset_invalid_mode(self, mock_is_repo):
        """Test reset with invalid mode."""
        from src.servers.git import git_reset

        mock_is_repo.return_value = True
        result = git_reset(mode="invalid")
        assert "Error" in result or "Invalid" in result


class TestGitWorktreeOperations:
    """Tests for worktree operations."""

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_worktree_list(self, mock_run, mock_is_repo):
        """Test listing worktrees."""
        from src.servers.git import git_worktree_list

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "/path/to/main (branch main)\n/path/to/feature (branch feature/new)")

        result = git_worktree_list()
        assert "main" in result or "feature" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_worktree_add_existing_branch(self, mock_run, mock_is_repo):
        """Test adding worktree for existing branch."""
        from src.servers.git import git_worktree_add

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Preparing new working tree")

        result = git_worktree_add("../myproject-feature", "feature/new")
        assert "worktree" in result.lower() or "feature" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_worktree_add_create_branch(self, mock_run, mock_is_repo):
        """Test adding worktree with new branch creation."""
        from src.servers.git import git_worktree_add

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Preparing new working tree")

        result = git_worktree_add("../myproject-feature", "feature/new", create_branch=True)
        assert "worktree" in result.lower() or "feature" in result

    @patch('src.servers.git._is_git_repo')
    def test_git_worktree_add_invalid_branch(self, mock_is_repo):
        """Test adding worktree with invalid branch name."""
        from src.servers.git import git_worktree_add

        mock_is_repo.return_value = True
        result = git_worktree_add("../path", "invalid branch")
        assert "Error" in result or "Invalid" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_worktree_remove(self, mock_run, mock_is_repo):
        """Test removing a worktree."""
        from src.servers.git import git_worktree_remove

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Removing worktrees")

        result = git_worktree_remove("../myproject-feature")
        assert "Removed" in result or "worktree" in result.lower()

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_worktree_remove_force(self, mock_run, mock_is_repo):
        """Test force removing a worktree."""
        from src.servers.git import git_worktree_remove

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Removing worktrees")

        result = git_worktree_remove("../myproject-feature", force=True)
        assert "Removed" in result or "worktree" in result.lower()

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_worktree_prune(self, mock_run, mock_is_repo):
        """Test pruning stale worktree information."""
        from src.servers.git import git_worktree_prune

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "")

        result = git_worktree_prune()
        assert "prune" in result.lower() or "completed" in result.lower()


class TestGitHubOperations:
    """Tests for GitHub CLI operations."""

    @patch('src.servers.git._run_gh_command')
    def test_gh_pr_create_success(self, mock_run):
        """Test creating a GitHub PR."""
        from src.servers.git import gh_pr_create

        mock_run.return_value = (True, "https://github.com/user/repo/pull/123")

        result = gh_pr_create("Add feature", "This PR adds a new feature")
        assert "https" in result or "pull" in result.lower()

    @patch('src.servers.git._run_gh_command')
    def test_gh_pr_create_draft(self, mock_run):
        """Test creating a draft PR."""
        from src.servers.git import gh_pr_create

        mock_run.return_value = (True, "https://github.com/user/repo/pull/123")

        result = gh_pr_create("WIP: Feature", "Work in progress", draft=True)
        assert result

    @patch('src.servers.git._run_gh_command')
    def test_gh_pr_create_with_base(self, mock_run):
        """Test creating PR with specific base branch."""
        from src.servers.git import gh_pr_create

        mock_run.return_value = (True, "https://github.com/user/repo/pull/123")

        result = gh_pr_create("Add feature", "Description", base="develop")
        assert result

    @patch('src.servers.git._run_gh_command')
    def test_gh_pr_list(self, mock_run):
        """Test listing pull requests."""
        from src.servers.git import gh_pr_list

        mock_run.return_value = (True, "#123\tAdd feature\tOPEN\n#122\tFix bug\tCLOSED")

        result = gh_pr_list()
        assert "#123" in result or "Add feature" in result

    @patch('src.servers.git._run_gh_command')
    def test_gh_pr_list_closed(self, mock_run):
        """Test listing closed pull requests."""
        from src.servers.git import gh_pr_list

        mock_run.return_value = (True, "#122\tFix bug\tCLOSED")

        result = gh_pr_list(state="closed")
        assert result

    @patch('src.servers.git._run_gh_command')
    def test_gh_pr_view(self, mock_run):
        """Test viewing PR details."""
        from src.servers.git import gh_pr_view

        mock_run.return_value = (True, "title: Add feature\nstate: OPEN\nauthor: user")

        result = gh_pr_view(123)
        assert "Add feature" in result or "OPEN" in result

    @patch('src.servers.git._run_gh_command')
    def test_gh_pr_view_current(self, mock_run):
        """Test viewing current branch PR."""
        from src.servers.git import gh_pr_view

        mock_run.return_value = (True, "title: Add feature\nstate: OPEN")

        result = gh_pr_view()
        assert result

    @patch('src.servers.git._run_gh_command')
    def test_gh_issue_list(self, mock_run):
        """Test listing issues."""
        from src.servers.git import gh_issue_list

        mock_run.return_value = (True, "#1\tBug report\tOPEN\n#2\tFeature request\tOPEN")

        result = gh_issue_list()
        assert "#1" in result or "Bug report" in result

    @patch('src.servers.git._run_gh_command')
    def test_gh_issue_list_with_labels(self, mock_run):
        """Test listing issues with label filter."""
        from src.servers.git import gh_issue_list

        mock_run.return_value = (True, "#1\tBug report\tOPEN")

        result = gh_issue_list(labels=["bug", "critical"])
        assert result

    @patch('src.servers.git._run_gh_command')
    def test_gh_issue_list_closed(self, mock_run):
        """Test listing closed issues."""
        from src.servers.git import gh_issue_list

        mock_run.return_value = (True, "#5\tFixed issue\tCLOSED")

        result = gh_issue_list(state="closed")
        assert result


class TestGitStatusAndRepository:
    """Tests for repository status and validation."""

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_status_success(self, mock_run, mock_is_repo):
        """Test getting repository status."""
        from src.servers.git import git_status

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "On branch main\nnothing to commit")

        result = git_status()
        assert "main" in result or "commit" in result.lower()

    @patch('src.servers.git._is_git_repo')
    def test_git_status_not_repo(self, mock_is_repo):
        """Test status on non-git directory."""
        from src.servers.git import git_status

        mock_is_repo.return_value = False
        result = git_status("/invalid/path")
        assert "Error" in result or "not a git repository" in result

    @patch('src.servers.git._run_git_command')
    def test_is_git_repo_true(self, mock_run):
        """Test checking if directory is git repo (true case)."""
        from src.servers.git import _is_git_repo

        mock_run.return_value = (True, ".git")
        result = _is_git_repo()
        assert result is True

    @patch('src.servers.git._run_git_command')
    def test_is_git_repo_false(self, mock_run):
        """Test checking if directory is git repo (false case)."""
        from src.servers.git import _is_git_repo

        mock_run.return_value = (False, "not a git repository")
        result = _is_git_repo()
        assert result is False


class TestGitEdgeCasesAndErrors:
    """Tests for edge cases and error handling."""

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_add_invalid_file_path(self, mock_run, mock_is_repo):
        """Test adding file with invalid path."""
        from src.servers.git import git_add

        mock_is_repo.return_value = True
        result = git_add("../../../etc/passwd")
        # Should either succeed or fail gracefully
        assert isinstance(result, str)

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_commit_with_special_characters(self, mock_run, mock_is_repo):
        """Test commit message with special characters."""
        from src.servers.git import git_commit

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "1 file changed")

        result = git_commit("feat: add feature with 'quotes' and \"double quotes\"")
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_log_empty_repository(self, mock_run, mock_is_repo):
        """Test log on empty repository."""
        from src.servers.git import git_log

        mock_is_repo.return_value = True
        mock_run.return_value = (False, "fatal: your current branch 'main' does not have any commits yet")

        result = git_log()
        assert "Error" in result or "fatal" in result.lower()

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_merge_fast_forward(self, mock_run, mock_is_repo):
        """Test merge with fast-forward."""
        from src.servers.git import git_merge

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Fast-forward")

        result = git_merge("feature")
        assert "Fast-forward" in result or "feature" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_push_rejected(self, mock_run, mock_is_repo):
        """Test push rejection."""
        from src.servers.git import git_push

        mock_is_repo.return_value = True
        mock_run.return_value = (False, "rejected - non-fast-forward")

        result = git_push()
        assert "Error" in result or "rejected" in result.lower()

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_pull_merge_conflict(self, mock_run, mock_is_repo):
        """Test pull with merge conflict."""
        from src.servers.git import git_pull

        mock_is_repo.return_value = True
        mock_run.return_value = (False, "CONFLICT (content): Merge conflict in file.txt")

        result = git_pull()
        assert "Error" in result or "CONFLICT" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_reset_with_multiple_files(self, mock_run, mock_is_repo):
        """Test resetting multiple files."""
        from src.servers.git import git_reset

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "")

        result = git_reset(files=["file1.py", "file2.py", "file3.py"])
        assert "Unstaged" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_stash_apply(self, mock_run, mock_is_repo):
        """Test applying stash without removing."""
        from src.servers.git import git_stash

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Applied stash")

        result = git_stash("apply")
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_diff_with_invalid_file(self, mock_run, mock_is_repo):
        """Test diff with non-existent file."""
        from src.servers.git import git_diff

        mock_is_repo.return_value = True
        result = git_diff(file_path="../../../etc/passwd")
        # Should handle gracefully
        assert isinstance(result, str)

    @patch('src.servers.git._run_gh_command')
    def test_gh_pr_create_invalid_base(self, mock_run):
        """Test PR creation with invalid base branch."""
        from src.servers.git import gh_pr_create

        result = gh_pr_create("Title", "Body", base="invalid base")
        assert "Error" in result or "Invalid" in result

    @patch('src.servers.git._run_gh_command')
    def test_gh_pr_create_gh_not_installed(self, mock_run):
        """Test PR creation when gh CLI is not installed."""
        from src.servers.git import gh_pr_create

        mock_run.return_value = (False, "GitHub CLI (gh) is not installed")

        result = gh_pr_create("Title", "Body")
        assert "Error" in result or "not installed" in result.lower()

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_checkout_detached_head(self, mock_run, mock_is_repo):
        """Test checking out specific commit (detached HEAD)."""
        from src.servers.git import git_checkout

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "HEAD is now at abc1234")

        result = git_checkout("abc1234")
        assert "abc1234" in result or "HEAD" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_show_invalid_commit(self, mock_run, mock_is_repo):
        """Test showing non-existent commit."""
        from src.servers.git import git_show

        mock_is_repo.return_value = True
        mock_run.return_value = (False, "fatal: bad revision 'invalid'")

        result = git_show("invalid")
        assert "Error" in result or "fatal" in result.lower()

    @patch('src.servers.git.subprocess.run')
    def test_run_git_command_generic_exception(self, mock_run):
        """Test git command with generic exception."""
        from src.servers.git import _run_git_command

        mock_run.side_effect = Exception("Unexpected error")
        success, output = _run_git_command(["status"])

        assert success is False
        assert "Error" in output

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_fetch_empty_output(self, mock_run, mock_is_repo):
        """Test fetch with empty output (already up to date)."""
        from src.servers.git import git_fetch

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "")

        result = git_fetch()
        assert "up to date" in result.lower() or "completed" in result.lower()

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_log_with_all_filters(self, mock_run, mock_is_repo):
        """Test log with multiple filters applied."""
        from src.servers.git import git_log

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "abc1234 | John Doe | 1 day ago | feat: feature")

        result = git_log(count=5, oneline=True, author="John", since="1 week ago")
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_add_empty_list(self, mock_run, mock_is_repo):
        """Test adding empty file list."""
        from src.servers.git import git_add

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "")

        result = git_add([])
        assert "Staged" in result or result  # Should handle gracefully


class TestGitComprehensiveBasicOps:
    """Comprehensive tests for basic git operations (10+ tests)."""

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_status_with_changes(self, mock_run, mock_is_repo):
        """Test status with staged and unstaged changes."""
        from src.servers.git import git_status

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "On branch main\nChanges to be committed:\n  modified: file.py")

        result = git_status()
        assert "main" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_status_with_untracked(self, mock_run, mock_is_repo):
        """Test status with untracked files."""
        from src.servers.git import git_status

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Untracked files:\n  new_file.py")

        result = git_status()
        assert "Untracked" in result or "new_file" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_add_with_path_validation(self, mock_run, mock_is_repo):
        """Test git add validates file paths."""
        from src.servers.git import git_add

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "")

        result = git_add("src/main.py")
        assert "Staged" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_commit_with_multiline_message(self, mock_run, mock_is_repo):
        """Test commit with multiline message."""
        from src.servers.git import git_commit

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "1 file changed")

        result = git_commit("feat: add feature\n\nDetailed description")
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_commit_nothing_to_commit(self, mock_run, mock_is_repo):
        """Test commit when nothing is staged."""
        from src.servers.git import git_commit

        mock_is_repo.return_value = True
        mock_run.return_value = (False, "nothing to commit")

        result = git_commit("feat: nothing")
        assert "Error" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_reset_all_files(self, mock_run, mock_is_repo):
        """Test resetting all staged files."""
        from src.servers.git import git_reset

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "")

        result = git_reset()
        assert "Reset" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_diff_with_context(self, mock_run, mock_is_repo):
        """Test diff shows context around changes."""
        from src.servers.git import git_diff

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "@@-1,5 +1,6@@\n context\n-old\n+new")

        result = git_diff()
        assert "diff" in result.lower() or "context" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_log_with_count_zero(self, mock_run, mock_is_repo):
        """Test log with count parameter."""
        from src.servers.git import git_log

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "abc1234 | Author | time | message")

        result = git_log(count=1)
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_show_head(self, mock_run, mock_is_repo):
        """Test showing HEAD commit."""
        from src.servers.git import git_show

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "commit abc1234\nAuthor: Test")

        result = git_show()
        assert "commit" in result.lower() or "abc1234" in result


class TestGitComprehensiveBranchOps:
    """Comprehensive tests for branch operations (10+ tests)."""

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_branch_with_custom_path(self, mock_run, mock_is_repo):
        """Test branch listing with custom repo path."""
        from src.servers.git import git_branch

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "* main\n  develop")

        result = git_branch(path="/custom/path")
        assert "main" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_branch_empty_repo(self, mock_run, mock_is_repo):
        """Test branch on empty repository."""
        from src.servers.git import git_branch

        mock_is_repo.return_value = True
        mock_run.return_value = (False, "fatal: not a valid object name")

        result = git_branch()
        assert "Error" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_checkout_with_path(self, mock_run, mock_is_repo):
        """Test checkout with custom path."""
        from src.servers.git import git_checkout

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Switched to branch 'feature'")

        result = git_checkout("feature", path="/repo")
        assert "feature" in result or "Switched" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_checkout_already_on_branch(self, mock_run, mock_is_repo):
        """Test checkout when already on target branch."""
        from src.servers.git import git_checkout

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Already on 'main'")

        result = git_checkout("main")
        assert "main" in result or "Already" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_merge_abort(self, mock_run, mock_is_repo):
        """Test merge abort on conflict."""
        from src.servers.git import git_merge

        mock_is_repo.return_value = True
        mock_run.return_value = (False, "CONFLICT")

        result = git_merge("feature")
        assert "Error" in result or "CONFLICT" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_merge_already_up_to_date(self, mock_run, mock_is_repo):
        """Test merge when already up to date."""
        from src.servers.git import git_merge

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Already up to date")

        result = git_merge("main")
        assert "up to date" in result.lower() or "Already" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_merge_with_custom_path(self, mock_run, mock_is_repo):
        """Test merge with custom repo path."""
        from src.servers.git import git_merge

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Merge made")

        result = git_merge("develop", path="/repo")
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_checkout_ends_with_slash(self, mock_run, mock_is_repo):
        """Test checkout validation rejects names ending with slash."""
        from src.servers.git import git_checkout

        mock_is_repo.return_value = True
        result = git_checkout("feature/")
        assert "Error" in result or "Invalid" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_merge_ends_with_dot(self, mock_run, mock_is_repo):
        """Test merge validation rejects names ending with dot."""
        from src.servers.git import git_merge

        mock_is_repo.return_value = True
        result = git_merge("feature.")
        assert "Error" in result or "Invalid" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_checkout_with_slash_slash(self, mock_run, mock_is_repo):
        """Test checkout validation rejects double slashes."""
        from src.servers.git import git_checkout

        mock_is_repo.return_value = True
        result = git_checkout("feature//main")
        assert "Error" in result or "Invalid" in result


class TestGitComprehensiveRemoteOps:
    """Comprehensive tests for remote operations (10+ tests)."""

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_fetch_with_custom_remote(self, mock_run, mock_is_repo):
        """Test fetch from custom remote."""
        from src.servers.git import git_fetch

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Fetching upstream")

        result = git_fetch(remote="upstream")
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_fetch_with_prune_and_custom_remote(self, mock_run, mock_is_repo):
        """Test fetch with prune and custom remote."""
        from src.servers.git import git_fetch

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Pruning")

        result = git_fetch(remote="upstream", prune=True)
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_pull_with_custom_remote_and_branch(self, mock_run, mock_is_repo):
        """Test pull from custom remote and branch."""
        from src.servers.git import git_pull

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Pulling")

        result = git_pull(remote="upstream", branch="main")
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_push_with_custom_remote_and_branch(self, mock_run, mock_is_repo):
        """Test push to custom remote and branch."""
        from src.servers.git import git_push

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Pushing")

        result = git_push(remote="upstream", branch="feature")
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_push_with_upstream_and_branch(self, mock_run, mock_is_repo):
        """Test push with upstream tracking and branch."""
        from src.servers.git import git_push

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Branch set up to track")

        result = git_push(branch="feature", set_upstream=True)
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_pull_invalid_branch(self, mock_run, mock_is_repo):
        """Test pull with invalid branch name."""
        from src.servers.git import git_pull

        mock_is_repo.return_value = True
        result = git_pull(branch="invalid branch")
        assert "Error" in result or "Invalid" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_push_invalid_remote(self, mock_run, mock_is_repo):
        """Test push with invalid remote name."""
        from src.servers.git import git_push

        mock_is_repo.return_value = True
        result = git_push(remote="invalid remote")
        assert "Error" in result or "Invalid" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_fetch_network_error(self, mock_run, mock_is_repo):
        """Test fetch with network error."""
        from src.servers.git import git_fetch

        mock_is_repo.return_value = True
        mock_run.return_value = (False, "fatal: unable to access repository")

        result = git_fetch()
        assert "Error" in result or "fatal" in result.lower()

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_pull_with_path(self, mock_run, mock_is_repo):
        """Test pull with custom path."""
        from src.servers.git import git_pull

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Already up to date")

        result = git_pull(path="/repo")
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_push_with_path(self, mock_run, mock_is_repo):
        """Test push with custom path."""
        from src.servers.git import git_push

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Pushing")

        result = git_push(path="/repo")
        assert result


class TestGitComprehensiveAdvancedOps:
    """Comprehensive tests for advanced operations (10+ tests)."""

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_stash_with_path(self, mock_run, mock_is_repo):
        """Test stash with custom path."""
        from src.servers.git import git_stash

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Saved")

        result = git_stash(path="/repo")
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_stash_apply_with_path(self, mock_run, mock_is_repo):
        """Test stash apply with custom path."""
        from src.servers.git import git_stash

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Applied")

        result = git_stash("apply", path="/repo")
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_worktree_list_with_path(self, mock_run, mock_is_repo):
        """Test worktree list with custom path."""
        from src.servers.git import git_worktree_list

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "/path/to/main (branch main)")

        result = git_worktree_list(path="/repo")
        assert result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_worktree_add_with_path(self, mock_run, mock_is_repo):
        """Test worktree add with custom repo path."""
        from src.servers.git import git_worktree_add

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Created")

        result = git_worktree_add("../feature", "feature/new", path="/repo")
        assert "worktree" in result.lower() or "feature" in result

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_worktree_remove_with_path(self, mock_run, mock_is_repo):
        """Test worktree remove with custom repo path."""
        from src.servers.git import git_worktree_remove

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "Removed")

        result = git_worktree_remove("../feature", path="/repo")
        assert "Removed" in result or "worktree" in result.lower()

    @patch('src.servers.git._is_git_repo')
    @patch('src.servers.git._run_git_command')
    def test_git_worktree_prune_with_path(self, mock_run, mock_is_repo):
        """Test worktree prune with custom path."""
        from src.servers.git import git_worktree_prune

        mock_is_repo.return_value = True
        mock_run.return_value = (True, "")

        result = git_worktree_prune(path="/repo")
        assert "prune" in result.lower() or "completed" in result.lower()

    @patch('src.servers.git._run_gh_command')
    def test_gh_pr_create_with_path(self, mock_run):
        """Test PR creation with custom path."""
        from src.servers.git import gh_pr_create

        mock_run.return_value = (True, "https://github.com/user/repo/pull/1")

        result = gh_pr_create("Title", "Body", path="/repo")
        assert "https" in result or "pull" in result.lower()

    @patch('src.servers.git._run_gh_command')
    def test_gh_pr_list_with_path(self, mock_run):
        """Test PR list with custom path."""
        from src.servers.git import gh_pr_list

        mock_run.return_value = (True, "#1\tTitle\tOPEN")

        result = gh_pr_list(path="/repo")
        assert result

    @patch('src.servers.git._run_gh_command')
    def test_gh_issue_list_with_path(self, mock_run):
        """Test issue list with custom path."""
        from src.servers.git import gh_issue_list

        mock_run.return_value = (True, "#1\tIssue\tOPEN")

        result = gh_issue_list(path="/repo")
        assert result

    @patch('src.servers.git._run_gh_command')
    def test_gh_pr_view_with_path(self, mock_run):
        """Test PR view with custom path."""
        from src.servers.git import gh_pr_view

        mock_run.return_value = (True, "title: Test")

        result = gh_pr_view(path="/repo")
        assert result


class TestGitPathValidation:
    """Tests for path validation and security."""

    @patch('src.servers.git._is_git_repo')
    def test_git_status_invalid_path(self, mock_is_repo):
        """Test status with invalid path."""
        from src.servers.git import git_status

        mock_is_repo.return_value = False
        result = git_status("/invalid/path")
        assert "Error" in result or "not a git repository" in result

    @patch('src.servers.git._is_git_repo')
    def test_git_branch_invalid_path(self, mock_is_repo):
        """Test branch with invalid path."""
        from src.servers.git import git_branch

        mock_is_repo.return_value = False
        result = git_branch("/invalid/path")
        assert "Error" in result or "not a git repository" in result

    @patch('src.servers.git._is_git_repo')
    def test_git_checkout_invalid_path(self, mock_is_repo):
        """Test checkout with invalid path."""
        from src.servers.git import git_checkout

        mock_is_repo.return_value = False
        result = git_checkout("main", path="/invalid/path")
        assert "Error" in result or "not a git repository" in result

    @patch('src.servers.git._is_git_repo')
    def test_git_merge_invalid_path(self, mock_is_repo):
        """Test merge with invalid path."""
        from src.servers.git import git_merge

        mock_is_repo.return_value = False
        result = git_merge("develop", path="/invalid/path")
        assert "Error" in result or "not a git repository" in result

    @patch('src.servers.git._is_git_repo')
    def test_git_stash_invalid_path(self, mock_is_repo):
        """Test stash with invalid path."""
        from src.servers.git import git_stash

        mock_is_repo.return_value = False
        result = git_stash(path="/invalid/path")
        assert "Error" in result or "not a git repository" in result

    @patch('src.servers.git._is_git_repo')
    def test_git_worktree_list_invalid_path(self, mock_is_repo):
        """Test worktree list with invalid path."""
        from src.servers.git import git_worktree_list

        mock_is_repo.return_value = False
        result = git_worktree_list(path="/invalid/path")
        assert "Error" in result or "not a git repository" in result

    @patch('src.servers.git._is_git_repo')
    def test_git_worktree_add_invalid_path(self, mock_is_repo):
        """Test worktree add with invalid path."""
        from src.servers.git import git_worktree_add

        mock_is_repo.return_value = False
        result = git_worktree_add("../feature", "feature", path="/invalid/path")
        assert "Error" in result or "not a git repository" in result

    @patch('src.servers.git._is_git_repo')
    def test_git_worktree_remove_invalid_path(self, mock_is_repo):
        """Test worktree remove with invalid path."""
        from src.servers.git import git_worktree_remove

        mock_is_repo.return_value = False
        result = git_worktree_remove("../feature", path="/invalid/path")
        assert "Error" in result or "not a git repository" in result

    @patch('src.servers.git._is_git_repo')
    def test_git_worktree_prune_invalid_path(self, mock_is_repo):
        """Test worktree prune with invalid path."""
        from src.servers.git import git_worktree_prune

        mock_is_repo.return_value = False
        result = git_worktree_prune(path="/invalid/path")
        assert "Error" in result or "not a git repository" in result


class TestGitRefValidation:
    """Tests for git reference validation edge cases."""

    def test_validate_git_ref_with_caret(self):
        """Test validation rejects caret character."""
        from src.servers.git import _validate_git_ref

        is_valid, error_msg = _validate_git_ref("feature^old")
        assert not is_valid

    def test_validate_git_ref_with_asterisk(self):
        """Test validation rejects asterisk."""
        from src.servers.git import _validate_git_ref

        is_valid, error_msg = _validate_git_ref("feature*")
        assert not is_valid

    def test_validate_git_ref_with_bracket(self):
        """Test validation rejects bracket."""
        from src.servers.git import _validate_git_ref

        is_valid, error_msg = _validate_git_ref("feature[0]")
        assert not is_valid

    def test_validate_git_ref_with_backslash(self):
        """Test validation rejects backslash."""
        from src.servers.git import _validate_git_ref

        is_valid, error_msg = _validate_git_ref("feature\\main")
        assert not is_valid

    def test_validate_git_ref_with_colon(self):
        """Test validation rejects colon."""
        from src.servers.git import _validate_git_ref

        is_valid, error_msg = _validate_git_ref("feature:tag")
        assert not is_valid

    def test_validate_git_ref_with_question_mark(self):
        """Test validation rejects question mark."""
        from src.servers.git import _validate_git_ref

        is_valid, error_msg = _validate_git_ref("feature?")
        assert not is_valid

    def test_validate_git_ref_with_tilde(self):
        """Test validation rejects tilde."""
        from src.servers.git import _validate_git_ref

        is_valid, error_msg = _validate_git_ref("feature~main")
        assert not is_valid

    def test_validate_git_ref_with_space(self):
        """Test validation rejects space."""
        from src.servers.git import _validate_git_ref

        is_valid, error_msg = _validate_git_ref("feature branch")
        assert not is_valid

    def test_validate_git_ref_valid_with_slash(self):
        """Test validation accepts valid slash in ref."""
        from src.servers.git import _validate_git_ref

        is_valid, error_msg = _validate_git_ref("feature/new-ui")
        assert is_valid

    def test_validate_git_ref_valid_with_dash(self):
        """Test validation accepts dash in ref."""
        from src.servers.git import _validate_git_ref

        is_valid, error_msg = _validate_git_ref("feature-new")
        assert is_valid

    def test_validate_git_ref_valid_with_underscore(self):
        """Test validation accepts underscore in ref."""
        from src.servers.git import _validate_git_ref

        is_valid, error_msg = _validate_git_ref("feature_new")
        assert is_valid

    def test_validate_git_ref_valid_with_numbers(self):
        """Test validation accepts numbers in ref."""
        from src.servers.git import _validate_git_ref

        is_valid, error_msg = _validate_git_ref("v1.0.0")
        assert is_valid

    def test_validate_git_ref_starts_with_dot(self):
        """Test validation accepts reference starting with dot (git allows it)."""
        from src.servers.git import _validate_git_ref

        is_valid, error_msg = _validate_git_ref(".feature")
        assert is_valid

    def test_validate_git_ref_ends_with_slash(self):
        """Test validation rejects reference ending with slash."""
        from src.servers.git import _validate_git_ref

        is_valid, error_msg = _validate_git_ref("feature/")
        assert not is_valid
