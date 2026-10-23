from typing import Dict, List, Optional, Tuple

from src.models import Connection, Zone


class Graph:

    def __init__(self) -> None:
        self.zones: Dict[str, Zone] = {}
        self.adjacency: Dict[str, List[Connection]] = {}
        self.start_zone: Optional[Zone] = None
        self.end_zone: Optional[Zone] = None

    def add_zone(
        self,
        zone: Zone,
        is_start: bool = False,
        is_end: bool = False,
    ) -> None:
        if zone.name in self.zones:
            raise ValueError(f"Duplicate zone name: '{zone.name}'")
        if is_start:
            if self.start_zone is not None:
                raise ValueError("Graph can only have one start zone")
            self.start_zone = zone
        if is_end:
            if self.end_zone is not None:
                raise ValueError("Graph can only have one end zone")
            self.end_zone = zone

        self.zones[zone.name] = zone
        self.adjacency[zone.name] = []

    def add_connection(
        self,
        name_a: str,
        name_b: str,
        max_link_capacity: int = 1,
    ) -> Connection:
        if name_a not in self.zones or name_b not in self.zones:
            raise ValueError(
                f"Cannot connect unknown zones: {name_a}-{name_b}"
            )

        zone_a = self.zones[name_a]
        zone_b = self.zones[name_b]

        for existing in self.adjacency[name_a]:
            if existing.get_other(zone_a).name == name_b:
                raise ValueError(
                    f"Duplicate connection between '{name_a}' and '{name_b}'"
                )

        conn = Connection(zone_a, zone_b, max_link_capacity)
        self.adjacency[name_a].append(conn)
        self.adjacency[name_b].append(conn)
        return conn

    def get_neighbors(self, zone: Zone) -> List[Tuple[Zone, Connection]]:
        neighbors: List[Tuple[Zone, Connection]] = []
        for conn in self.adjacency.get(zone.name, []):
            other = conn.get_other(zone)
            if other.is_accessible:
                neighbors.append((other, conn))
        return neighbors

    def get_connection(
        self,
        name_a: str,
        name_b: str,
    ) -> Optional[Connection]:
        for conn in self.adjacency.get(name_a, []):
            if conn.get_other(self.zones[name_a]).name == name_b:
                return conn
        return None

    def validate(self) -> None:
        if self.start_zone is None:
            raise ValueError("Invalid graph: missing start zone")
        if self.end_zone is None:
            raise ValueError("Invalid graph: missing end zone")
        if self.start_zone.name == self.end_zone.name:
            raise ValueError("Start and end zones must be distinct")
        if not self.adjacency[self.start_zone.name]:
            raise ValueError("Start zone has no outgoing connections")
        if not self.adjacency[self.end_zone.name]:
            raise ValueError("End zone has no incoming connections")
