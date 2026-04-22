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


def delete_account_container_by_name(container_name: str):
    with _get_conn() as conn:
        conn.execute("""
            DELETE FROM account_containers WHERE container_name = ?
        """, (container_name,))
        conn.commit()
