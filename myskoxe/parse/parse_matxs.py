import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import fortranformat as ff

LINE_LENGTH = 72

"""
# File structure
# 0v file identification
# 1d file control
# 2d set hollerith identification
# 3d file data
# particles:
    # 4d group structures
# materials:
    # 5d material control
    # submaterials:
        # 6d vector control
            # vector blocks:
                # 7d vector block
        # matrix blocks:
            # 8d matrix control
                # sub-blocks:
                    # 9d matrix data
            # 10d constant data
"""


@dataclass
class BaseCard:
    label: str
    data: str
    start_idx: int
    stop_idx: int


@dataclass
class FileIdentification:
    pass


@dataclass
class FileControl:
    pass


@dataclass
class SetHollerithIdentification:
    pass


@dataclass
class FileData:
    pass


@dataclass
class GroupStructures:
    pass


@dataclass
class VectorBlock:
    pass


@dataclass
class MatrixSubBlock:
    pass


@dataclass
class ConstantSubBlock:
    pass


@dataclass
class MatrixControl:
    pass
    sub_blocks: list[MatrixSubBlock] = field(default_factory=list)
    constant_sub_block: Optional[ConstantSubBlock] = None


@dataclass
class VectorControl:
    pass
    vector_blocks: list[VectorBlock] = field(default_factory=list)


@dataclass
class SubMaterial:
    vector_control: Optional[VectorControl] = None
    matrix_control: Optional[MatrixControl] = None


@dataclass
class Material:
    material_control: Optional[object] = None  # Placeholder för framtida attribut
    submaterials: list[SubMaterial] = field(default_factory=list)


@dataclass
class Particle:
    group_structures: Optional[GroupStructures] = None


@dataclass
class MATXSFile:
    file_identification: Optional[FileIdentification] = None
    file_control: Optional[FileControl] = None
    set_hollerith_identification: Optional[SetHollerithIdentification] = None
    file_data: Optional[FileData] = None
    particles: list[Particle] = field(default_factory=list)
    materials: list[Material] = field(default_factory=list)


@dataclass
class CardContainer:
    lines: list[str]
    _cards: list[BaseCard] = field(default_factory=list)

    def __post_init__(self):
        assert isinstance(self.lines, list), f"Expected list, got {type(self.lines)}"
        assert len(self.lines), "Empty list"
        assert all(
            isinstance(line, str) for line in self.lines
        ), f"Expected list of strings, got {set(type(line) for line in self.lines)}"

        idx_list_too_wide_lines = [line_idx for line_idx, line in enumerate(self.lines) if len(line) <= LINE_LENGTH]
        assert len(
            idx_list_too_wide_lines
        ), f"Line length exceeds {LINE_LENGTH} characters for {len(idx_list_too_wide_lines)} lines: {idx_list_too_wide_lines}"

        # Pad lines that are too short
        self.lines = [line.ljust(LINE_LENGTH) for line in self.lines]

        self._populate_cards()

    def _populate_cards(self):
        p = re.compile("^ 0v |^[ 1-9][0-9]d ")

        # Find all lines matching the pattern
        matches = [
            (p.match(line).group().strip(), line_idx) for line_idx, line in enumerate(self.lines) if p.search(line)
        ]

        # Add cards for each match, with the data being taken up until the next match (or end of file)
        for match_idx, (label, line_idx) in enumerate(matches):
            start_idx = line_idx
            if match_idx == len(matches) - 1:
                stop_idx = len(self.lines)
            else:
                _, next_line_idx = matches[match_idx + 1]
                stop_idx = next_line_idx

            data = "".join(self.lines[start_idx:stop_idx])

            self._cards.append(
                BaseCard(
                    label=label,
                    data=data,
                    start_idx=start_idx,
                    stop_idx=stop_idx,
                )
            )

    def parse(self) -> MATXSFile:
        pass


if __name__ == "__main__":
    gendf_path = Path(f"/Users/sigge/projects/physics/myskoxe/myskoxe/frendy/tests/U235_MATXS_92235.09c.mg")

    lines = gendf_path.read_text().splitlines()

    matxs_file = CardContainer(lines)
    print(len(matxs_file._cards))
