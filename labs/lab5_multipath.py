import heapq
from typing import Dict, List, Optional, Set, Tuple

from lab1_models import ZoneType
from lab2_graph import Graph
from lab4_pathfinding import _reconstruct_path, calculate_path_cost


def _find_path_avoiding(
    graph: Graph,
    start_name: str,
    end_name: str,
    blocked: Set[str],
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

        current_zone = graph.zones[current]
        for neighbor, _conn in graph.get_neighbors(current_zone):
            nbr_name = neighbor.name
            conn_key = (
                min(current, nbr_name),
                max(current, nbr_name),
            )
            if conn_key in blocked_conns:
                continue
            if nbr_name in blocked and nbr_name != end_name:
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

    path = _reconstruct_path(came_from, start_name, end_name)
    return path if path else None


def find_disjoint_paths(graph: Graph) -> List[List[str]]:
    """Find multiple capacity-aware paths from start to end."""
    if not graph.start_zone or not graph.end_zone:
        return []

    start = graph.start_zone.name
    end = graph.end_zone.name
    disjoint_paths: List[List[str]] = []

    zone_usage: Dict[str, int] = {}
    conn_usage: Dict[Tuple[str, str], int] = {}
    blocked_zones: Set[str] = set()
    blocked_conns: Set[Tuple[str, str]] = set()

    while True:
        path = _find_path_avoiding(
            graph, start, end, blocked_zones, blocked_conns
        )
        if not path:
            break

        disjoint_paths.append(path)

        for zone_name in path[1:-1]:
            zone = graph.zones[zone_name]
            current_count = zone_usage.get(zone_name, 0) + 1
            zone_usage[zone_name] = current_count
            if current_count >= zone.max_drones:
                blocked_zones.add(zone_name)

        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            conn_key = (min(u, v), max(u, v))
            conn_cap = 1
            for neighbor, conn in graph.get_neighbors(graph.zones[u]):
                if neighbor.name == v:
                    conn_cap = conn.max_link_capacity
                    break

            used_conn = conn_usage.get(conn_key, 0) + 1
            conn_usage[conn_key] = used_conn
            if used_conn >= conn_cap:
                blocked_conns.add(conn_key)

    return disjoint_paths


def dispatch_drones(
    paths: List[List[str]],
    path_costs: List[int],
    nb_drones: int,
) -> Tuple[Dict[int, List[int]], int]:
    if not paths or nb_drones <= 0:
        return {}, 0

    assignments: Dict[int, List[int]] = {
        i: [] for i in range(len(paths))
    }

    for drone_id in range(1, nb_drones + 1):
        best_path_idx = 0
        best_finish_turn = 10**9

        for idx, cost in enumerate(path_costs):
            finish_turn = cost + len(assignments[idx])
            if finish_turn < best_finish_turn:
                best_finish_turn = finish_turn
                best_path_idx = idx

        assignments[best_path_idx].append(drone_id)

    total_turns = 0
    for idx, drones in assignments.items():
        if drones:
            finish = path_costs[idx] + len(drones) - 1
            if finish > total_turns:
                total_turns = finish

    return assignments, total_turns


if __name__ == "__main__":
    import sys
    from lab3_parser import Parser

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

    print(f"=== Testing Multi-Path on: {target_map} ===")
    print(f"Fleet Size: {nb_drones} drones\n")

    paths = find_disjoint_paths(graph)
    print(f"Disjoint Paths Found: {len(paths)}")
    path_costs: List[int] = []
    for i, p in enumerate(paths):
        cost = calculate_path_cost(graph, p)
        path_costs.append(cost)
        print(
            f"  Path {i + 1} (turns={cost}, hops={len(p) - 1}): "
            f"{' -> '.join(p)}"
        )

    assignments, total_turns = dispatch_drones(
        paths, path_costs, nb_drones
    )
    print(f"\nEstimated Simulation Turns: {total_turns}")
    for idx, drones in assignments.items():
        drone_names = [f"D{d}" for d in drones]
        print(
            f"  Path {idx + 1} ({len(drones)} drones): "
            f"{', '.join(drone_names)}"
        )
