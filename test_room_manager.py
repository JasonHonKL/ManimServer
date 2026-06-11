import pytest
from room_manager import RoomManager


class TestRoomManagerInit:
    def test_creates_correct_number_of_rooms(self):
        rm = RoomManager(5)
        assert rm.total == 5
        assert rm.rooms == ["student-01", "student-02", "student-03", "student-04", "student-05"]

    def test_zero_rooms_raises(self):
        with pytest.raises(ValueError):
            RoomManager(0)

    def test_negative_rooms_raises(self):
        with pytest.raises(ValueError):
            RoomManager(-1)

    def test_starts_empty(self):
        rm = RoomManager(10)
        assert rm.occupied == 0
        assert rm.available == 10


class TestRoomManagerAssign:
    def test_assign_returns_first_room(self, rm):
        room = rm.assign("Alice")
        assert room == "student-01"

    def test_assign_fills_sequentially(self, rm):
        assert rm.assign("Alice") == "student-01"
        assert rm.assign("Bob") == "student-02"
        assert rm.assign("Carol") == "student-03"

    def test_assign_same_name_returns_same_room(self, rm):
        rm.assign("Alice")
        assert rm.assign("Alice") == "student-01"

    def test_assign_returns_none_when_full(self, rm):
        for name in ["A", "B", "C"]:
            rm.assign(name)
        assert rm.assign("D") is None

    def test_assign_empty_string_returns_none(self, rm):
        assert rm.assign("") is None
        assert rm.assign("   ") is None

    def test_assign_tracks_occupancy(self, rm):
        assert rm.occupied == 0
        rm.assign("Alice")
        assert rm.occupied == 1
        assert rm.available == 2


class TestRoomManagerLeave:
    def test_leave_removes_assignment(self, rm):
        rm.assign("Alice")
        room = rm.leave("Alice")
        assert room == "student-01"
        assert rm.occupied == 0

    def test_leave_unknown_name_returns_none(self, rm):
        assert rm.leave("Nobody") is None

    def test_leave_frees_room_for_reassignment(self, rm):
        rm.assign("Alice")
        rm.assign("Bob")
        rm.leave("Alice")
        assert rm.assign("Carol") == "student-01"


class TestRoomManagerAuth:
    def test_auth_with_correct_name(self, rm):
        rm.assign("Alice")
        assert rm.auth("student-01", "Alice") is True

    def test_auth_with_wrong_name(self, rm):
        rm.assign("Alice")
        assert rm.auth("student-01", "Bob") is False

    def test_auth_auto_claims_unassigned(self, rm):
        assert rm.auth("student-01", "Alice") is True
        assert rm.name_for_room("student-01") == "Alice"

    def test_auth_empty_name_fails(self, rm):
        assert rm.auth("student-01", "") is False


class TestRoomManagerReset:
    def test_reset_clears_room(self, rm):
        rm.assign("Alice")
        name = rm.reset("student-01")
        assert name == "Alice"
        assert rm.name_for_room("student-01") is None

    def test_reset_unknown_room(self, rm):
        assert rm.reset("student-99") is None


class TestRoomManagerSnapshot:
    def test_snapshot_empty(self, rm):
        snaps = rm.snapshot()
        assert len(snaps) == 3
        assert all(s.name == "" for s in snaps)

    def test_snapshot_populated(self, rm):
        rm.assign("Alice")
        snaps = rm.snapshot()
        assert snaps[0].name == "Alice"
        assert snaps[1].name == ""


class TestRoomManagerQueries:
    def test_is_assigned(self, rm):
        assert rm.is_assigned("Alice") is False
        rm.assign("Alice")
        assert rm.is_assigned("Alice") is True

    def test_room_for_name(self, rm):
        rm.assign("Alice")
        assert rm.room_for_name("Alice") == "student-01"
        assert rm.room_for_name("Nobody") is None

    def test_name_for_room(self, rm):
        rm.assign("Alice")
        assert rm.name_for_room("student-01") == "Alice"
        assert rm.name_for_room("student-99") is None
