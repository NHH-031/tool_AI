def test_core_imports():
    import core.schemas
    import core.jobs
    import core.providers
    import core.orchestrator
    import core.templates
    import core.assets
    import agents
    import engines.whiteboard
    import audio
    import compositor
    import apps.api

    assert core.schemas is not None
    assert core.jobs is not None
    assert core.providers is not None
    assert core.orchestrator is not None
    assert core.templates is not None
    assert core.assets is not None
    assert agents is not None
    assert engines.whiteboard is not None
    assert audio is not None
    assert compositor is not None
    assert apps.api is not None
