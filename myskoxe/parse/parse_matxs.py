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

        # # Pad lines that are too short
        # self.lines = [line.ljust(LINE_LENGTH) for line in self.lines]

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

    def get_next_card_label(self):
        if len(self._cards):
            return self._cards[0].label
        return None

    def get_next_card_level(self):
        if len(self._cards):
            return self._cards[0].level
        return None


class FFDataRecordType(Enum):
    SCALAR = auto()
    ARRAY = auto()
    TABLE = auto()
    EMPTY = auto()
    DECIMAL_SHIFT = auto()


@dataclass
class FFDataRecord:
    key: str
    count: int
    kind: str
    type: FFDataRecordType
    table_rows: Optional[int] = None

    def __post_init__(self):
        if self.type == FFDataRecordType.EMPTY:
            assert self.kind == "X", f"Expected kind 'X' for empty record, got {self.kind}"
        if self.type == FFDataRecordType.SCALAR:
            assert self.count == 1, f"Expected count 1 for scalar record, got {self.count}"
        if self.type == FFDataRecordType.DECIMAL_SHIFT:
            assert self.kind == "P", f"Expected kind 'P' for decimal shift record, got {self.kind}"

        if self.type == FFDataRecordType.TABLE:
            assert self.table_rows is not None, f"Expected table_rows to be set for table record, got {self.table_rows}"
            assert self.count == 1, f"Expected count 1 for table record, got {self.count}"
        else:
            assert (
                self.table_rows is None
            ), f"Expected table_rows to be None for non-table record, got {self.table_rows}"

        # Check that kind does not start with a number
        assert not re.match("\d", self.kind), f"Kind should not start with a number, got {self.kind}"

    @classmethod
    def read_records(cls, data: str, records: list["FFDataRecord"]):
        results = {}

        table_record_indicies = [
            record_idx for record_idx, record in enumerate(records) if record.type is FFDataRecordType.TABLE
        ]

        # Unless there is only one table row, expand the table records to the correct number of records
        if len(table_record_indicies) > 1:
            first_table_record = records[table_record_indicies[0]]

            # If there are any TABLE records, assert that they are all clumped together,
            # one after the other in the list of records
            for i in range(len(table_record_indicies) - 1):
                assert (
                    table_record_indicies[i] + 1 == table_record_indicies[i + 1]
                ), f"TABLE records should be clumped together, but were placed at {table_record_indicies}"

            # Check that all table records have the same table_rows size
            assert all(
                [
                    record.table_rows == first_table_record.table_rows
                    for record in records
                    if record.type is FFDataRecordType.TABLE
                ]
            )

            new_records: list[FFDataRecord] = []
            for record_idx, record in enumerate(records):
                if record_idx == table_record_indicies[0]:
                    repeated_table_indices = table_record_indicies * first_table_record.table_rows
                    for repeated_table_idx in repeated_table_indices:
                        new_records.append(records[repeated_table_idx])
                elif record_idx in table_record_indicies:
                    continue
                else:
                    new_records.append(record)
            records = new_records

        # Read the data
        format_str = ",".join([f"{record.count}{record.kind}" for record in records])
        print(format_str)
        parsed_card = ff.FortranRecordReader(format_str).read(data)

        assert len(parsed_card) == sum(
            [
                record.count
                for record in records
                if record.type not in [FFDataRecordType.EMPTY, FFDataRecordType.DECIMAL_SHIFT]
            ]
        ), f"Expected {sum([record.count for record in records])} values, got {len(parsed_card)}"

        counter = 0
        for record in records:
            if record.type in [FFDataRecordType.EMPTY, FFDataRecordType.DECIMAL_SHIFT]:
                continue

            assert counter + record.count <= len(
                parsed_card
            ), f"Record {record.key} expected {record.count} values, but only {len(parsed_card) - counter} values left"

            if record.type == FFDataRecordType.SCALAR:
                results[record.key] = parsed_card[counter]
            elif record.type == FFDataRecordType.ARRAY:
                results[record.key] = parsed_card[counter : counter + record.count]
            elif record.type == FFDataRecordType.TABLE:
                if record.key not in results:
                    results[record.key] = []
                results[record.key].append(parsed_card[counter])
            else:
                raise ValueError(f"Unsupported record type {record.type}")
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
    def consume_container(cls, card_container: CardContainer):
        card = card_container._cards.pop(0)

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
    def consume_container(cls, card_container: CardContainer):
        card = card_container._cards.pop(0)

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


@dataclass
class SetHollerithIdentification:
    data: dict

    _LABEL = "2d"
    _LEVEL = 2

    @classmethod
    def consume_container(cls, card_container: CardContainer):
        card = card_container._cards.pop(0)

        assert card.label == cls._LABEL, f"Expected label {cls._LABEL}, got {card.label}"
        assert card.level == cls._LEVEL, f"Expected level {cls._LEVEL}, got {card.level}"

        records = [
            FFDataRecord(key="title", count=1, kind="A4", type=FFDataRecordType.SCALAR),
            FFDataRecord(key="hsetid", count=9, kind="A8", type=FFDataRecordType.ARRAY),
        ]

        data = FFDataRecord.read_records(card.data, records)

        return cls(data)


@dataclass
class FileData:
    data: dict

    _LABEL = "3d"
    _LEVEL = 3

    @classmethod
    def consume_container(cls, card_container: CardContainer, matxs_file: "MATXSFile"):
        card = card_container._cards.pop(0)

        assert card.label == cls._LABEL, f"Expected label {cls._LABEL}, got {card.label}"
        assert card.level == cls._LEVEL, f"Expected level {cls._LEVEL}, got {card.level}"

        npart = matxs_file.file_control.data["npart"]
        nmat = matxs_file.file_control.data["nmat"]
        ntype = matxs_file.file_control.data["ntype"]

        records = [
            FFDataRecord(key="title", count=1, kind="A4", type=FFDataRecordType.SCALAR),
            FFDataRecord(key=None, count=4, kind="X", type=FFDataRecordType.EMPTY),
            FFDataRecord(key="hprt", count=npart, kind="A8", type=FFDataRecordType.ARRAY),
            FFDataRecord(key="htype", count=ntype, kind="A8", type=FFDataRecordType.ARRAY),
            FFDataRecord(key="hmatn", count=nmat, kind="A8", type=FFDataRecordType.ARRAY),
            FFDataRecord(key="ngrp", count=npart, kind="I6", type=FFDataRecordType.ARRAY),
            FFDataRecord(key="jinp", count=ntype, kind="I6", type=FFDataRecordType.ARRAY),
            FFDataRecord(key="joutp", count=ntype, kind="I6", type=FFDataRecordType.ARRAY),
            FFDataRecord(key="nsubm", count=nmat, kind="I6", type=FFDataRecordType.ARRAY),
            FFDataRecord(key="locm", count=nmat, kind="I6", type=FFDataRecordType.ARRAY),
        ]

        data = FFDataRecord.read_records(card.data, records)

        return cls(data)


@dataclass
class GroupStructure:
    data: dict

    _LABEL = "4d"
    _LEVEL = 4

    @classmethod
    def consume_container(cls, card_container: CardContainer, matxs_file: "MATXSFile"):
        card = card_container._cards.pop(0)

        assert card.label == cls._LABEL, f"Expected label {cls._LABEL}, got {card.label}"
        assert card.level == cls._LEVEL, f"Expected level {cls._LEVEL}, got {card.level}"

        particle_idx = len(matxs_file.particles)
        ngr = matxs_file.file_data.data["ngrp"][particle_idx]

        records = [
            FFDataRecord(key="title", count=1, kind="A4", type=FFDataRecordType.SCALAR),
            FFDataRecord(key=None, count=8, kind="X", type=FFDataRecordType.EMPTY),
            FFDataRecord(key=None, count=1, kind="P", type=FFDataRecordType.DECIMAL_SHIFT),
            FFDataRecord(key="gpb", count=ngr, kind="E12.5", type=FFDataRecordType.ARRAY),
            FFDataRecord(key="emin", count=1, kind="E12.5", type=FFDataRecordType.SCALAR),
        ]

        data = FFDataRecord.read_records(card.data, records)

        return cls(data)


@dataclass
class MaterialControl:
    data: dict

    _LABEL = "5d"
    _LEVEL = 5

    @classmethod
    def consume_container(cls, card_container: CardContainer, matxs_file: "MATXSFile"):
        card = card_container._cards.pop(0)

        assert card.label == cls._LABEL, f"Expected label {cls._LABEL}, got {card.label}"
        assert card.level == cls._LEVEL, f"Expected level {cls._LEVEL}, got {card.level}"

        material_idx = len(matxs_file.materials)
        nsubm = matxs_file.file_data.data["nsubm"][material_idx]

        records = [
            FFDataRecord(key="title", count=1, kind="A4", type=FFDataRecordType.SCALAR),
            FFDataRecord(key="hmat", count=1, kind="A8", type=FFDataRecordType.SCALAR),
            FFDataRecord(key=None, count=1, kind="P", type=FFDataRecordType.DECIMAL_SHIFT),
            FFDataRecord(key="amass", count=1, kind="E12.5", type=FFDataRecordType.SCALAR),
            FFDataRecord(key="temp", count=1, kind="E12.5", type=FFDataRecordType.TABLE, table_rows=nsubm),
            FFDataRecord(key="sigz", count=1, kind="E12.5", type=FFDataRecordType.TABLE, table_rows=nsubm),
            FFDataRecord(key="itype", count=1, kind="I6", type=FFDataRecordType.TABLE, table_rows=nsubm),
            FFDataRecord(key="n1d", count=1, kind="I6", type=FFDataRecordType.TABLE, table_rows=nsubm),
            FFDataRecord(key="n2d", count=1, kind="I6", type=FFDataRecordType.TABLE, table_rows=nsubm),
            FFDataRecord(key="locs", count=1, kind="I6", type=FFDataRecordType.TABLE, table_rows=nsubm),
        ]

        data = FFDataRecord.read_records(card.data, records)

        return cls(data)


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
    material_control: Optional[object] = None
    submaterials: list[SubMaterial] = field(default_factory=list)

    @classmethod
    def consume_container(cls, card_container: CardContainer, matxs_file: "MATXSFile"):
        next_card_label = card_container.get_next_card_label()
        assert next_card_label == "5d", f"Expected label 5d, got {next_card_label}"

        material = cls()

        material.material_control = MaterialControl.consume_container(card_container, matxs_file)

        # TODO: Fill submaterials

        return material


@dataclass
class Particle:
    group_structure: Optional[GroupStructure] = None

    @classmethod
    def consume_container(cls, card_container: CardContainer, matxs_file: "MATXSFile"):
        next_card_label = card_container.get_next_card_label()
        assert next_card_label == "4d", f"Expected label 4d, got {next_card_label}"

        particle = cls()

        particle.group_structure = GroupStructure.consume_container(card_container, matxs_file)

        return particle


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
            next_card_label = card_container.get_next_card_label()

            if next_card_label == "0v":
                self.file_identification = FileIdentification.consume_container(card_container)
            elif next_card_label == "1d":
                self.file_control = FileControl.consume_container(card_container)
            elif next_card_label == "2d":
                self.set_hollerith_identification = SetHollerithIdentification.consume_container(card_container)
            elif next_card_label == "3d":
                self.file_data = FileData.consume_container(card_container, self)
            elif next_card_label == "4d":
                self.particles.append(Particle.consume_container(card_container, self))
            elif next_card_label == "5d":
                self.materials.append(Material.consume_container(card_container, self))
            elif next_card_label is None:
                print(f"End of file reached")
                break
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
