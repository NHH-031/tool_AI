from core.jobs.models import JobStage, JobStatus, ProductionJob


def test_production_job_lifecycle():
    job = ProductionJob.create_default(title="Test Whiteboard Video", prompt="Làm video về AI")
    assert job.title == "Test Whiteboard Video"
    assert job.status == JobStatus.PENDING
    assert job.current_stage == JobStage.QUEUED
    assert len(job.stages) == 8

    # Chuyển trạng thái sang script generation
    job.transition_to(JobStage.SCRIPT_GENERATION, JobStatus.RUNNING)
    assert job.current_stage == JobStage.SCRIPT_GENERATION
    assert job.status == JobStatus.RUNNING

    # Hoàn thành stage
    job.transition_to(JobStage.SCRIPT_GENERATION, JobStatus.COMPLETED)
    stage_prog = next(s for s in job.stages if s.stage == JobStage.SCRIPT_GENERATION)
    assert stage_prog.status == JobStatus.COMPLETED
    assert stage_prog.started_at is not None
    assert stage_prog.completed_at is not None
