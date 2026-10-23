from typing import Dict, List, Optional

from lab1_models import ZoneType
from lab2_graph import Graph


class DroneState:

    def __init__(
        self,
        drone_id: int,
        path: List[str],
        start_turn: int,
    ) -> None:
        self.id: int = drone_id
        self.path: List[str] = path
        self.step_idx: int = 0
        self.wait_turns: int = 0
        self.start_turn: int = start_turn
        self.has_arrived: bool = False

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
                self.graph.end_zone
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

        for path_idx, queue in self.departure_queues.items():
            if not queue:
                continue

            candidate = queue[0]
            target = candidate.next_zone
            if not target:
                continue

            target_zone = self.graph.zones[target]
            is_goal = (
                self.graph.end_zone
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

    def run(self, verbose: bool = True) -> int:
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


if __name__ == "__main__":
    import sys
    from lab3_parser import Parser
    from lab4_pathfinding import calculate_path_cost
    from lab5_multipath import dispatch_drones, find_disjoint_paths

    target_map = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "maps/easy/02_simple_fork.txt"
    )

    parser = Parser(target_map)
    try:
        graph, nb_drones = parser.parse()
    except Exception as exc:
        print(f"Error parsing map: {exc}")
        sys.exit(1)

    print(f"=== Running Simulation on: {target_map} ===")
    print(f"Fleet Size: {nb_drones} drones\n")

    paths = find_disjoint_paths(graph)
    path_costs = [calculate_path_cost(graph, p) for p in paths]
    assignments, est_turns = dispatch_drones(
        paths, path_costs, nb_drones
    )

    print(f"Paths found: {len(paths)}")
    for idx, p in enumerate(paths):
        d_count = len(assignments.get(idx, []))
        print(
            f"  Path {idx + 1} ({d_count} drones, cost={path_costs[idx]}): "
            f"{' -> '.join(p)}"
        )
    print(f"\nEstimated turns: {est_turns}\n")
    print("--- Simulation Output ---")

    sim = Simulation(graph, paths, assignments)
    actual_turns = sim.run(verbose=True)

    print("-------------------------")
    print(f"Simulation completed in {actual_turns} turns!")
    if actual_turns == est_turns:
        print("SUCCESS: Actual turns match estimated turns perfectly!")
