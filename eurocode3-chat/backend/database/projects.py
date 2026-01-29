"""
Project Management Database.
Groups conversations and calculations into engineering projects.
"""
import sqlite3
import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
import threading


class ProjectManager:
    """SQLite-based project management."""

    _local = threading.local()

    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path
        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.connection.row_factory = sqlite3.Row
            self._local.connection.execute("PRAGMA foreign_keys = ON")
        return self._local.connection

    @contextmanager
    def _get_cursor(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e

    def _init_tables(self):
        with self._get_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    client TEXT DEFAULT '',
                    location TEXT DEFAULT '',
                    steel_grade TEXT DEFAULT 'S355',
                    national_annex TEXT DEFAULT 'EC',
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_conversations (
                    project_id TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    PRIMARY KEY (project_id, conversation_id),
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS saved_calculations (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    name TEXT NOT NULL,
                    calc_type TEXT NOT NULL,
                    input_data TEXT NOT NULL,
                    result_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_saved_calcs_project
                ON saved_calculations(project_id)
            """)

    # ---- Project CRUD ----

    def create_project(self, name: str, description: str = "",
                       client: str = "", location: str = "",
                       steel_grade: str = "S355", national_annex: str = "EC") -> str:
        project_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        with self._get_cursor() as cursor:
            cursor.execute(
                """INSERT INTO projects (id,name,description,client,location,steel_grade,national_annex,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (project_id, name, description, client, location, steel_grade, national_annex, now, now)
            )
        return project_id

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        with self._get_cursor() as cursor:
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            if not row:
                return None

            # Get linked conversations
            cursor.execute(
                "SELECT conversation_id FROM project_conversations WHERE project_id = ?",
                (project_id,)
            )
            conv_ids = [r["conversation_id"] for r in cursor.fetchall()]

            # Get saved calculations
            cursor.execute(
                "SELECT id, name, calc_type, created_at FROM saved_calculations WHERE project_id = ?",
                (project_id,)
            )
            calcs = [dict(r) for r in cursor.fetchall()]

            return {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "client": row["client"],
                "location": row["location"],
                "steel_grade": row["steel_grade"],
                "national_annex": row["national_annex"],
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "conversation_ids": conv_ids,
                "calculations": calcs,
            }

    def list_projects(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with self._get_cursor() as cursor:
            cursor.execute("""
                SELECT p.*, COUNT(DISTINCT pc.conversation_id) as conv_count,
                       COUNT(DISTINCT sc.id) as calc_count
                FROM projects p
                LEFT JOIN project_conversations pc ON p.id = pc.project_id
                LEFT JOIN saved_calculations sc ON p.id = sc.project_id
                GROUP BY p.id
                ORDER BY p.updated_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return [dict(r) for r in cursor.fetchall()]

    def update_project(self, project_id: str, **kwargs) -> bool:
        allowed = {"name", "description", "client", "location", "steel_grade", "national_annex", "status"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False

        updates["updated_at"] = datetime.utcnow().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [project_id]

        with self._get_cursor() as cursor:
            cursor.execute(f"UPDATE projects SET {set_clause} WHERE id = ?", values)
            return cursor.rowcount > 0

    def delete_project(self, project_id: str) -> bool:
        with self._get_cursor() as cursor:
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            return cursor.rowcount > 0

    # ---- Link conversations to projects ----

    def link_conversation(self, project_id: str, conversation_id: str) -> bool:
        with self._get_cursor() as cursor:
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO project_conversations (project_id, conversation_id) VALUES (?, ?)",
                    (project_id, conversation_id)
                )
                return True
            except Exception:
                return False

    def unlink_conversation(self, project_id: str, conversation_id: str) -> bool:
        with self._get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM project_conversations WHERE project_id = ? AND conversation_id = ?",
                (project_id, conversation_id)
            )
            return cursor.rowcount > 0

    # ---- Saved calculations ----

    def save_calculation(self, name: str, calc_type: str,
                         input_data: Dict, result_data: Dict,
                         project_id: Optional[str] = None) -> str:
        calc_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        with self._get_cursor() as cursor:
            cursor.execute(
                """INSERT INTO saved_calculations (id, project_id, name, calc_type, input_data, result_data, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (calc_id, project_id, name, calc_type, json.dumps(input_data), json.dumps(result_data), now)
            )
        return calc_id

    def get_calculation(self, calc_id: str) -> Optional[Dict[str, Any]]:
        with self._get_cursor() as cursor:
            cursor.execute("SELECT * FROM saved_calculations WHERE id = ?", (calc_id,))
            row = cursor.fetchone()
            if not row:
                return None
            result = dict(row)
            result["input_data"] = json.loads(result["input_data"])
            result["result_data"] = json.loads(result["result_data"])
            return result

    def list_calculations(self, project_id: Optional[str] = None,
                          calc_type: Optional[str] = None,
                          limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_cursor() as cursor:
            query = "SELECT id, project_id, name, calc_type, created_at FROM saved_calculations WHERE 1=1"
            params = []
            if project_id:
                query += " AND project_id = ?"
                params.append(project_id)
            if calc_type:
                query += " AND calc_type = ?"
                params.append(calc_type)
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]

    def delete_calculation(self, calc_id: str) -> bool:
        with self._get_cursor() as cursor:
            cursor.execute("DELETE FROM saved_calculations WHERE id = ?", (calc_id,))
            return cursor.rowcount > 0
