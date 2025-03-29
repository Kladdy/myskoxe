import re
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional

import fortranformat as ff

LINE_LENGTH = 72

"""
# MATXS file structure
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

    def __str__(self):
        return f"CardContainer with {len(self._cards)} cards: {[card.label for card in self._cards]}"


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
            ), f"TABLE records should have the same table_rows size, but got {[record.table_rows for record in records if record.type is FFDataRecordType.TABLE]}"

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
    data: dict

    _LABEL = "7d"
    _LEVEL = 7

    @classmethod
    def consume_container(
        cls,
        card_container: CardContainer,
        matxs_file: "MATXSFile",
        material: "Material",
        submaterial: "SubMaterial",
        vector_control: "VectorControl",
    ):
        card = card_container._cards.pop(0)

        assert card.label == cls._LABEL, f"Expected label {cls._LABEL}, got {card.label}"
        assert card.level == cls._LEVEL, f"Expected level {cls._LEVEL}, got {card.level}"

        maxw = matxs_file.file_control.data["maxw"]
        vector_block_idx = len(submaterial.vector_blocks)

        nfg = vector_control.data["nfg"]
        nlg = vector_control.data["nlg"]

        assert len(nfg) == len(nlg), f"Expected nfg and nlg to have the same length, got {len(nfg)} and {len(nlg)}"

        group_count_per_vector = [nlg[i] - nfg[i] + 1 for i in range(len(nfg))]

        # Cumulative sum of group_count_per_vector unless it reaches a value higher than maxw, then start a new cumulative sum
        # until it reaches maxw again, etc.
        group_count_per_vector_cumsum: list[int] = []
        cumulative_sum = 0

        for group_count in group_count_per_vector:
            if cumulative_sum + group_count > maxw:
                group_count_per_vector_cumsum.append(cumulative_sum)
                cumulative_sum = 0
            cumulative_sum += group_count

        if cumulative_sum > 0:
            group_count_per_vector_cumsum.append(cumulative_sum)

        kmax = group_count_per_vector_cumsum[vector_block_idx]

        records = [
            FFDataRecord(key="title", count=1, kind="A4", type=FFDataRecordType.SCALAR),
            FFDataRecord(key=None, count=8, kind="X", type=FFDataRecordType.EMPTY),
            FFDataRecord(key=None, count=1, kind="P", type=FFDataRecordType.DECIMAL_SHIFT),
            FFDataRecord(key="vps", count=kmax, kind="E12.5", type=FFDataRecordType.ARRAY),
        ]

        data = FFDataRecord.read_records(card.data, records)

        return cls(data)


@dataclass
class MatrixSubBlock:
    data: dict

    _LABEL = "9d"
    _LEVEL = 9

    @classmethod
    def consume_container(
        cls,
        card_container: CardContainer,
        matxs_file: "MATXSFile",
        material: "Material",
        submaterial: "SubMaterial",
        matrix_block: "MatrixBlock",
        matrix_control: "MatrixControl",
    ):
        card = card_container._cards.pop(0)

        assert card.label == cls._LABEL, f"Expected label {cls._LABEL}, got {card.label}"
        assert card.level == cls._LEVEL, f"Expected level {cls._LEVEL}, got {card.level}"

        maxw = matxs_file.file_control.data["maxw"]
        sub_block_idx = len(matrix_block.matrix_sub_blocks)

        lord = matrix_control.data["lord"]
        jband = matrix_control.data["jband"]

        # Cumulative sum of jband*lord unless it reaches a value higher than maxw, then start a new cumulative sum
        # until it reaches maxw again, etc.
        jband_cumsum: list[int] = []
        cumulative_sum = 0

        for bandwidth in jband:
            if cumulative_sum + lord * bandwidth > maxw:
                jband_cumsum.append(cumulative_sum)
                cumulative_sum = 0
            cumulative_sum += lord * bandwidth

        if cumulative_sum > 0:
            jband_cumsum.append(cumulative_sum)

        kmax = jband_cumsum[sub_block_idx]

        records = [
            FFDataRecord(key="title", count=1, kind="A4", type=FFDataRecordType.SCALAR),
            FFDataRecord(key=None, count=8, kind="X", type=FFDataRecordType.EMPTY),
            FFDataRecord(key=None, count=1, kind="P", type=FFDataRecordType.DECIMAL_SHIFT),
            FFDataRecord(key="scat", count=kmax, kind="E12.5", type=FFDataRecordType.ARRAY),
        ]

        data = FFDataRecord.read_records(card.data, records)

        return cls(data)


@dataclass
class ConstantSubBlock:
    data: dict

    _LABEL = "10d"
    _LEVEL = 10

    @classmethod
    def consume_container(
        cls,
        card_container: CardContainer,
        matxs_file: "MATXSFile",
        material: "Material",
        submaterial: "SubMaterial",
        matrix_block: "MatrixBlock",
    ):
        card = card_container._cards.pop(0)

        assert card.label == cls._LABEL, f"Expected label {cls._LABEL}, got {card.label}"
        assert card.level == cls._LEVEL, f"Expected level {cls._LEVEL}, got {card.level}"

        submaterial_idx = len(material.submaterials)
        data_type = material.material_control.data["itype"][submaterial_idx]
        joutp = matxs_file.file_data.data["joutp"][data_type - 1]
        noutg = matxs_file.file_data.data["ngrp"][joutp - 1]

        jconst = matrix_block.matrix_control.data["jconst"]

        records = [
            FFDataRecord(key="title", count=1, kind="A4", type=FFDataRecordType.SCALAR),
            FFDataRecord(key=None, count=8, kind="X", type=FFDataRecordType.EMPTY),
            FFDataRecord(key=None, count=1, kind="P", type=FFDataRecordType.DECIMAL_SHIFT),
            FFDataRecord(key="spec", count=noutg, kind="E12.5", type=FFDataRecordType.TABLE),
            FFDataRecord(key="prod", count=jconst, kind="E12.5", type=FFDataRecordType.TABLE),
        ]

        data = FFDataRecord.read_records(card.data, records)

        return cls(data)


@dataclass
class MatrixControl:
    data: dict

    _LABEL = "8d"
    _LEVEL = 8

    @classmethod
    def consume_container(
        cls,
        card_container: CardContainer,
        matxs_file: "MATXSFile",
        material: "Material",
        submaterial: "SubMaterial",
        matrix_block: "MatrixBlock",
    ):
        card = card_container._cards.pop(0)

        assert card.label == cls._LABEL, f"Expected label {cls._LABEL}, got {card.label}"
        assert card.level == cls._LEVEL, f"Expected level {cls._LEVEL}, got {card.level}"

        submaterial_idx = len(material.submaterials)
        data_type = material.material_control.data["itype"][submaterial_idx]
        joutp = matxs_file.file_data.data["joutp"][data_type - 1]
        noutg = matxs_file.file_data.data["ngrp"][joutp - 1]

        records = [
            FFDataRecord(key="title", count=1, kind="A4", type=FFDataRecordType.SCALAR),
            FFDataRecord(key=None, count=4, kind="X", type=FFDataRecordType.EMPTY),
            FFDataRecord(key="hmtx", count=1, kind="A8", type=FFDataRecordType.SCALAR),
            FFDataRecord(key="lord", count=1, kind="I6", type=FFDataRecordType.SCALAR),
            FFDataRecord(key="jconst", count=1, kind="I6", type=FFDataRecordType.SCALAR),
            FFDataRecord(key="jband", count=noutg, kind="I6", type=FFDataRecordType.ARRAY),
            FFDataRecord(key="ijj", count=noutg, kind="I6", type=FFDataRecordType.ARRAY),
        ]

        data = FFDataRecord.read_records(card.data, records)

        matrix_control = cls(data)

        while card_container._cards:
            next_card_level = card_container.get_next_card_level()

            if next_card_level is None or next_card_level <= 8:
                break
            elif next_card_level == 9:
                matrix_block.matrix_sub_blocks.append(
                    MatrixSubBlock.consume_container(
                        card_container, matxs_file, material, submaterial, matrix_block, matrix_control
                    )
                )
            elif next_card_level == 10:
                matrix_block.constant_sub_block = ConstantSubBlock.consume_container(
                    card_container, matxs_file, material, submaterial, matrix_block
                )
            else:
                raise ValueError(f"Unexpected card level {next_card_level}")

        return matrix_control


@dataclass
class MatrixBlock:
    matrix_control: Optional[MatrixControl] = None
    matrix_sub_blocks: list[MatrixSubBlock] = field(default_factory=list)
    constant_sub_block: Optional[ConstantSubBlock] = None

    @classmethod
    def consume_container(
        cls, card_container: CardContainer, matxs_file: "MATXSFile", material: "Material", submaterial: "SubMaterial"
    ):
        matrix_block = cls()

        while card_container._cards:
            next_card_level = card_container.get_next_card_level()

            if next_card_level is None or next_card_level <= 7:
                break
            elif next_card_level == 8 and matrix_block.matrix_control is None:
                matrix_block.matrix_control = MatrixControl.consume_container(
                    card_container, matxs_file, material, submaterial, matrix_block
                )
            elif next_card_level == 8 and matrix_block.matrix_control is not None:
                break
            else:
                raise ValueError(f"Unexpected card level {next_card_level}")

        return submaterial


@dataclass
class VectorControl:
    data: dict

    _LABEL = "6d"
    _LEVEL = 6

    @classmethod
    def consume_container(
        cls, card_container: CardContainer, matxs_file: "MATXSFile", material: "Material", submaterial: "SubMaterial"
    ):
        card = card_container._cards.pop(0)

        assert card.label == cls._LABEL, f"Expected label {cls._LABEL}, got {card.label}"
        assert card.level == cls._LEVEL, f"Expected level {cls._LEVEL}, got {card.level}"

        submaterial_idx = len(material.submaterials)
        n1d = material.material_control.data["n1d"][submaterial_idx]

        records = [
            FFDataRecord(key="title", count=1, kind="A4", type=FFDataRecordType.SCALAR),
            FFDataRecord(key=None, count=4, kind="X", type=FFDataRecordType.EMPTY),
            FFDataRecord(key="hvps", count=n1d, kind="A8", type=FFDataRecordType.ARRAY),
            FFDataRecord(key="nfg", count=n1d, kind="I6", type=FFDataRecordType.ARRAY),
            FFDataRecord(key="nlg", count=n1d, kind="I6", type=FFDataRecordType.ARRAY),
        ]

        data = FFDataRecord.read_records(card.data, records)

        vector_control = cls(data)

        while card_container._cards:
            next_card_level = card_container.get_next_card_level()

            if next_card_level is None or next_card_level <= 5:
                break
            elif next_card_level == 6:
                raise ValueError(f"Unexpected card level {next_card_level}")
            elif next_card_level == 7:
                submaterial.vector_blocks.append(
                    VectorBlock.consume_container(card_container, matxs_file, material, submaterial, vector_control)
                )
            else:
                break

        return vector_control


@dataclass
class SubMaterial:
    vector_control: Optional[VectorControl] = None
    vector_blocks: list[VectorBlock] = field(default_factory=list)
    matrix_blocks: list[MatrixBlock] = field(default_factory=list)

    @classmethod
    def consume_container(cls, card_container: CardContainer, matxs_file: "MATXSFile", material: "Material"):
        submaterial_idx = len(material.submaterials)
        n1d = material.material_control.data["n1d"][submaterial_idx]
        n2d = material.material_control.data["n2d"][submaterial_idx]

        submaterial = cls()

        while card_container._cards:
            next_card_level = card_container.get_next_card_level()

            if next_card_level is None or next_card_level <= 5:
                break
            elif next_card_level == 6 and submaterial.vector_control is None:
                submaterial.vector_control = VectorControl.consume_container(
                    card_container, matxs_file, material, submaterial
                )
            elif next_card_level == 6 and submaterial.vector_control is not None:
                break
            elif next_card_level == 7:
                raise ValueError(f"Unexpected card level {next_card_level}")
            elif next_card_level == 8:
                if len(submaterial.matrix_blocks) == n2d:  # Already found enough matrix blocks for the submaterial
                    break
                submaterial.matrix_blocks.append(
                    MatrixBlock.consume_container(card_container, matxs_file, material, submaterial)
                )
            else:
                raise ValueError(f"Unexpected card level {next_card_level}")

        return submaterial


@dataclass
class Material:
    material_control: Optional[MaterialControl] = None
    submaterials: list[SubMaterial] = field(default_factory=list)

    @classmethod
    def consume_container(cls, card_container: CardContainer, matxs_file: "MATXSFile"):
        next_card_label = card_container.get_next_card_label()
        assert next_card_label == "5d", f"Expected label 5d, got {next_card_label}"

        material = cls()

        material.material_control = MaterialControl.consume_container(card_container, matxs_file)

        while card_container._cards:
            next_card_level = card_container.get_next_card_level()

            if next_card_level is None or next_card_level <= 5:
                break
            elif next_card_level == 6 or next_card_level == 8:  # Vector block or matrix block
                material.submaterials.append(SubMaterial.consume_container(card_container, matxs_file, material))
            else:
                raise ValueError(f"Unexpected card level {next_card_level}")

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

    @classmethod
    def consume_container(cls, card_container: CardContainer):

        matxs_file = MATXSFile()

        while card_container._cards:
            next_card_label = card_container.get_next_card_label()

            if next_card_label is None:
                break

            if next_card_label == "0v":
                matxs_file.file_identification = FileIdentification.consume_container(card_container)
            elif next_card_label == "1d":
                matxs_file.file_control = FileControl.consume_container(card_container)
            elif next_card_label == "2d":
                matxs_file.set_hollerith_identification = SetHollerithIdentification.consume_container(card_container)
            elif next_card_label == "3d":
                matxs_file.file_data = FileData.consume_container(card_container, matxs_file)
            elif next_card_label == "4d":
                matxs_file.particles.append(Particle.consume_container(card_container, matxs_file))
            elif next_card_label == "5d":
                matxs_file.materials.append(Material.consume_container(card_container, matxs_file))
            else:
                raise ValueError(f"The card {next_card_label} should have been consumed further down the line")

        return matxs_file


if __name__ == "__main__":
    gendf_path = Path(
        f"/Users/sigge/projects/physics/myskoxe/myskoxe/frendy/tests/U235_MATXS_92235.09c_modified_row_56.mg"
        # f"/Users/sigge/projects/physics/myskoxe/myskoxe/frendy/tests/U235_MATXS_92235.09c.mg"
    )

    lines = gendf_path.read_text().splitlines()

    matxs_file_data = CardContainer(lines)
    print(matxs_file_data)
    matxs = MATXSFile.consume_container(matxs_file_data)
    print(matxs)
