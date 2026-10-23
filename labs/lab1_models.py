from enum import Enum
from typing import Optional


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
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.zone_type: ZoneType = zone_type
        self.color: Optional[str] = color
        self.max_drones: int = max_drones
        self.current_drones: int = 0

    @property
    def movement_cost(self) -> int:
        if self.zone_type == ZoneType.RESTRICTED:
            return 2
        return 1

    @property
    def is_accessible(self) -> bool:
        return self.zone_type != ZoneType.BLOCKED

    def has_capacity(self) -> bool:
        return self.current_drones < self.max_drones

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
        self.zone_a: Zone = zone_a
        self.zone_b: Zone = zone_b
        self.max_link_capacity: int = max_link_capacity
        self.current_load: int = 0

    def get_other(self, zone: Zone) -> Zone:
        if zone == self.zone_a:
            return self.zone_b
        return self.zone_a

    def has_capacity(self) -> bool:
        return self.current_load < self.max_link_capacity

    def __repr__(self) -> str:
        return (
            f"Connection({self.zone_a.name} <-> {self.zone_b.name}, "
            f"cap={self.max_link_capacity})"
        )


class Drone:
    def __init__(self, drone_id: int, start_zone: Zone) -> None:
        self.id: int = drone_id
        self.current_zone: Zone = start_zone

    @property
    def name(self) -> str:
        return f"D{self.id}"

    def __repr__(self) -> str:
        return f"Drone({self.name} at {self.current_zone.name})"


# تجربة بسيطة وسريعة للتأكد من عمل الكائنات
if __name__ == "__main__":
    hub1 = Zone("start_hub", 0, 0, ZoneType.NORMAL)
    hub2 = Zone("roof1", 3, 4, ZoneType.RESTRICTED, max_drones=2)
    conn = Connection(hub1, hub2, max_link_capacity=1)
    drone1 = Drone(1, hub1)
    print("Created successfully:")
    print(hub1)
    print(hub2, "-> Movement cost:", hub2.movement_cost)
    print(conn)
    print(drone1)
