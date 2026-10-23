import heapq
from typing import Dict, List, Optional, Set, Tuple

from src.graph import Graph
from src.models import ZoneType


class PathFinder:

    def __init__(self, graph: Graph) -> None:
        self.graph: Graph = graph

    def calculate_path_cost(self, path: List[str]) -> int:
        if len(path) <= 1:
            return 0
        total = 0
        for name in path[1:]:
            zone = self.graph.zones.get(name)
            if zone:
                total += zone.movement_cost
        return total

    def _reconstruct_path(
        self,
        came_from: Dict[str, Optional[str]],
        start: str,
        end: str,
    ) -> List[str]:
        if end not in came_from:
            return []

        path: List[str] = []
        current: Optional[str] = end
        while current is not None:
            path.append(current)
            current = came_from.get(current)

        path.reverse()
        if path and path[0] == start:
            return path
        return []

    def _find_path_avoiding(
        self,
        start_name: str,
        end_name: str,
        blocked_zones: Set[str],
        blocked_conns: Set[Tuple[str, str]],
    ) -> Optional[List[str]]:
        heap: List[Tuple[int, int, str]] = [(0, 0, start_name)]
        min_cost: Dict[str, int] = {start_name: 0}
        came_from: Dict[str, Optional[str]] = {start_name: None}
        prio_count: Dict[str, int] = {start_name: 0}

        while heap:
            cost, neg_prio, current = heapq.heappop(heap)

            if current == end_name:
                break

            if cost > min_cost.get(current, 10**9):
                continue

            current_zone = self.graph.zones[current]
            for neighbor, _conn in self.graph.get_neighbors(current_zone):
                nbr_name = neighbor.name

                conn_key = (
                    min(current, nbr_name),
                    max(current, nbr_name),
                )
                if conn_key in blocked_conns:
                    continue

                if nbr_name in blocked_zones and nbr_name != end_name:
                    continue

                step_cost = neighbor.movement_cost
                new_cost = cost + step_cost
                is_prio = 1 if neighbor.zone_type == ZoneType.PRIORITY else 0
                new_prio = (-neg_prio) + is_prio

                better = False
                if nbr_name not in min_cost:
                    better = True
                elif new_cost < min_cost[nbr_name]:
                    better = True
                elif (
                    new_cost == min_cost[nbr_name]
                    and new_prio > prio_count[nbr_name]
                ):
                    better = True

                if better:
                    min_cost[nbr_name] = new_cost
                    prio_count[nbr_name] = new_prio
                    came_from[nbr_name] = current
                    heapq.heappush(heap, (new_cost, -new_prio, nbr_name))

        path = self._reconstruct_path(came_from, start_name, end_name)
        return path if path else None

    def find_disjoint_paths(self) -> List[List[str]]:
        if not self.graph.start_zone or not self.graph.end_zone:
            return []

        start = self.graph.start_zone.name
        end = self.graph.end_zone.name
        disjoint_paths: List[List[str]] = []

        zone_usage: Dict[str, int] = {}
        conn_usage: Dict[Tuple[str, str], int] = {}
        blocked_zones: Set[str] = set()
        blocked_conns: Set[Tuple[str, str]] = set()

        while True:
            path = self._find_path_avoiding(
                start, end, blocked_zones, blocked_conns
            )
            if not path:
                break

            disjoint_paths.append(path)

            for zone_name in path[1:-1]:
                zone = self.graph.zones[zone_name]
                curr_count = zone_usage.get(zone_name, 0) + 1
                zone_usage[zone_name] = curr_count
                if curr_count >= zone.max_drones:
                    blocked_zones.add(zone_name)

            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                conn_key = (min(u, v), max(u, v))
                conn = self.graph.get_connection(u, v)
                conn_cap = conn.max_link_capacity if conn else 1

                curr_conn = conn_usage.get(conn_key, 0) + 1
                conn_usage[conn_key] = curr_conn
                if curr_conn >= conn_cap:
                    blocked_conns.add(conn_key)

        return disjoint_paths

    def dispatch_drones(
        self,
        paths: List[List[str]],
        nb_drones: int,
    ) -> Tuple[Dict[int, List[int]], int]:
        if not paths or nb_drones <= 0:
            return {}, 0

        path_costs = [self.calculate_path_cost(p) for p in paths]
        assignments: Dict[int, List[int]] = {
            i: [] for i in range(len(paths))
        }

        for drone_id in range(1, nb_drones + 1):
            best_idx = 0
            best_finish = 10**9

            for idx, cost in enumerate(path_costs):
                finish = cost + len(assignments[idx])
                if finish < best_finish:
                    best_finish = finish
                    best_idx = idx

            assignments[best_idx].append(drone_id)

        total_turns = 0
        for idx, drones in assignments.items():
            if drones:
                finish = path_costs[idx] + len(drones) - 1
                if finish > total_turns:
                    total_turns = finish

        return assignments, total_turns
