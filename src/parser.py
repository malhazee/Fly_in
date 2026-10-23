import re
from typing import Dict, Set, Tuple

from src.graph import Graph
from src.models import Zone, ZoneType


class Parser:

    def __init__(self, filepath: str) -> None:
        self.filepath: str = filepath
        self.graph: Graph = Graph()
        self.nb_drones: int = 0
        self._parsed_connections: Set[Tuple[str, str]] = set()

    def parse(self) -> Tuple[Graph, int]:
        with open(self.filepath, "r", encoding="utf-8") as file:
            lines = file.readlines()

        line_number = 0
        for raw_line in lines:
            line_number += 1
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            self._parse_line(line, line_number)

        self.graph.validate()
        if self.nb_drones <= 0:
            raise ValueError("Map error: nb_drones must be greater than 0")

        return self.graph, self.nb_drones

    def _parse_line(self, line: str, line_num: int) -> None:
        if line.startswith("nb_drones:"):
            self._parse_nb_drones(line, line_num)
        elif line.startswith("start_hub:"):
            self._parse_zone(line, line_num, is_start=True)
        elif line.startswith("end_hub:"):
            self._parse_zone(line, line_num, is_end=True)
        elif line.startswith("hub:"):
            self._parse_zone(line, line_num)
        elif line.startswith("connection:"):
            self._parse_connection(line, line_num)
        else:
            raise ValueError(
                f"Line {line_num}: Unrecognized directive '{line}'"
            )

    def _parse_nb_drones(self, line: str, line_num: int) -> None:
        if self.nb_drones > 0:
            raise ValueError(f"Line {line_num}: nb_drones already defined")

        parts = line.split(":", 1)
        raw_val = parts[1].strip()
        try:
            val = int(raw_val)
            if val <= 0:
                raise ValueError
            self.nb_drones = val
        except ValueError as exc:
            raise ValueError(
                f"Line {line_num}: nb_drones must be a positive integer"
            ) from exc

    def _parse_metadata(self, raw_meta: str) -> Dict[str, str]:
        inside = raw_meta.strip()[1:-1].strip()
        meta: Dict[str, str] = {}
        if not inside:
            return meta

        for item in inside.split():
            if "=" not in item:
                continue
            k, v = item.split("=", 1)
            meta[k.strip()] = v.strip()
        return meta

    def _parse_zone(
        self,
        line: str,
        line_num: int,
        is_start: bool = False,
        is_end: bool = False,
    ) -> None:
        content = line.split(":", 1)[1].strip()
        meta_dict: Dict[str, str] = {}

        bracket_match = re.search(r"\[(.*?)\]", content)
        if bracket_match:
            meta_dict = self._parse_metadata(bracket_match.group(0))
            content = content[:bracket_match.start()].strip()

        parts = content.split()
        if len(parts) != 3:
            raise ValueError(
                f"Line {line_num}: Invalid zone format: '{line}'"
            )

        name, x_str, y_str = parts
        if "-" in name:
            raise ValueError(
                f"Line {line_num}: Zone name '{name}' cannot contain '-'"
            )

        try:
            x, y = int(x_str), int(y_str)
        except ValueError as exc:
            raise ValueError(
                f"Line {line_num}: Coordinates must be integers"
            ) from exc

        zone_type = ZoneType.NORMAL
        if "zone" in meta_dict:
            try:
                zone_type = ZoneType(meta_dict["zone"])
            except ValueError as exc:
                raise ValueError(
                    f"Line {line_num}: Invalid zone type "
                    f"'{meta_dict['zone']}'"
                ) from exc

        max_drones = 1
        if "max_drones" in meta_dict:
            try:
                max_drones = int(meta_dict["max_drones"])
                if max_drones < 1:
                    raise ValueError
            except ValueError as exc:
                raise ValueError(
                    f"Line {line_num}: max_drones must be a positive int"
                ) from exc

        color = meta_dict.get("color")
        zone = Zone(
            name=name,
            x=x,
            y=y,
            zone_type=zone_type,
            color=color,
            max_drones=max_drones,
        )
        self.graph.add_zone(zone, is_start=is_start, is_end=is_end)

    def _parse_connection(self, line: str, line_num: int) -> None:
        content = line.split(":", 1)[1].strip()
        meta_dict: Dict[str, str] = {}

        bracket_match = re.search(r"\[(.*?)\]", content)
        if bracket_match:
            meta_dict = self._parse_metadata(bracket_match.group(0))
            content = content[:bracket_match.start()].strip()

        if "-" not in content:
            raise ValueError(
                f"Line {line_num}: Connection must be 'zoneA-zoneB'"
            )

        parts = content.split("-", 1)
        name_a, name_b = parts[0].strip(), parts[1].strip()

        conn_key: Tuple[str, str] = (
            min(name_a, name_b),
            max(name_a, name_b),
        )
        if conn_key in self._parsed_connections:
            raise ValueError(
                f"Line {line_num}: Duplicate connection '{name_a}-{name_b}'"
            )
        self._parsed_connections.add(conn_key)

        max_cap = 1
        if "max_link_capacity" in meta_dict:
            try:
                max_cap = int(meta_dict["max_link_capacity"])
                if max_cap < 1:
                    raise ValueError
            except ValueError as exc:
                raise ValueError(
                    f"Line {line_num}: max_link_capacity must be positive"
                ) from exc

        self.graph.add_connection(
            name_a, name_b, max_link_capacity=max_cap
        )
