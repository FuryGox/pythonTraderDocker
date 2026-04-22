import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "accounts.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS account_containers (
                account TEXT NOT NULL,
                platform TEXT NOT NULL,
                server TEXT NOT NULL,
                container_name TEXT NOT NULL,
                PRIMARY KEY (account, platform)
            )
        """)
        conn.commit()


def add_account_container(account: str, platform: str, server: str, container_name: str):
    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO account_containers (account, platform, server, container_name)
            VALUES (?, ?, ?, ?)
        """, (account, platform, server, container_name))
        conn.commit()


def save_account_container(account: str, platform: str, server: str, container_name: str):
    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO account_containers (account, platform, server, container_name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(account, platform) DO UPDATE SET
                server = excluded.server,
                container_name = excluded.container_name
        """, (account, platform, server, container_name))
        conn.commit()


def get_account_container(account: str, platform: str) -> dict | None:
    with _get_conn() as conn:
        row = conn.execute("""
            SELECT * FROM account_containers WHERE account = ? AND platform = ?
        """, (account, platform)).fetchone()
        return dict(row) if row else None


def list_account_containers() -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute("""
            SELECT account, platform, server, container_name
            FROM account_containers
            ORDER BY account, platform
        """).fetchall()
        return [dict(row) for row in rows]


def update_account_container(account: str, platform: str, server: str, container_name: str):
    with _get_conn() as conn:
        cursor = conn.execute("""
            UPDATE account_containers
            SET server = ?, container_name = ?
            WHERE account = ? AND platform = ?
        """, (server, container_name, account, platform))
        conn.commit()
        return cursor.rowcount


def delete_account_container(account: str, platform: str):
    with _get_conn() as conn:
        cursor = conn.execute("""
            DELETE FROM account_containers WHERE account = ? AND platform = ?
        """, (account, platform))
        conn.commit()
        return cursor.rowcount


def clear_account_containers():
    with _get_conn() as conn:
        cursor = conn.execute("DELETE FROM account_containers")
        conn.commit()
        return cursor.rowcount


def delete_account_containers_by_names(container_names: list[str]):
    if not container_names:
        return 0

    placeholders = ", ".join("?" for _ in container_names)
    with _get_conn() as conn:
        cursor = conn.execute(
            f"DELETE FROM account_containers WHERE container_name IN ({placeholders})",
            container_names,
        )
        conn.commit()
        return cursor.rowcount


def delete_account_container_by_name(container_name: str):
    with _get_conn() as conn:
        conn.execute("""
            DELETE FROM account_containers WHERE container_name = ?
        """, (container_name,))
        conn.commit()
