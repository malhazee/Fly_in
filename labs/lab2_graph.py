from typing import Dict, List, Optional, Tuple
from lab1_models import Connection, Zone, ZoneType


class Graph:
    def __init__(self) -> None:
        self.zones: Dict[str, Zone] = {}
        self.adjacency: Dict[str, list[Connection]] = {}
        self.start_zone: Optional[Zone] = None
        self.end_zone: Optional[Zone] = None

    def add_zone(
            self,
            zone: Zone,
            is_start: bool = False,
            is_end: bool = False
    ) -> None:
        if zone.name in self.zones:
            raise ValueError(f"Duplicate zone name: {zone.name}")

        self.zones[zone.name] = zone
        self.adjacency[zone.name] = []

        if is_start:
            if self.start_zone is not None:
                raise ValueError("Graph already has start_hub")
            self.start_zone = zone

        if is_end:
            if self.end_zone is not None:
                raise ValueError("Graph already has an end_hub")
            self.end_zone = zone

    def add_connection(
            self,
            name_a: str,
            name_b: str,
            max_link_capacity: int = 1,
    ) -> Connection:
        if name_a not in self.zones or name_b not in self.zones:
            raise KeyError(f"Zones not found: {name_a} or {name_b}")

        zone_a = self.zones[name_a]
        zone_b = self.zones[name_b]

        conn = Connection(zone_a, zone_b, max_link_capacity)
        self.adjacency[name_a].append(conn)
        self.adjacency[name_b].append(conn)
        return conn

    def get_neighbors(
            self,
            zone: Zone,
    ) -> List[Tuple[Zone, Connection]]:
        neighbors: List[Tuple[Zone, Connection]] = []
        for conn in self.adjacency.get(zone.name,  []):
            other = conn.get_other(zone)
            if other.is_accessible:
                neighbors.append((other, conn))
        return neighbors

    def validate(self) -> None:
        if self.start_zone is None:
            raise ValueError("Missing atart_hub in the graph")
        if self.end_zone is None:
            raise ValueError("Missing end_hub in the graph")
        if self.start_zone == self.end_zone:
            raise ValueError("start_hub and end_hub connot be the same")


if __name__ == "__main__":
    g = Graph()
    # بناء شبكة تجريبية بسيطة
    z_start = Zone("hub", 0, 0, ZoneType.NORMAL)
    z_roof = Zone("roof1", 3, 4, ZoneType.RESTRICTED)
    z_corridor = Zone("corridorA", 4, 3, ZoneType.PRIORITY)
    z_blocked = Zone("obstacleX", 5, 5, ZoneType.BLOCKED)
    z_end = Zone("goal", 10, 10, ZoneType.NORMAL)
    g.add_zone(z_start, is_start=True)
    g.add_zone(z_roof)
    g.add_zone(z_corridor)
    g.add_zone(z_blocked)
    g.add_zone(z_end, is_end=True)
    g.add_connection("hub", "roof1")
    g.add_connection("hub", "corridorA")
    g.add_connection("hub", "obstacleX")
    g.add_connection("roof1", "goal")
    g.add_connection("corridorA", "goal")
    g.validate()
    print("Graph built and validated successfully!")
    print(f"Total zones: {len(g.zones)}")
    assert g.start_zone is not None
    assert g.end_zone is not None
    print(f"Start: {g.start_zone.name}, End: {g.end_zone.name}")
    # فحص الجيران المتاحين لـ hub (المفروض يستثني obstacleX لأنه BLOCKED)
    hub_neighbors = g.get_neighbors(z_start)
    print("\nAccessible neighbors from 'hub':")
    for n_zone, n_conn in hub_neighbors:
        print(f" -> {n_zone.name}"
              f" (type={n_zone.zone_type.value}) via {n_conn}")
