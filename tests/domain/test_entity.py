from amoneyplan.domain import Entity


def test_entity_id():
    entity = Entity("abc")
    assert entity.id == "abc"
