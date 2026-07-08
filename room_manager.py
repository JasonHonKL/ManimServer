from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class RoomSnapshot:
    room_id: str
    name: str = ""
    assigned_at: str = ""


class RoomManager:
    def __init__(self, room_count: int):
        if room_count < 1:
            raise ValueError("room_count must be >= 1")
        self._count = room_count
        self._rooms = [f"student-{i:02d}" for i in range(1, room_count + 1)]
        self._name_to_room: dict[str, str] = {}
        self._room_to_name: dict[str, str] = {}
        self._assigned_at: dict[str, float] = {}

    @property
    def rooms(self) -> list[str]:
        return self._rooms

    @property
    def occupied(self) -> int:
        return len(self._room_to_name)

    @property
    def total(self) -> int:
        return len(self._rooms)

    @property
    def available(self) -> int:
        return len(self._rooms) - len(self._room_to_name)

    def assign(self, name: str) -> str | None:
        """Assign a room to name. Returns room_id or None if full."""
        if not name or not name.strip():
            return None

        name = name.strip()
        if name in self._name_to_room:
            return self._name_to_room[name]

        free = [r for r in self._rooms if r not in self._room_to_name]
        if not free:
            return None

        room = free[0]
        self._name_to_room[name] = room
        self._room_to_name[room] = name
        self._assigned_at[room] = time.time()
        return room

    def leave(self, name: str) -> str | None:
        """Remove a name→room mapping. Returns freed room_id or None."""
        room = self._name_to_room.pop(name, None)
        if room:
            self._room_to_name.pop(room, None)
            self._assigned_at.pop(room, None)
        return room

    def auth(self, room_id: str, name: str) -> bool:
        """Check if name is authorized for room_id."""
        if not name or not room_id:
            return False

        owner = self._room_to_name.get(room_id)
        if owner is None:
            return False

        return owner == name

    def reset(self, room_id: str) -> str | None:
        """Reset a room, returning the freed name or None."""
        name = self._room_to_name.pop(room_id, None)
        if name:
            self._name_to_room.pop(name, None)
            self._assigned_at.pop(room_id, None)
        return name

    def is_assigned(self, name: str) -> bool:
        return name in self._name_to_room

    def room_for_name(self, name: str) -> str | None:
        return self._name_to_room.get(name)

    def name_for_room(self, room_id: str) -> str | None:
        return self._room_to_name.get(room_id)

    def snapshot(self) -> list[RoomSnapshot]:
        result = []
        for room in self._rooms:
            name = self._room_to_name.get(room, "")
            ts = self._assigned_at.get(room)
            t = time.strftime("%H:%M:%S", time.localtime(ts)) if ts else ""
            result.append(RoomSnapshot(room_id=room, name=name, assigned_at=t))
        return result

    def reset_all(self) -> int:
        """Clear all room assignments. Returns count of rooms freed."""
        count = len(self._room_to_name)
        self._name_to_room.clear()
        self._room_to_name.clear()
        self._assigned_at.clear()
        return count
