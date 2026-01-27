
import json
import logging
import sqlite3

from mcp.server.fastmcp import FastMCP

from src.core.security import validate_path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("DoraemonDatabase")


def _get_connection(db_path: str) -> sqlite3.Connection:
    """Get a connection to the SQLite database."""
    # Security check: ensure path is valid
    valid_path = validate_path(db_path)

    conn = sqlite3.connect(valid_path)
    conn.row_factory = sqlite3.Row
    return conn


@mcp.tool()
def db_read_query(query: str, db_path: str) -> str:
    """
    Execute a SELECT query on a SQLite database.

    Args:
        query: The SQL SELECT statement
        db_path: Path to the SQLite database file

    Returns:
        JSON string of the results or error message
    """
    if not query.strip().lower().startswith("select"):
        return "Error: Only SELECT queries are allowed in db_read_query. Use db_write_query for modifications."

    try:
        conn = _get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        # Convert rows to dicts
        results = [dict(row) for row in rows]

        if not results:
            return "No results found."

        return json.dumps(results, indent=2, default=str)

    except Exception as e:
        logger.error(f"Database error: {e}")
        return f"Database error: {str(e)}"


@mcp.tool()
def db_write_query(query: str, db_path: str) -> str:
    """
    Execute an INSERT, UPDATE, DELETE, or CREATE query on a SQLite database.

    Args:
        query: The SQL statement
        db_path: Path to the SQLite database file

    Returns:
        Success message or error
    """
    try:
        conn = _get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        row_count = cursor.rowcount
        conn.close()

        return f"Query executed successfully. Rows affected: {row_count}"

    except Exception as e:
        logger.error(f"Database error: {e}")
        return f"Database error: {str(e)}"


@mcp.tool()
def db_list_tables(db_path: str) -> str:
    """
    List all tables in the SQLite database.

    Args:
        db_path: Path to the SQLite database file
    """
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    return str(db_read_query(query, db_path))


@mcp.tool()
def db_describe_table(table_name: str, db_path: str) -> str:
    """
    Get the schema of a specific table.

    Args:
        table_name: Name of the table
        db_path: Path to the SQLite database file
    """
    query = f"PRAGMA table_info({table_name});"
    try:
        conn = _get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return f"Table '{table_name}' not found or empty schema."

        # Format output nicely
        output = [f"Schema for {table_name}:"]
        for row in rows:
            # cid, name, type, notnull, dflt_value, pk
            output.append(f"- {row['name']} ({row['type']}) {'PK' if row['pk'] else ''}")

        return "\n".join(output)
    except Exception as e:
        return f"Error describing table: {e}"


if __name__ == "__main__":
    mcp.run()
