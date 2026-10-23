from collections import deque
import heapq
from typing import Dict, List, Optional, Set, Tuple
from lab2_graph import Graph
from lab1_models import ZoneType


def _reconstruct_path(
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


def bfs_shortest_path(
    graph: Graph,
    start_name: Optional[str] = None,
    end_name: Optional[str] = None,
) -> List[str]:
    actual_start = start_name or (
        graph.start_zone.name if graph.start_zone else None
    )
    actual_end = end_name or (
        graph.end_zone.name if graph.end_zone else None
    )

    if not actual_start or not actual_end:
        return []
    if (
        actual_start not in graph.zones
        or actual_end not in graph.zones
    ):
        return []
    if actual_start == actual_end:
        return [actual_start]

    queue: deque[str] = deque([actual_start])
    visited: Set[str] = {actual_start}
    came_from: Dict[str, Optional[str]] = {actual_start: None}

    while queue:
        current = queue.popleft()
        if current == actual_end:
            break

        current_zone = graph.zones[current]
        for neighbor, _conn in graph.get_neighbors(current_zone):
            nbr_name = neighbor.name
            if nbr_name not in visited:
                visited.add(nbr_name)
                came_from[nbr_name] = current
                queue.append(nbr_name)

    return _reconstruct_path(came_from, actual_start, actual_end)


def dijkstra_shortest_path(
    graph: Graph,
    start_name: Optional[str] = None,
    end_name: Optional[str] = None,
) -> Tuple[List[str], int]:
    actual_start = start_name or (
        graph.start_zone.name if graph.start_zone else None
    )
    actual_end = end_name or (
        graph.end_zone.name if graph.end_zone else None
    )

    if not actual_start or not actual_end:
        return [], 0
    if (
        actual_start not in graph.zones
        or actual_end not in graph.zones
    ):
        return [], 0
    if actual_start == actual_end:
        return [actual_start], 0

    heap: List[Tuple[int, int, str]] = [(0, 0, actual_start)]
    min_cost: Dict[str, int] = {actual_start: 0}
    came_from: Dict[str, Optional[str]] = {actual_start: None}
    prio_count: Dict[str, int] = {actual_start: 0}

    while heap:
        cost, neg_prio, current = heapq.heappop(heap)

        if current == actual_end:
            break

        if cost > min_cost.get(current, 10**9):
            continue

        current_zone = graph.zones[current]
        for neighbor, _conn in graph.get_neighbors(current_zone):
            nbr_name = neighbor.name
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

    path = _reconstruct_path(came_from, actual_start, actual_end)
    if not path:
        return [], 0
    return path, min_cost.get(actual_end, 0)


def calculate_path_cost(graph: Graph, path: List[str]) -> int:
    """Calculate total turn cost of a path."""
    if len(path) <= 1:
        return 0
    total = 0
    for name in path[1:]:
        zone = graph.zones.get(name)
        if zone:
            total += zone.movement_cost
    return total


if __name__ == "__main__":
    import sys
    from lab3_parser import Parser

    target_map = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "maps/easy/01_linear_path.txt"
    )

    parser = Parser(target_map)
    try:
        graph, _nb_drones = parser.parse()
    except Exception as exc:
        print(f"Error parsing map: {exc}")
        sys.exit(1)

    print(f"=== Testing Map: {target_map} ===")
    start_hub = graph.start_zone.name if graph.start_zone else "None"
    end_hub = graph.end_zone.name if graph.end_zone else "None"
    print(f"Start: {start_hub} -> End: {end_hub}\n")

    # 1. BFS Path
    bfs_path = bfs_shortest_path(graph)
    bfs_cost = calculate_path_cost(graph, bfs_path)
    print(f"BFS Path:       {' -> '.join(bfs_path)}")
    print(f"BFS Hops:       {len(bfs_path) - 1}")
    print(f"BFS Turns:      {bfs_cost}\n")

    # 2. Dijkstra Path
    dijk_path, dijk_cost = dijkstra_shortest_path(graph)
    print(f"Dijkstra Path:  {' -> '.join(dijk_path)}")
    print(f"Dijkstra Hops:  {len(dijk_path) - 1}")
    print(f"Dijkstra Turns: {dijk_cost}")
