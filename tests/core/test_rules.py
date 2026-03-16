from src.core import rules as rules_module
from src.core.rules import load_all_instructions, load_project_rules


def test_load_project_rules_supports_agents_hierarchy(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    nested = repo / "src" / "feature"
    nested.mkdir(parents=True)
    (repo / ".git").mkdir()
    (repo / "AGENTS.md").write_text("root agent instructions", encoding="utf-8")
    (repo / "src" / "AGENTS.md").write_text("nested agent instructions", encoding="utf-8")

    monkeypatch.chdir(nested)

    content = load_project_rules(nested)

    assert content is not None
    assert "root agent instructions" in content
    assert "nested agent instructions" in content
    assert content.index("root agent instructions") < content.index("nested agent instructions")


def test_load_all_instructions_cache_invalidates_when_agents_changes(tmp_path, monkeypatch):
    rules_module._TEXT_CACHE.clear()
    rules_module._PROJECT_RULES_CACHE.clear()
    rules_module._ALL_INSTRUCTIONS_CACHE.clear()

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    agents = repo / "AGENTS.md"
    agents.write_text("first rules", encoding="utf-8")

    monkeypatch.chdir(repo)

    first = load_all_instructions({}, repo)
    assert "first rules" in first

    agents.write_text("second rules", encoding="utf-8")

    second = load_all_instructions({}, repo)
    assert "second rules" in second
