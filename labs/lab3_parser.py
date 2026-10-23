import re
from typing import Dict, Set, Tuple
from lab1_models import Zone, ZoneType
from lab2_graph import Graph


class Parser:
    def __init__(self, filepath: str) -> None:
        self.filepath: str = filepath
        self.graph: Graph = Graph()
        self.nb_drones: int = 0
        self._parsed_connections: Set[Tuple[str, str]] = set()

    def parse(self) -> Tuple[Graph, int]:
        with open(self.filepath, "r", encoding="utf8") as file:
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
            raise ValueError("Invalid map: nb_drones must be greater than 0")

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
            raise ValueError(f"Line {line_num}: Unknown directive '{line}'")

    def _parse_nb_drones(self, line: str, line_num: int) -> None:
        if self.nb_drones > 0:
            raise ValueError(f"Line {line_num}: Duplicate nb_drones definiton")
        parts = line.split(":")
        if len(parts) != 2:
            raise ValueError(f"Line {line_num}: Malformed nb_drones line")
        try:
            self.nb_drones = int(parts[1].strip())
        except ValueError as exc:
            raise ValueError(
                f"Line {line_num}: nb_drones must be an integer"
            ) from exc

    def _parse_metadata(self, meta_text: str) -> Dict[str, str]:
        metadata: Dict[str, str] = {}
        tags = meta_text.strip("[]").split()
        for tag in tags:
            if "=" in tag:
                key, val = tag.split("=", 1)
                metadata[key.strip()] = val.strip()
        return metadata

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
            raise ValueError(f"Line {line_num}: Invalid zone format:'{line}'")

        name, x_str, y_str = parts
        if "-" in name:
            raise ValueError(f"line {line_num}: Zone name cannot contain '-'")

        try:
            x, y = int(x_str), int(y_str)
        except ValueError as exc:
            raise ValueError(
                f"Line {line_num}: Coordinates must be ints"
            ) from exc

        zone_type = ZoneType.NORMAL
        if "zone" in meta_dict:
            try:
                zone_type = ZoneType(meta_dict["zone"])
            except ValueError as exc:
                raise ValueError(
                    f"Line {line_num}: Invalid zone type '{meta_dict['zone']}'"
                ) from exc

        max_drones = int(meta_dict.get("max_drones", 1))
        color = meta_dict.get("color")

        zone = Zone(
            name=name,
            x=x,
            y=y,
            zone_type=zone_type,
            color=color,
            max_drones=max_drones,
        )
        self.graph.add_zone(zone, is_start, is_end)

    def _parse_connection(self, line: str, line_num: int) -> None:
        content = line.split(":", 1)[1].strip()
        meta_dict: Dict[str, str] = {}
        bracket_match = re.search(r"\[(.*?)\]", content)
        if bracket_match:
            meta_dict = self._parse_metadata(bracket_match.group(0))
            content = content[:bracket_match.start()].strip()

        if "-" not in content:
            raise ValueError(f"Line {line_num}: Malformed connection '{line}'")

        parts = content.split("-")
        if len(parts) != 2:
            raise ValueError(f"Line {line_num}: Malformed connection '{line}'")

        name_a, name_b = parts[0].strip(), parts[1].strip()
        edge_key = (min(name_a, name_b), max(name_a, name_b))
        if edge_key in self._parsed_connections:
            raise ValueError(
                f"Line {line_num}: Duplicate connection '{name_a}-{name_b}'"
            )

        self._parsed_connections.add(edge_key)
        max_cap = int(meta_dict.get("max_link_capacity", "1"))
        self.graph.add_connection(name_a, name_b, max_link_capacity=max_cap)


# فحص الـ Parser على خريطة حقيقية من خرائط المشروع!
if __name__ == "__main__":
    test_map = "maps/easy/01_linear_path.txt"
    parser = Parser(test_map)
    graph, drones = parser.parse()
    print(f"Successfully parsed: {test_map}")
    print(f"Total Drones: {drones}")
    print(f"Zones count: {len(graph.zones)}")
    assert graph.start_zone is not None
    assert graph.end_zone is not None
    print(f"Start: {graph.start_zone.name}, End: {graph.end_zone.name}")
    # فحص خريطة ثانية فيها ميتاداتا وسعات وأنواع مناطق
    medium_map = "maps/medium/03_priority_puzzle.txt"
    p2 = Parser(medium_map)
    g2, d2 = p2.parse()
    print(f"\nSuccessfully parsed: {medium_map}")
    print(f"Total Drones: {d2}, Zones count: {len(g2.zones)}")
    for z in g2.zones.values():
        if z.zone_type != ZoneType.NORMAL or z.max_drones > 1:
            print(f" - {z.name}: type={z.zone_type.value}, cap={z.max_drones}")
