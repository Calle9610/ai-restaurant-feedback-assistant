from agent import db


def test_agent_package_importable():
    assert db.get_client is not None
    assert db.get_service_client is not None
