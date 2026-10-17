"""SQLite-backed Persistent Job Store.

Thay thế hoàn toàn in-memory dictionary lưu trữ tác vụ render và production job.
Dữ liệu được lưu bền vững trên ổ đĩa, không bị mất khi restart server hoặc lỗi tiến trình.
"""
from __future__ import annotations

import collections.abc
import datetime
import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

logger = logging.getLogger(__name__)

# Default SQLite database path in data/
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "jobs.db"


class SQLiteJobStore:
    """Quản lý lưu trữ SQLite cho Export Jobs và Production Jobs."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS export_jobs (
                    job_id TEXT PRIMARY KEY,
                    project_id TEXT,
                    title TEXT,
                    status TEXT,
                    stage TEXT,
                    progress_percent REAL,
                    video_url TEXT,
                    error_message TEXT,
                    qa_report_json TEXT,
                    metadata_json TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS production_jobs (
                    job_id TEXT PRIMARY KEY,
                    title TEXT,
                    prompt TEXT,
                    status TEXT,
                    current_stage TEXT,
                    progress_percent REAL,
                    job_data_json TEXT,
                    job_details_json TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
            conn.commit()

    # --- Export Jobs Operations ---

    def save_export_job(self, job_id: str, data: Dict[str, Any]) -> None:
        """Lưu hoặc cập nhật thông tin export job."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        qa_json = json.dumps(data.get("qa_report")) if data.get("qa_report") is not None else None
        
        # Lưu các trường khác vào metadata_json nếu có
        meta = {k: v for k, v in data.items() if k not in [
            "job_id", "project_id", "title", "status", "stage",
            "progress_percent", "video_url", "error_message", "qa_report",
            "created_at", "updated_at"
        ]}
        meta_json = json.dumps(meta) if meta else None

        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO export_jobs (
                    job_id, project_id, title, status, stage,
                    progress_percent, video_url, error_message,
                    qa_report_json, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    project_id = COALESCE(excluded.project_id, export_jobs.project_id),
                    title = COALESCE(excluded.title, export_jobs.title),
                    status = excluded.status,
                    stage = excluded.stage,
                    progress_percent = excluded.progress_percent,
                    video_url = COALESCE(excluded.video_url, export_jobs.video_url),
                    error_message = COALESCE(excluded.error_message, export_jobs.error_message),
                    qa_report_json = COALESCE(excluded.qa_report_json, export_jobs.qa_report_json),
                    metadata_json = COALESCE(excluded.metadata_json, export_jobs.metadata_json),
                    updated_at = excluded.updated_at
                """,
                (
                    job_id,
                    data.get("project_id", "default"),
                    data.get("title", "Whiteboard Video"),
                    data.get("status", "pending"),
                    data.get("stage", "Khởi tạo..."),
                    float(data.get("progress_percent", 0.0)),
                    data.get("video_url"),
                    data.get("error_message"),
                    qa_json,
                    meta_json,
                    data.get("created_at", now),
                    now,
                ),
            )
            conn.commit()

    def get_export_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin export job theo job_id."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM export_jobs WHERE job_id = ?", (job_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_export_dict(row)

    def list_export_jobs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Danh sách các export job theo thứ tự mới nhất."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM export_jobs ORDER BY created_at DESC LIMIT ?", (limit,)
            )
            return [self._row_to_export_dict(r) for r in cursor.fetchall()]

    def delete_export_job(self, job_id: str) -> bool:
        """Xóa một export job."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM export_jobs WHERE job_id = ?", (job_id,))
            conn.commit()
            return cursor.rowcount > 0

    def _row_to_export_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        qa = json.loads(row["qa_report_json"]) if row["qa_report_json"] else None
        meta = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
        res = {
            "job_id": row["job_id"],
            "project_id": row["project_id"],
            "title": row["title"],
            "status": row["status"],
            "stage": row["stage"],
            "progress_percent": row["progress_percent"],
            "video_url": row["video_url"],
            "error_message": row["error_message"],
            "qa_report": qa,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        res.update(meta)
        return res

    # --- Production Jobs Operations ---

    def save_production_job(self, job_id: str, job_dict: Dict[str, Any], details: Optional[Dict[str, Any]] = None) -> None:
        """Lưu hoặc cập nhật thông tin production job."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        job_json = json.dumps(job_dict)
        details_json = json.dumps(details) if details is not None else None

        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO production_jobs (
                    job_id, title, prompt, status, current_stage,
                    progress_percent, job_data_json, job_details_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_id) DO UPDATE SET
                    title = excluded.title,
                    prompt = excluded.prompt,
                    status = excluded.status,
                    current_stage = excluded.current_stage,
                    progress_percent = excluded.progress_percent,
                    job_data_json = excluded.job_data_json,
                    job_details_json = COALESCE(excluded.job_details_json, production_jobs.job_details_json),
                    updated_at = excluded.updated_at
                """,
                (
                    job_id,
                    job_dict.get("title", ""),
                    job_dict.get("prompt", ""),
                    str(job_dict.get("status", "pending")),
                    str(job_dict.get("current_stage", "init")),
                    float(job_dict.get("progress_percent", 0.0)),
                    job_json,
                    details_json,
                    job_dict.get("created_at", now),
                    now,
                ),
            )
            conn.commit()

    def get_production_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Lấy dict data của production job."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT job_data_json FROM production_jobs WHERE job_id = ?", (job_id,)
            )
            row = cursor.fetchone()
            if not row or not row["job_data_json"]:
                return None
            return json.loads(row["job_data_json"])

    def get_production_job_details(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Lấy chi tiết config của production job."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT job_details_json FROM production_jobs WHERE job_id = ?", (job_id,)
            )
            row = cursor.fetchone()
            if not row or not row["job_details_json"]:
                return None
            return json.loads(row["job_details_json"])

    def list_production_jobs(self) -> List[Dict[str, Any]]:
        """Lấy toàn bộ danh sách production jobs."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT job_data_json FROM production_jobs ORDER BY created_at DESC"
            )
            res = []
            for r in cursor.fetchall():
                if r["job_data_json"]:
                    res.append(json.loads(r["job_data_json"]))
            return res


class ExportJobRecordProxy(collections.abc.MutableMapping):
    """
    Proxy cho một bản ghi export job, đồng bộ tức thì các thay đổi xuống SQLite
    khi truy cập theo cú pháp dict thông thường: job_record["stage"] = "..."
    """

    def __init__(self, store: SQLiteJobStore, job_id: str, data: Dict[str, Any]):
        self._store = store
        self._job_id = job_id
        self._data = dict(data)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._store.save_export_job(self._job_id, self._data)

    def __delitem__(self, key: str) -> None:
        del self._data[key]
        self._store.save_export_job(self._job_id, self._data)

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)


class ExportJobStoreDict(collections.abc.MutableMapping):
    """
    Adapter tương thích 100% với cú pháp dict `_EXPORT_JOBS[job_id]` hiện có,
    nhưng lưu trữ bền vững trong SQLite.
    """

    def __init__(self, store: Optional[SQLiteJobStore] = None):
        self._store = store or SQLiteJobStore()

    def __getitem__(self, job_id: str) -> ExportJobRecordProxy:
        data = self._store.get_export_job(job_id)
        if data is None:
            raise KeyError(job_id)
        return ExportJobRecordProxy(self._store, job_id, data)

    def __setitem__(self, job_id: str, value: Dict[str, Any]) -> None:
        self._store.save_export_job(job_id, value)

    def __delitem__(self, job_id: str) -> None:
        if not self._store.delete_export_job(job_id):
            raise KeyError(job_id)

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        return self._store.get_export_job(key) is not None

    def __iter__(self) -> Iterator[str]:
        jobs = self._store.list_export_jobs()
        return iter([j["job_id"] for j in jobs])

    def __len__(self) -> int:
        return len(self._store.list_export_jobs())


# Global singleton store instance
global_job_store = SQLiteJobStore()
