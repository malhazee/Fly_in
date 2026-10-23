import time
from typing import Dict, List, Tuple

from src.graph import Graph
from src.models import ZoneType
from src.simulation import Simulation


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


class Visualizer:

    def __init__(self, graph: Graph, sim: Simulation) -> None:
        self.graph: Graph = graph
        self.sim: Simulation = sim

    def _render_path_pipeline(self, path: List[str], path_idx: int) -> str:
        nodes_str: List[str] = []
        for zone_name in path:
            zone = self.graph.zones[zone_name]
            is_start = (
                self.graph.start_zone is not None
                and zone_name == self.graph.start_zone.name
            )
            is_end = (
                self.graph.end_zone is not None
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

    def animate(self, delay: float = 3.0) -> int:
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

    def animate_space_time(
        self,
        turns_moves: List[List[str]],
        unique_paths: List[List[str]],
        schedules: List[List[Tuple[str, int]]],
        total_drones: int,
        delay: float = 0.5,
    ) -> int:
        """Animate space-time fleet routing with colored path pipelines."""
        goal_name = (
            self.graph.end_zone.name if self.graph.end_zone else "goal"
        )
        start_name = (
            self.graph.start_zone.name if self.graph.start_zone else "start"
        )
        for turn_idx, moves in enumerate(turns_moves, 1):
            # Compute current location of all drones at this turn
            drone_pos: Dict[int, str] = {}
            for d_idx, sched in enumerate(schedules, 1):
                curr_z = start_name
                for z, arr_t in sched:
                    if arr_t <= turn_idx:
                        curr_z = z
                    else:
                        break
                drone_pos[d_idx] = curr_z
            arrived = sum(1 for z in drone_pos.values() if z == goal_name)
            waiting = sum(1 for z in drone_pos.values() if z == start_name)
            in_air = total_drones - arrived - waiting
            lines: List[str] = []
            lines.append(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}")
            lines.append(
                f"{Colors.BOLD} FLY-IN SPACE-TIME VISUALIZER "
                f"— TURN {turn_idx:02d} / {len(turns_moves):02d}{Colors.RESET}"
            )
            lines.append(
                f" Fleet: {total_drones} | Waiting: {waiting} | "
                f"In Air: {in_air} | Arrived: {arrived}"
            )
            lines.append(f"{Colors.DIM}{'-' * 70}{Colors.RESET}\n")
            lines.append(
                f"{Colors.BOLD}ACTIVE HIGHWAYS (PIPELINES):{Colors.RESET}"
            )
            for p_idx, path in enumerate(unique_paths, 1):
                nodes_repr: List[str] = []
                for zone_name in path:
                    zone = self.graph.zones[zone_name]
                    is_start = zone_name == start_name
                    is_end = zone_name == goal_name
                    # Drones currently at this zone
                    occupants = [
                        f"D{d_id}" for d_id, z in drone_pos.items()
                        if z == zone_name
                    ]
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
                    occ_str = ""
                    if occupants:
                        if len(occupants) > 3:
                            more = len(occupants) - 2
                            d_list = f"{','.join(occupants[:2])},+{more}"
                        else:
                            d_list = ",".join(occupants)
                        occ_str = (
                            f" {Colors.BLUE}{Colors.BOLD}({d_list}){color}"
                        )
                    badge = (
                        f"{color}[{prefix}:{zone_name}{occ_str}]{Colors.RESET}"
                    )
                    nodes_repr.append(badge)
                pipe_str = " ──> ".join(nodes_repr)
                lines.append(
                    f"  {Colors.BOLD}Highway {p_idx}:{Colors.RESET} "
                    f"{pipe_str}\n"
                )
            lines.append(f"{Colors.DIM}{'-' * 70}{Colors.RESET}")
            colored_moves = [
                f"{Colors.BLUE}{m.split('-')[0]}{Colors.RESET}-"
                f"{Colors.CYAN}{m.split('-', 1)[1]}{Colors.RESET}"
                for m in moves
            ]
            lines.append(f" Moves: {' '.join(colored_moves)}")
            lines.append(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")
            print("\n".join(lines))
            time.sleep(delay)
        return len(turns_moves)
