from typing import Dict, List, Set, Tuple

from src.graph import Graph
from src.models import DroneState, ZoneType


class Simulation:

    def __init__(
        self,
        graph: Graph,
        paths: List[List[str]],
        assignments: Dict[int, List[int]],
    ) -> None:
        self.graph: Graph = graph
        self.paths: List[List[str]] = paths
        self.drones: List[DroneState] = []
        self.occupancy: Dict[str, int] = {
            name: 0 for name in graph.zones
        }
        self.conn_occupancy: Dict[Tuple[str, str], int] = {}
        self.departure_queues: Dict[int, List[DroneState]] = {}

        for path_idx, drone_ids in assignments.items():
            self.departure_queues[path_idx] = []
            assigned_path = paths[path_idx]
            for d_id in drone_ids:
                drone = DroneState(
                    drone_id=d_id,
                    path=assigned_path,
                    start_turn=0,
                )
                self.drones.append(drone)
                self.departure_queues[path_idx].append(drone)

    def is_finished(self) -> bool:
        return all(drone.has_arrived for drone in self.drones)

    def step(self) -> List[str]:
        moves: List[str] = []
        just_arrived_ids: Set[int] = set()
        # 1. Drones on restricted connections arrive at their destination
        for drone in self.drones:
            if drone.transit_conn is not None:
                target = drone.next_zone
                if target is not None:
                    conn_key = drone.transit_conn
                    self.conn_occupancy[conn_key] -= 1
                    drone.transit_conn = None
                    drone.step_idx += 1
                    just_arrived_ids.add(drone.id)
                    moves.append(f"{drone.name}-{target}")
                    if (
                        self.graph.end_zone
                        and target == self.graph.end_zone.name
                    ):
                        drone.has_arrived = True
                    else:
                        self.occupancy[target] += 1
        # 2. Active drones advancing
        active = [
            d for d in self.drones
            if d.step_idx > 0 and not d.has_arrived
            and d.transit_conn is None and d.id not in just_arrived_ids
        ]
        active.sort(key=lambda d: d.step_idx, reverse=True)
        for drone in active:
            target = drone.next_zone
            if not target:
                continue
            curr = drone.current_zone
            target_zone = self.graph.zones[target]
            conn = self.graph.get_connection(curr, target)
            max_link = conn.max_link_capacity if conn else 1
            conn_key = (min(curr, target), max(curr, target))
            is_goal = (
                self.graph.end_zone is not None
                and target == self.graph.end_zone.name
            )
            if target_zone.zone_type == ZoneType.RESTRICTED:
                if self.conn_occupancy.get(conn_key, 0) < max_link:
                    self.occupancy[curr] -= 1
                    self.conn_occupancy[conn_key] = (
                        self.conn_occupancy.get(conn_key, 0) + 1
                    )
                    drone.transit_conn = conn_key
                    moves.append(f"{drone.name}-{curr}-{target}")
            else:
                target_free = (
                    is_goal or self.occupancy[target] < target_zone.max_drones
                )
                link_free = self.conn_occupancy.get(conn_key, 0) < max_link
                if target_free and link_free:
                    self.occupancy[curr] -= 1
                    drone.step_idx += 1
                    moves.append(f"{drone.name}-{target}")
                    if is_goal:
                        drone.has_arrived = True
                    else:
                        self.occupancy[target] += 1
        # 3. Departure queues at start
        for _path_idx, queue in self.departure_queues.items():
            if not queue:
                continue
            candidate = queue[0]
            target = candidate.next_zone
            if not target:
                continue
            curr = candidate.current_zone
            target_zone = self.graph.zones[target]
            conn = self.graph.get_connection(curr, target)
            max_link = conn.max_link_capacity if conn else 1
            conn_key = (min(curr, target), max(curr, target))
            is_goal = (
                self.graph.end_zone is not None
                and target == self.graph.end_zone.name
            )
            if target_zone.zone_type == ZoneType.RESTRICTED:
                if self.conn_occupancy.get(conn_key, 0) < max_link:
                    queue.pop(0)
                    self.conn_occupancy[conn_key] = (
                        self.conn_occupancy.get(conn_key, 0) + 1
                    )
                    candidate.transit_conn = conn_key
                    moves.append(f"{candidate.name}-{curr}-{target}")
            else:
                target_free = (
                    is_goal or self.occupancy[target] < target_zone.max_drones
                )
                link_free = self.conn_occupancy.get(conn_key, 0) < max_link
                if target_free and link_free:
                    queue.pop(0)
                    candidate.step_idx += 1
                    moves.append(f"{candidate.name}-{target}")
                    if is_goal:
                        candidate.has_arrived = True
                    else:
                        self.occupancy[target] += 1
        moves.sort(key=lambda m: int(m.split("-")[0][1:]))
        return moves

    def run(self, verbose: bool = False) -> int:
        turn = 0
        while not self.is_finished():
            turn += 1
            moves = self.step()
            if moves:
                line = " ".join(moves)
                if verbose:
                    print(f"Turn {turn:02d}: {line}")
                else:
                    print(line)
        return turn
