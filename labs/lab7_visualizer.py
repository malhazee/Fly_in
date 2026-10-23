import time
from typing import Dict, List

from lab1_models import ZoneType
from lab2_graph import Graph
from lab6_simulation import Simulation


class Colors:

    RESET: str = "\033[0m"
    BOLD: str = "\033[1m"
    DIM: str = "\033[2m"

    RED: str = "\033[31m"
    GREEN: str = "\033[32m"
    YELLOW: str = "\033[33m"
    BLUE: str = "\033[34m"
    MAGENTA: str = "\033[35m"
    CYAN: str = "\033[36m"
    WHITE: str = "\033[37m"

    BG_BLUE: str = "\033[44m"
    BG_GREEN: str = "\033[42m"
    BG_RED: str = "\033[41m"


class Visualizer:

    def __init__(self, graph: Graph, sim: Simulation) -> None:
        self.graph: Graph = graph
        self.sim: Simulation = sim

        xs = [z.x for z in graph.zones.values()]
        ys = [z.y for z in graph.zones.values()]
        self.min_x: int = min(xs) if xs else 0
        self.max_x: int = max(xs) if xs else 0
        self.min_y: int = min(ys) if ys else 0
        self.max_y: int = max(ys) if ys else 0

    def _get_drones_by_zone(self) -> Dict[str, List[str]]:
        mapping: Dict[str, List[str]] = {
            name: [] for name in self.graph.zones
        }
        for drone in self.sim.drones:
            if drone.has_arrived:
                if self.graph.end_zone:
                    mapping[self.graph.end_zone.name].append(drone.name)
            elif drone.step_idx == 0:
                if self.graph.start_zone:
                    mapping[self.graph.start_zone.name].append(drone.name)
            else:
                mapping[drone.current_zone].append(drone.name)
        return mapping

    def _get_zone_badge(self, zone_name: str) -> str:
        zone = self.graph.zones[zone_name]
        is_start = (
            self.graph.start_zone
            and zone_name == self.graph.start_zone.name
        )
        is_end = (
            self.graph.end_zone
            and zone_name == self.graph.end_zone.name
        )

        if is_start:
            return f"{Colors.GREEN}[START: {zone_name}]{Colors.RESET}"
        if is_end:
            return f"{Colors.RED}[GOAL: {zone_name}]{Colors.RESET}"
        if zone.zone_type == ZoneType.PRIORITY:
            return f"{Colors.YELLOW}[PRIO: {zone_name}]{Colors.RESET}"
        if zone.zone_type == ZoneType.RESTRICTED:
            return f"{Colors.MAGENTA}[REST: {zone_name}]{Colors.RESET}"
        return f"{Colors.CYAN}[HUB: {zone_name}]{Colors.RESET}"

    def _render_path_pipeline(self, path: List[str], path_idx: int) -> str:
        nodes_str: List[str] = []
        for zone_name in path:
            zone = self.graph.zones[zone_name]
            is_start = (
                self.graph.start_zone
                and zone_name == self.graph.start_zone.name
            )
            is_end = (
                self.graph.end_zone
                and zone_name == self.graph.end_zone.name
            )
            occupants: List[str] = []
            for drone in self.sim.drones:
                if drone.path == path:
                    if is_start and drone.step_idx == 0:
                        occupants.append(drone.name)
                    elif is_end and drone.has_arrived:
                        occupants.append(drone.name)
                    elif (
                        not is_start
                        and not drone.has_arrived
                        and drone.current_zone == zone_name
                    ):
                        occupants.append(drone.name)
            color = Colors.CYAN
            prefix = "HUB"
            if is_start:
                color = Colors.GREEN
                prefix = "START"
            elif is_end:
                color = Colors.RED
                prefix = "GOAL"
            elif zone.zone_type == ZoneType.PRIORITY:
                color = Colors.YELLOW
                prefix = "PRIO"
            elif zone.zone_type == ZoneType.RESTRICTED:
                color = Colors.MAGENTA
                prefix = "REST"
            occ_text = ""
            if occupants:
                d_str = ",".join(occupants)
                occ_text = f" {Colors.BLUE}{Colors.BOLD}({d_str}){color}"
            node_repr = (
                f"{color}[{prefix}:{zone_name}{occ_text}]{Colors.RESET}"
            )
            nodes_str.append(node_repr)
        return " ──> ".join(nodes_str)
    def render_dashboard(
        self,
        turn: int,
        last_moves: List[str],
    ) -> str:
        total = len(self.sim.drones)
        arrived = sum(1 for d in self.sim.drones if d.has_arrived)
        waiting = sum(
            1 for d in self.sim.drones
            if d.step_idx == 0 and not d.has_arrived
        )
        in_air = total - arrived - waiting
        lines: List[str] = []
        lines.append(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}")
        lines.append(
            f"{Colors.BOLD} FLY-IN SIMULATION "
            f"— TURN {turn:02d}{Colors.RESET}"
        )
        lines.append(
            f" Fleet: {total} | Waiting: {waiting} | "
            f"In Air: {in_air} | Arrived: {arrived}"
        )
        lines.append(f"{Colors.DIM}{'-' * 70}{Colors.RESET}\n")
        lines.append(f"{Colors.BOLD}ACTIVE PATH PIPELINES:{Colors.RESET}")
        for idx, path in enumerate(self.sim.paths):
            pipeline = self._render_path_pipeline(path, idx)
            lines.append(
                f"  {Colors.BOLD}Path {idx + 1}:{Colors.RESET} {pipeline}\n"
            )
        lines.append(f"{Colors.DIM}{'-' * 70}{Colors.RESET}")
        moves_str = (
            " ".join(last_moves)
            if last_moves
            else f"{Colors.DIM}(none){Colors.RESET}"
        )
        lines.append(f" Moves this turn: {moves_str}")
        lines.append(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")
        return "\n".join(lines)
    def animate(self, delay: float = 1.0) -> int:
        """Animate simulation turn-by-turn with clear screen frames."""
        turn = 0
        print("\033[2J\033[H", end="")
        print(self.render_dashboard(turn=0, last_moves=[]))
        time.sleep(delay)
        while not self.sim.is_finished():
            turn += 1
            moves = self.sim.step()
            print("\033[2J\033[H", end="")
            print(self.render_dashboard(turn=turn, last_moves=moves))
            time.sleep(delay)
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

    paths = find_disjoint_paths(graph)
    path_costs = [calculate_path_cost(graph, p) for p in paths]
    assignments, _est_turns = dispatch_drones(
        paths, path_costs, nb_drones
    )

    sim = Simulation(graph, paths, assignments)
    visualizer = Visualizer(graph, sim)

    total_turns = visualizer.animate(delay=3.0)
    print(
        f"{Colors.GREEN}{Colors.BOLD}"
        f"Mission accomplished in {total_turns} turns!{Colors.RESET}"
    )
