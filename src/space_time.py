import heapq
from typing import Dict, List, Set, Tuple

from src.graph import Graph
from src.models import ZoneType


class SpaceTimeRouter:

    def __init__(self, graph: Graph) -> None:
        self.graph: Graph = graph
        self.schedules: List[List[Tuple[str, int]]] = []
        self.unique_paths: List[List[str]] = []

    def route_fleet(
        self,
        nb_drones: int,
    ) -> Tuple[List[List[str]], int]:
        if not self.graph.start_zone or not self.graph.end_zone:
            return [], 0

        start_name = self.graph.start_zone.name
        end_name = self.graph.end_zone.name

        # Reservation tables: (element, turn) -> occupancy
        zone_res: Dict[Tuple[str, int], int] = {}
        conn_res: Dict[Tuple[Tuple[str, str], int], int] = {}

        # List of (zone_name, arrival_turn) for each drone
        schedules: List[List[Tuple[str, int]]] = []

        for drone_id in range(1, nb_drones + 1):
            # Min-heap element: (turn, -priority, zone_name, path_history)
            heap: List[
                Tuple[int, int, str, List[Tuple[str, int]]]
            ] = [(0, 0, start_name, [(start_name, 0)])]

            visited: Set[Tuple[str, int]] = set()
            best_schedule: List[Tuple[str, int]] = []

            while heap:
                t, neg_prio, curr, hist = heapq.heappop(heap)

                if curr == end_name:
                    best_schedule = hist
                    break

                state_key = (curr, t)
                if state_key in visited:
                    continue
                visited.add(state_key)

                if t > 120:
                    continue

                # Option 1: Wait in current zone (if space available)
                next_t = t + 1
                curr_cap = (
                    9999
                    if (curr == start_name or curr == end_name)
                    else self.graph.zones[curr].max_drones
                )
                if zone_res.get((curr, next_t), 0) < curr_cap:
                    heapq.heappush(
                        heap,
                        (next_t, neg_prio, curr, hist + [(curr, next_t)]),
                    )

                # Option 2: Move to accessible neighbor
                current_zone = self.graph.zones[curr]
                for neighbor, conn in self.graph.get_neighbors(current_zone):
                    nbr_name = neighbor.name
                    transit_cost = neighbor.movement_cost
                    arrival_t = t + transit_cost

                    # Check link capacity during transit turns
                    conn_key = (
                        min(curr, nbr_name),
                        max(curr, nbr_name),
                    )
                    edge_ok = True
                    for dt in range(1, transit_cost + 1):
                        if (
                            conn_res.get((conn_key, t + dt), 0)
                            >= conn.max_link_capacity
                        ):
                            edge_ok = False
                            break
                    if not edge_ok:
                        continue

                    # Check destination zone capacity upon arrival
                    nbr_cap = (
                        9999
                        if nbr_name == end_name
                        else neighbor.max_drones
                    )
                    if zone_res.get((nbr_name, arrival_t), 0) >= nbr_cap:
                        continue

                    is_prio = (
                        1
                        if neighbor.zone_type == ZoneType.PRIORITY
                        else 0
                    )
                    new_prio = (-neg_prio) + is_prio

                    new_hist = hist + [(nbr_name, arrival_t)]
                    heapq.heappush(
                        heap,
                        (arrival_t, -new_prio, nbr_name, new_hist),
                    )

            if not best_schedule:
                raise RuntimeError(
                    f"SpaceTimeRouter: Unable to route drone D{drone_id}"
                )

            # Book reservations for this drone
            for i in range(len(best_schedule) - 1):
                z_curr, t_curr = best_schedule[i]
                z_next, t_next = best_schedule[i + 1]
                if z_curr != z_next:
                    conn_key = (
                        min(z_curr, z_next),
                        max(z_curr, z_next),
                    )
                    for dt in range(1, t_next - t_curr + 1):
                        conn_res[(conn_key, t_curr + dt)] = (
                            conn_res.get((conn_key, t_curr + dt), 0) + 1
                        )
                if z_next != end_name and z_next != start_name:
                    zone_res[(z_next, t_next)] = (
                        zone_res.get((z_next, t_next), 0) + 1
                    )

            schedules.append(best_schedule)

        # Convert space-time schedules to simulation turn lines
        max_turns = max(sched[-1][1] for sched in schedules)
        turns_moves: List[List[str]] = [[] for _ in range(max_turns + 1)]

        for d_idx, sched in enumerate(schedules):
            d_name = f"D{d_idx + 1}"
            for i in range(len(sched) - 1):
                z_curr, _t_curr = sched[i]
                z_next, t_next = sched[i + 1]
                if z_curr != z_next:
                    turns_moves[t_next].append(f"{d_name}-{z_next}")

        # Filter out turn 0 and sort each turn's moves by drone ID
        clean_turns: List[List[str]] = []
        for t in range(1, max_turns + 1):
            turn_list = turns_moves[t]
            turn_list.sort(key=lambda m: int(m.split("-")[0][1:]))
            clean_turns.append(turn_list)

        self.schedules = schedules
        self.unique_paths = []
        for sched in schedules:
            p: List[str] = []
            for z, _t in sched:
                if not p or p[-1] != z:
                    p.append(z)
            if p not in self.unique_paths:
                self.unique_paths.append(p)
        return clean_turns, max_turns
