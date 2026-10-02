from core.schemas.annotation import CanvasSchema
from core.schemas.scene_graph import (
    Position,
    SceneGraph,
    VisualEntity,
    VisualRelationship,
)


def test_scene_graph_creation_and_traversal():
    graph = SceneGraph(
        entities=[
            VisualEntity(
                id="monkey",
                label="monkey",
                category="character",
                position=Position(x=100, y=100, width=200, height=300),
                layer=1,
            ),
            VisualEntity(
                id="tree",
                label="tree",
                category="structure",
                position=Position(x=50, y=50, width=500, height=800),
                layer=0,
            ),
        ],
        relationships=[
            VisualRelationship(
                id="rel-1",
                source_id="monkey",
                target_id="tree",
                relation_type="climbing",
                action="trèo",
            )
        ],
    )

    assert len(graph.entities) == 2
    assert len(graph.relationships) == 1

    monkey = graph.get_entity("monkey")
    assert monkey is not None
    assert monkey.category == "character"

    tree = graph.get_entity("tree")
    assert tree is not None
    assert tree.layer == 0

    rels = graph.get_relationships_for("monkey")
    assert len(rels) == 1
    assert rels[0].relation_type == "climbing"
