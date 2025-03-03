import re
from dataclasses import dataclass, field
from enum import Enum, auto
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
    level: int
    data: str
    start_idx: int
    stop_idx: int


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

            level = int(re.match("\d", label).group())

            self._cards.append(
                BaseCard(
                    label=label,
                    level=level,
                    data=data,
                    start_idx=start_idx,
                    stop_idx=stop_idx,
                )
            )


class FFDataRecordType(Enum):
    SCALAR = auto()
    ARRAY = auto()
    EMPTY = auto()


@dataclass
class FFDataRecord:
    key: str
    count: int
    kind: str
    type: FFDataRecordType

    def __post_init__(self):
        if self.type == FFDataRecordType.EMPTY:
            assert self.kind == "X", f"Expected kind 'X' for empty record, got {self.kind}"
        if self.type == FFDataRecordType.SCALAR:
            assert self.count == 1, f"Expected count 1 for scalar record, got {self.count}"

        # Check that kind does not start with a number
        assert not re.match("\d", self.kind), f"Kind should not start with a number, got {self.kind}"

    @classmethod
    def read_records(cls, data: str, records: list["FFDataRecord"]):
        results = {}

        # Read the data
        format_str = ",".join([f"{record.count}{record.kind}" for record in records])
        parsed_card = ff.FortranRecordReader(format_str).read(data)

        assert len(parsed_card) == sum(
            [record.count for record in records if record.type != FFDataRecordType.EMPTY]
        ), f"Expected {sum([record.count for record in records])} values, got {len(parsed_card)}"

        counter = 0
        for record in records:
            if record.type == FFDataRecordType.EMPTY:
                continue

            assert counter + record.count <= len(
                parsed_card
            ), f"Record {record.key} expected {record.count} values, but only {len(parsed_card) - counter} values left"

            if record.type == FFDataRecordType.SCALAR:
                results[record.key] = parsed_card[counter]
            else:
                results[record.key] = parsed_card[counter : counter + record.count]
            counter += record.count

        assert counter == len(
            parsed_card
        ), f"Expected {len(parsed_card)} values to be parsed, but only parsed {counter}"

        return results


@dataclass
class FileIdentification:
    data: dict

    _LABEL = "0v"
    _LEVEL = 0

    @classmethod
    def consume_card(cls, card: BaseCard):
        assert card.label == cls._LABEL, f"Expected label {cls._LABEL}, got {card.label}"
        assert card.level == cls._LEVEL, f"Expected level {cls._LEVEL}, got {card.level}"

        # ff_format = ff.FortranRecordReader("(A4,A8,A1,2A8,A1,I6)")
        records = [
            FFDataRecord(key="title", count=1, kind="A4", type=FFDataRecordType.SCALAR),
            FFDataRecord(key="hname", count=1, kind="A8", type=FFDataRecordType.SCALAR),
            FFDataRecord(key="sep1", count=1, kind="X", type=FFDataRecordType.EMPTY),
            FFDataRecord(key="huse", count=2, kind="A8", type=FFDataRecordType.ARRAY),
            FFDataRecord(key="sep2", count=1, kind="X", type=FFDataRecordType.EMPTY),
            FFDataRecord(key="ivers", count=1, kind="I6", type=FFDataRecordType.SCALAR),
        ]

        data = FFDataRecord.read_records(card.data, records)

        return cls(data)


@dataclass
class FileControl:
    data: dict

    _LABEL = "1d"
    _LEVEL = 1

    @classmethod
    def consume_card(cls, card: BaseCard):
        assert card.label == cls._LABEL, f"Expected label {cls._LABEL}, got {card.label}"
        assert card.level == cls._LEVEL, f"Expected level {cls._LEVEL}, got {card.level}"

        records = [
            FFDataRecord(key="title", count=1, kind="A6", type=FFDataRecordType.SCALAR),
            FFDataRecord(key="npart", count=1, kind="I6", type=FFDataRecordType.SCALAR),
            FFDataRecord(key="ntype", count=1, kind="I6", type=FFDataRecordType.SCALAR),
            FFDataRecord(key="nholl", count=1, kind="I6", type=FFDataRecordType.SCALAR),
            FFDataRecord(key="nmat", count=1, kind="I6", type=FFDataRecordType.SCALAR),
            FFDataRecord(key="maxw", count=1, kind="I6", type=FFDataRecordType.SCALAR),
            FFDataRecord(key="length", count=1, kind="I6", type=FFDataRecordType.SCALAR),
        ]

        data = FFDataRecord.read_records(card.data, records)

        return cls(data)


# !cr set hollerith identification
# !c
# !cl (hsetid(i),i=1,nholl)
# !c
# !cw nholl*mult
# !c
# !cb format(4h 2d /(9a8))
# !c
# !cd hsetid hollerith identification of set (a8)
# !cd (to be edited out 72 characters per line)


@dataclass
class SetHollerithIdentification:
    data: dict

    _LABEL = "2d"
    _LEVEL = 2

    @classmethod
    def consume_card(cls, card: BaseCard):
        assert card.label == cls._LABEL, f"Expected label {cls._LABEL}, got {card.label}"
        assert card.level == cls._LEVEL, f"Expected level {cls._LEVEL}, got {card.level}"

        records = [
            FFDataRecord(key="title", count=1, kind="A4", type=FFDataRecordType.SCALAR),
            FFDataRecord(key=None, count=68, kind="X", type=FFDataRecordType.EMPTY),
            FFDataRecord(key="hsetid", count=7, kind="A8", type=FFDataRecordType.ARRAY),
        ]

        data = FFDataRecord.read_records(card.data, records)

        return cls(data)


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

    def consume_container(self, card_container: CardContainer):
        while card_container._cards:
            card = card_container._cards.pop(0)

            if card.label == "0v":
                self.file_identification = FileIdentification.consume_card(card)
            elif card.label == "1d":
                self.file_control = FileControl.consume_card(card)
            elif card.label == "2d":
                self.set_hollerith_identification = SetHollerithIdentification.consume_card(card)
            # elif card.label == "3d":
            #     self.file_data = FileData.consume_card(card)
            else:
                break
                raise ValueError(f"The card {card} should have been consumed further down the line")


if __name__ == "__main__":
    gendf_path = Path(f"/Users/sigge/projects/physics/myskoxe/myskoxe/frendy/tests/U235_MATXS_92235.09c.mg")

    lines = gendf_path.read_text().splitlines()

    matxs_file = CardContainer(lines)
    print(len(matxs_file._cards))

    matxs = MATXSFile()
    matxs.consume_container(matxs_file)
    print(matxs)
