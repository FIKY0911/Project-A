import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from config import DB_PATH

SCHEMA_PATH = Path(__file__).parent / "schema.sql"

class DatabaseManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    def _init_db(self):
        with self.get_connection() as conn:
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            conn.commit()

    def init_session_with_rehydration(self) -> Dict[str, Any]:
        """
        Implements SRD Section 7.2 Session Rehydration & State Recovery:
        1. Query last session
        2. If previous was ONLINE, mark as CRASHED and fetch last 15 conversation logs
        3. Create new session ONLINE
        Returns { "session_id": ..., "recovered_logs": [...] }
        """
        new_session_id = str(uuid.uuid4())
        recovered_logs = []

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT session_id, system_state FROM sessions ORDER BY started_at DESC LIMIT 1;")
            prev_row = cursor.fetchone()

            if prev_row:
                prev_id = prev_row["session_id"]
                prev_state = prev_row["system_state"]
                if prev_state == "ONLINE":
                    # Unclean termination
                    cursor.execute(
                        "UPDATE sessions SET system_state = 'CRASHED', crash_reason = 'ABRUPT_TERMINATION' WHERE session_id = ?;",
                        (prev_id,)
                    )
                    # Fetch last 15 conversation logs
                    cursor.execute(
                        "SELECT role, message_content, timestamp FROM conversation_logs WHERE session_id = ? ORDER BY log_id ASC LIMIT 15;",
                        (prev_id,)
                    )
                    for row in cursor.fetchall():
                        recovered_logs.append({
                            "role": row["role"],
                            "message_content": row["message_content"],
                            "timestamp": row["timestamp"]
                        })

            # Create new session
            cursor.execute(
                "INSERT INTO sessions (session_id, started_at, system_state) VALUES (?, datetime('now'), 'ONLINE');",
                (new_session_id,)
            )
            conn.commit()

        return {
            "session_id": new_session_id,
            "recovered_logs": recovered_logs
        }

    def close_session(self, session_id: str, clean: bool = True):
        with self.get_connection() as conn:
            state = "SHUTDOWN" if clean else "CRASHED"
            conn.execute(
                "UPDATE sessions SET ended_at = datetime('now'), system_state = ? WHERE session_id = ?;",
                (state, session_id)
            )
            conn.commit()

    def log_conversation(self, session_id: str, role: str, content: str, audio_file_path: Optional[str] = None, latency_ms: Optional[int] = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversation_logs (session_id, role, message_content, audio_file_path, latency_ms, timestamp)
                VALUES (?, ?, ?, ?, ?, datetime('now'));
                """,
                (session_id, role, content, audio_file_path, latency_ms)
            )
            conn.commit()
            return cursor.lastrowid

    def get_conversation_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT role, message_content, audio_file_path, timestamp
                FROM conversation_logs
                WHERE session_id = ?
                ORDER BY log_id ASC
                LIMIT ?;
                """,
                (session_id, limit)
            )
            return [dict(row) for row in cursor.fetchall()]

    def create_task(self, task_id: str, session_id: str, initial_prompt: str) -> str:
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO task_executions (task_id, session_id, initial_prompt, status, initiated_at)
                VALUES (?, ?, ?, 'RUNNING', datetime('now'));
                """,
                (task_id, session_id, initial_prompt)
            )
            conn.commit()
        return task_id

    def update_task_status(self, task_id: str, status: str):
        with self.get_connection() as conn:
            finished_clause = ", finished_at = datetime('now')" if status in ("COMPLETED", "ABORTED", "FAILED") else ""
            conn.execute(
                f"UPDATE task_executions SET status = ? {finished_clause} WHERE task_id = ?;",
                (status, task_id)
            )
            conn.commit()

    def log_action(self, task_id: str, action_type: str, target_payload: str, execution_order: int, status: str = "SUCCESS"):
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO action_logs (task_id, action_type, target_payload, execution_order, execution_status, executed_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'));
                """,
                (task_id, action_type, target_payload, execution_order, status)
            )
            conn.commit()

    def log_audit_violation(self, task_id: Optional[str], violation_code: str, flagged_content: str, action_taken: str = "ABORT_TASK"):
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_violations (task_id, violation_code, flagged_content, action_taken, detected_at)
                VALUES (?, ?, ?, ?, datetime('now'));
                """,
                (task_id or "NO_TASK", violation_code, flagged_content, action_taken)
            )
            conn.commit()

    def get_active_llm_config(self) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM llm_configurations WHERE is_active = 1 LIMIT 1;")
            row = cursor.fetchone()
            return dict(row) if row else None

    def save_llm_config(self, provider_name: str, model_name: str, api_key: str, base_url: Optional[str] = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Set all to inactive
            cursor.execute("UPDATE llm_configurations SET is_active = 0;")
            # Insert or update
            cursor.execute(
                """
                INSERT INTO llm_configurations (provider_name, model_name, api_key_encrypted, base_url, is_active, updated_at)
                VALUES (?, ?, ?, ?, 1, datetime('now'));
                """,
                (provider_name, model_name, api_key, base_url)
            )
            conn.commit()
