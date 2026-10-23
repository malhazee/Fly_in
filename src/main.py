import argparse
import sys

from src.parser import Parser
from src.pathfinder import PathFinder
from src.simulation import Simulation
from src.visualizer import Visualizer
from src.space_time import SpaceTimeRouter


def main() -> int:
    cli_parser = argparse.ArgumentParser(
        description="Fly-in: Autonomous drone fleet routing simulation."
    )
    cli_parser.add_argument(
        "map_file",
        help="Path to the map text file",
    )
    cli_parser.add_argument(
        "-v",
        "--visualize",
        action="store_true",
        help="Enable live ANSI terminal visualizer",
    )
    cli_parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Animation delay per turn in seconds (default: 3.0)",
    )
    cli_parser.add_argument(
        "--space-time",
        "--st",
        action="store_true",
        help="Enable Space-Time multi-agent routing for bottleneck maps",
    )
    args = cli_parser.parse_args()

    try:
        map_parser = Parser(args.map_file)
        graph, nb_drones = map_parser.parse()

        if args.space_time:
            st_router = SpaceTimeRouter(graph)
            turn_moves, _total = st_router.route_fleet(nb_drones)
            if args.visualize:
                dummy_sim = Simulation(graph, [], {})
                vis = Visualizer(graph, dummy_sim)
                vis.animate_space_time(
                    turn_moves,
                    st_router.unique_paths,
                    st_router.schedules,
                    nb_drones,
                    delay=args.delay,
                )
            else:
                for moves in turn_moves:
                    if moves:
                        print(" ".join(moves))
            return 0
        pathfinder = PathFinder(graph)
        paths = pathfinder.find_disjoint_paths()
        if not paths:
            sys.stderr.write("Error: No valid flight paths found.\n")
            return 1

        assignments, _est_turns = pathfinder.dispatch_drones(
            paths, nb_drones
        )

        sim = Simulation(graph, paths, assignments)

        if args.visualize:
            vis = Visualizer(graph, sim)
            vis.animate(delay=args.delay)
        else:
            sim.run(verbose=False)

        return 0

    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
