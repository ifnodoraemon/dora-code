import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from src.core.logger import configure_root_logger
from src.core.paths import chroma_dir, persona_path, state_dir

# Setup logging
configure_root_logger()
logger = logging.getLogger(__name__)

# Suppress noisy HTTP request logs from the Gemini/httpx SDK
logging.getLogger("httpx").setLevel(logging.WARNING)

# Initialize FastMCP Server
mcp = FastMCP("AgentMemory")

# Lazy-initialized globals
_initialized = False
embedding_fn = None
client = None
collection = None
COLLECTION_NAME = None


def _persist_dir() -> str:
    """Resolve the current project's vector store directory."""
    return str(chroma_dir())


def _memory_file() -> Path:
    """Resolve the current project's persona file."""
    return persona_path()


def _ensure_initialized():
    """Lazily initialize ChromaDB and embeddings on first use."""
    global _initialized, embedding_fn, client, collection, COLLECTION_NAME
    if collection is not None:
        _initialized = True
        return
    if _initialized:
        return
    _initialized = True

    state_dir().mkdir(parents=True, exist_ok=True)

    try:
        import chromadb

        from src.services.embeddings import RemoteEmbeddingFunction

        embedding_fn = RemoteEmbeddingFunction()
        client = chromadb.PersistentClient(path=_persist_dir())

        provider = embedding_fn.provider
        COLLECTION_NAME = f"agent_notes_{provider}"

        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn
        )
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB collection: {e}")
        collection = None


@mcp.tool()
def save_note(
    title: str, content: str, collection_name: str = "default", tags: list[str] | None = None
) -> str:
    """Save a note to the long-term memory (Vector DB)."""
    _ensure_initialized()
    if collection is None:
        return "Memory system is not initialized."

    tags = tags or []

    if len(content) > 100000:
        return f"Error: Content too long ({len(content)} chars). Maximum allowed is 100000 characters."

    try:
        # We use a single shared collection for now with metadata filtering if needed,
        # or we could create potential sub-collections.
        # To keep it simple and avoid model dimension mismatches across collections, we use the main one.

        note_id = f"{collection_name}_{title}_{hashlib.sha256(content.encode()).hexdigest()[:12]}"

        # Add metadata for filtering
        metadatas: list[dict[str, Any]] = [{"title": title, "tags": ",".join(tags), "project": collection_name}]

        collection.add(
            documents=[content],
            metadatas=metadatas, # type: ignore
            ids=[note_id]
        )
        logger.info(f"Saved note '{title}' to project '{collection_name}'")
        return f"Note '{title}' saved to project {collection_name}."
    except Exception as e:
        logger.error(f"Failed to save note '{title}': {e}")
        return f"Failed to save note: {e}"


@mcp.tool()
def search_notes(query: str, collection_name: str = "default", n_results: int = 3) -> str:
    """Search for notes in the long-term memory."""
    _ensure_initialized()
    if collection is None:
        return "Memory system is not initialized."

    try:
        # Filter by project/collection_name in metadata
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"project": collection_name}
        )

        docs = results.get("documents")
        metas = results.get("metadatas")

        if not docs or not docs[0] or not metas or not metas[0]:
            return f"Notes not found in project {collection_name}."

        output = []
        for doc, meta in zip(docs[0], metas[0], strict=True):
            output.append(f"[标题: {meta.get('title', 'Untitled')}]\n{doc}")

        return "\n---\n".join(output)
    except Exception as e:
        return f"Search failed: {e}"


@mcp.tool()
def delete_note(title: str, collection_name: str = "default") -> str:
    """Delete a note from the long-term memory by title."""
    _ensure_initialized()
    if collection is None:
        return "Memory system is not initialized."

    try:
        # Find notes matching the title in the collection
        results = collection.get(
            where={"$and": [{"title": title}, {"project": collection_name}]}
        )

        if not results or not results.get("ids"):
            return f"Note '{title}' not found in project {collection_name}."

        # Delete all matching notes
        collection.delete(ids=results["ids"])
        logger.info(f"Deleted note '{title}' from project '{collection_name}'")
        return f"Note '{title}' deleted from project {collection_name}."
    except Exception as e:
        logger.error(f"Failed to delete note '{title}': {e}")
        return f"Failed to delete note: {e}"


@mcp.tool()
def list_notes(collection_name: str = "default", limit: int = 20) -> str:
    """List all notes in a collection."""
    _ensure_initialized()
    if collection is None:
        return "Memory system is not initialized."

    try:
        # Get all notes in the collection
        results = collection.get(
            where={"project": collection_name},
            limit=limit
        )

        if not results or not results.get("ids"):
            return f"No notes found in project {collection_name}."

        output = [f"=== Notes in {collection_name} ==="]
        metas = results.get("metadatas", [])
        docs = results.get("documents", [])

        for i, (meta, doc) in enumerate(zip(metas, docs, strict=False)):
            title = meta.get("title", "Untitled") if meta else "Untitled"
            tags = meta.get("tags", "") if meta else ""
            preview = (doc[:80] + "...") if doc and len(doc) > 80 else (doc or "")
            output.append(f"[{i+1}] {title}")
            if tags:
                output.append(f"    Tags: {tags}")
            output.append(f"    {preview}")

        return "\n".join(output)
    except Exception as e:
        logger.error(f"Failed to list notes: {e}")
        return f"Failed to list notes: {e}"

@mcp.tool()
def update_user_persona(key: str, value: str) -> str:
    """Update user persona (preferences, job, etc.)."""
    memory_file = _memory_file()
    memory_file.parent.mkdir(parents=True, exist_ok=True)

    data = {}
    if memory_file.exists():
        try:
            with memory_file.open() as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    data[key] = value

    with memory_file.open("w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return f"Remembered about you: {key} = {value}"


@mcp.tool()
def get_user_persona() -> str:
    """Read current user persona."""
    memory_file = _memory_file()
    if not memory_file.exists():
        return "No user persona yet."
    with memory_file.open() as f:
        return f.read()


if __name__ == "__main__":
    mcp.run()
