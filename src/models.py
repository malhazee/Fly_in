from enum import Enum
from typing import List, Optional, Tuple


class ZoneType(Enum):

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone:

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: ZoneType = ZoneType.NORMAL,
        color: Optional[str] = None,
        max_drones: int = 1,
    ) -> None:
        if "-" in name:
            raise ValueError(f"Zone name '{name}' cannot contain dashes")
        if max_drones < 1:
            raise ValueError("max_drones must be at least 1")

        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.zone_type: ZoneType = zone_type
        self.color: Optional[str] = color
        self.max_drones: int = max_drones
        self.transit_conn: Optional[Tuple[str, str]] = None

    @property
    def movement_cost(self) -> int:
        if self.zone_type == ZoneType.RESTRICTED:
            return 2
        return 1

    @property
    def is_accessible(self) -> bool:
        return self.zone_type != ZoneType.BLOCKED

    def __repr__(self) -> str:
        return (
            f"Zone({self.name}, "
            f"type={self.zone_type.value}, "
            f"cap={self.max_drones})"
        )


class Connection:

    def __init__(
        self,
        zone_a: Zone,
        zone_b: Zone,
        max_link_capacity: int = 1,
    ) -> None:
        if zone_a.name == zone_b.name:
            raise ValueError("Connection cannot connect a zone to itself")
        if max_link_capacity < 1:
            raise ValueError("max_link_capacity must be at least 1")

        self.zone_a: Zone = zone_a
        self.zone_b: Zone = zone_b
        self.max_link_capacity: int = max_link_capacity

    def get_other(self, zone: Zone) -> Zone:
        if zone.name == self.zone_a.name:
            return self.zone_b
        if zone.name == self.zone_b.name:
            return self.zone_a
        raise ValueError(f"Zone '{zone.name}' is not part of this connection")

    @property
    def key(self) -> tuple[str, str]:
        return (
            min(self.zone_a.name, self.zone_b.name),
            max(self.zone_a.name, self.zone_b.name),
        )

    def __repr__(self) -> str:
        return (
            f"Connection({self.zone_a.name} <-> {self.zone_b.name}, "
            f"cap={self.max_link_capacity})"
        )


class DroneState:

    def __init__(
        self,
        drone_id: int,
        path: List[str],
        start_turn: int = 0,
    ) -> None:
        self.id: int = drone_id
        self.path: List[str] = path
        self.step_idx: int = 0
        self.wait_turns: int = 0
        self.start_turn: int = start_turn
        self.has_arrived: bool = False
        self.transit_conn: Optional[Tuple[str, str]] = None

    @property
    def name(self) -> str:
        return f"D{self.id}"

    @property
    def current_zone(self) -> str:
        return self.path[self.step_idx]

    @property
    def next_zone(self) -> Optional[str]:
        if self.step_idx + 1 < len(self.path):
            return self.path[self.step_idx + 1]
        return None

    def __repr__(self) -> str:
        return f"DroneState({self.name}, at={self.current_zone})"
