"""Unit tests for SQLite-backed Job Store."""
import pytest
from pathlib import Path
from core.storage.job_store import SQLiteJobStore, ExportJobStoreDict


def test_sqlite_job_store_crud(tmp_path: Path):
    db_file = tmp_path / "test_jobs.db"
    store = SQLiteJobStore(db_path=db_file)

    # 1. Create export job
    store.save_export_job(
        "job-exp-01",
        {
            "project_id": "proj-1",
            "title": "Dog Running",
            "status": "pending",
            "stage": "Initializing...",
            "progress_percent": 10.0,
        },
    )

    # 2. Get export job
    job = store.get_export_job("job-exp-01")
    assert job is not None
    assert job["job_id"] == "job-exp-01"
    assert job["status"] == "pending"
    assert job["progress_percent"] == 10.0
    assert job["stage"] == "Initializing..."

    # 3. Update export job
    store.save_export_job(
        "job-exp-01",
        {
            "status": "completed",
            "stage": "Finished rendering!",
            "progress_percent": 100.0,
            "video_url": "/output/dog.mp4",
        },
    )
    updated = store.get_export_job("job-exp-01")
    assert updated is not None
    assert updated["status"] == "completed"
    assert updated["progress_percent"] == 100.0
    assert updated["video_url"] == "/output/dog.mp4"

    # 4. List jobs
    jobs = store.list_export_jobs()
    assert len(jobs) == 1
    assert jobs[0]["job_id"] == "job-exp-01"

    # 5. Delete job
    assert store.delete_export_job("job-exp-01") is True
    assert store.get_export_job("job-exp-01") is None


def test_export_job_store_dict_proxy(tmp_path: Path):
    db_file = tmp_path / "test_jobs_proxy.db"
    store = SQLiteJobStore(db_path=db_file)
    jobs_dict = ExportJobStoreDict(store=store)

    # Set item
    jobs_dict["export-test-99"] = {
        "status": "running",
        "stage": "Drawing strokes...",
        "progress_percent": 45.0,
    }
    assert "export-test-99" in jobs_dict

    # Proxy update in place
    record = jobs_dict["export-test-99"]
    record["stage"] = "Synthesizing voice..."
    record["progress_percent"] = 75.0

    # Verify directly from fresh store instance
    fresh_store = SQLiteJobStore(db_path=db_file)
    saved = fresh_store.get_export_job("export-test-99")
    assert saved is not None
    assert saved["stage"] == "Synthesizing voice..."
    assert saved["progress_percent"] == 75.0

    # Delete
    del jobs_dict["export-test-99"]
    assert "export-test-99" not in jobs_dict
