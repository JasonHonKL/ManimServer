import pytest
from room_manager import RoomManager
from settings import Config

TEST_CONFIG = Config(
    num_students=3,
    cpu="0.5",
    memory="1g",
    base_port=8001,
    auth_port=9000,
    nginx_port=8080,
    image="test",
    data_dir="data",
    workspaces_dir="workspaces",
    admin_password="testpass",
)


@pytest.fixture
def rm() -> RoomManager:
    return RoomManager(3)


@pytest.fixture
def rooms() -> RoomManager:
    return RoomManager(3)


@pytest.fixture
def client() -> "TestClient":
    import auth_server
    from fastapi.testclient import TestClient
    auth_server.rooms = RoomManager(3)
    auth_server.config = TEST_CONFIG
    return TestClient(auth_server.app)
