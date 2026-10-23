from typing import Dict, List

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

        active_drones = [
            d for d in self.drones
            if d.step_idx > 0 and not d.has_arrived
        ]
        active_drones.sort(key=lambda d: d.step_idx, reverse=True)

        for drone in active_drones:
            if drone.wait_turns > 0:
                drone.wait_turns -= 1
                continue

            target = drone.next_zone
            if not target:
                continue

            target_zone = self.graph.zones[target]
            is_goal = (
                self.graph.end_zone is not None
                and target == self.graph.end_zone.name
            )

            if is_goal or self.occupancy[target] < target_zone.max_drones:
                old_zone = drone.current_zone
                self.occupancy[old_zone] -= 1

                drone.step_idx += 1
                moves.append(f"{drone.name}-{target}")

                if is_goal:
                    drone.has_arrived = True
                else:
                    self.occupancy[target] += 1
                    if target_zone.zone_type == ZoneType.RESTRICTED:
                        drone.wait_turns = 1

        for _path_idx, queue in self.departure_queues.items():
            if not queue:
                continue

            candidate = queue[0]
            target = candidate.next_zone
            if not target:
                continue

            target_zone = self.graph.zones[target]
            is_goal = (
                self.graph.end_zone is not None
                and target == self.graph.end_zone.name
            )

            if is_goal or self.occupancy[target] < target_zone.max_drones:
                queue.pop(0)
                candidate.step_idx += 1
                moves.append(f"{candidate.name}-{target}")

                if is_goal:
                    candidate.has_arrived = True
                else:
                    self.occupancy[target] += 1
                    if target_zone.zone_type == ZoneType.RESTRICTED:
                        candidate.wait_turns = 1

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
