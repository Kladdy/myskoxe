import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto

import fortranformat as ff

MAX_LINE_LENGTH = 72


class RecordType(Enum):
    SCALAR = auto()
    ARRAY = auto()
    NEWLINE = auto()
    EMPTY = auto()


@dataclass
class FortranFormatCardRecord:
    key: str
    format: str
    type: RecordType
    get_n_values_from: tuple[str, str] = None

    def __post_init__(self):
        if self.get_n_values_from is not None:
            assert type(self.get_n_values_from) == tuple, "get_n_values_from must be a tuple"
            assert len(self.get_n_values_from) == 2, "get_n_values_from must have length 2"

    def get_n_values(self):
        match self.type:
            case RecordType.SCALAR:
                return 1
            case RecordType.ARRAY | RecordType.EMPTY:
                integer_match = re.match(r"^\d+", self.format)
                if not integer_match:
                    raise ValueError(f"Format {self.format} for record {self.key} does not start with an integer")
                n_values = int(integer_match.group()) or 1
                return n_values
            case RecordType.NEWLINE:
                return 0
            case _:
                raise ValueError(f"Unknown record type {self.type}")

    def get_chars_per_value(self):
        match self.type:
            case RecordType.SCALAR | RecordType.ARRAY:
                integer_match = re.search(r"\d+$", self.format)
                if not integer_match:
                    raise ValueError(f"Format {self.format} for record {self.key} does not end with an integer")
                return int(integer_match.group())
            case RecordType.EMPTY:
                integer_match = re.search(r"\d+$", self.format)
                if not integer_match:
                    return 1
                return int(integer_match.group())
            case RecordType.NEWLINE:
                return 0
            case _:
                raise ValueError(f"Unknown record type {self.type}")


@dataclass
class FortranFormatBaseCard(ABC):
    records: list[FortranFormatCardRecord]
    expected_records: dict[str, any] = None
    _format: str = None
    _reader: ff.FortranRecordReader = None

    def __post_init__(self):
        if self._format is not None:
            raise ValueError("_format is not allowed to be set manually")
        if self._reader is not None:
            raise ValueError("_reader is not allowed to be set manually")

        for record in self.records:
            if record.type == RecordType.NEWLINE:
                if record.format != "/":
                    raise ValueError(f"Newline record {record.key} must have format '/', but was {record.format}")

            if record.get_n_values_from and re.match(r"^\d+", record.format):
                raise ValueError(
                    f"Record {record.key} has get_n_values_from set, but format {record.format} starts with an integer"
                )

        self.set_reader()

    def set_reader(self):
        for record in self.records:
            if record.get_n_values_from is not None and record.type != RecordType.ARRAY:
                raise ValueError(
                    f"Record {record.key} is not of type {RecordType.ARRAY}, but has get_n_values_from set"
                )

        self._format = f"{','.join([record.format for record in self.records])}"
        self._reader = ff.FortranRecordReader(self._format)

    @abstractmethod
    def parse_card(self, card_data: str):
        pass


@dataclass
class FortranFormatBasicCard(FortranFormatBaseCard):
    pass

    def parse_card(self, card_data: str):
        result = {}

        parsed_card = self._reader.read(card_data)

        counter = 0
        for record in self.records:
            if record.type == RecordType.NEWLINE or record.type == RecordType.EMPTY:
                continue

            n_values = record.get_n_values()

            assert counter + n_values <= len(
                parsed_card
            ), f"Record {record.key} expected {n_values} values, but only {len(parsed_card) - counter} values left"

            if n_values == 1 and record.type == RecordType.SCALAR:
                result[record.key] = parsed_card[counter]
            else:
                result[record.key] = parsed_card[counter : counter + n_values]
            counter += n_values

        assert counter == len(
            parsed_card
        ), f"Expected {len(parsed_card)} values to be parsed, but only parsed {counter}"

        if self.expected_records is not None:
            for key, expected_value in self.expected_records.items():
                if key not in result:
                    raise ValueError(f"Expected record {key} not found in parsed card")
                if result[key] != expected_value:
                    raise ValueError(f"Expected value {expected_value} for record {key}, but got {result[key]}")

        return result

    def _prepare_for_parse_card(self, previous_results: dict[str, any]):
        for record in self.records:
            if record.get_n_values_from:
                card_key, record_key = record.get_n_values_from
                n_values = previous_results[card_key][record_key]
                record.format = f"{n_values}{record.format}"
                record.get_n_values_from = None

        self.set_reader()

        char_counter = 0
        new_records: list[FortranFormatCardRecord] = []
        for record in self.records:
            if record.type == RecordType.NEWLINE:
                new_records.append(record)
                char_counter = 0
                continue

            record_n_values = record.get_n_values()
            record_chars_per_value = record.get_chars_per_value()
            chars_for_record = record_n_values * record_chars_per_value

            if char_counter + chars_for_record <= MAX_LINE_LENGTH:
                char_counter += chars_for_record
                new_records.append(record)
                continue

            # Add records of the same type until the line is full
            for i in range(record_n_values):
                if char_counter + record_chars_per_value > MAX_LINE_LENGTH:
                    new_records.append(FortranFormatCardRecord(key=None, format="/", type=RecordType.NEWLINE))
                    char_counter = 0

                # Remove integers at beginning of string for format
                new_format = re.sub(r"^\d+", "", record.format)
                new_format = f"1{new_format}"  # Add 1 to format
                new_records.append(
                    FortranFormatCardRecord(
                        key=record.key,
                        format=new_format,
                        type=record.type,
                    )
                )
                char_counter += record_chars_per_value

        self.records = new_records
        self.set_reader()


@dataclass
class FortranFormatMultipleBasicCard(FortranFormatBaseCard):
    repeated_record_for_cards: str = None
    repeated_record_for_values: str = None
    get_n_cards_and_values_from: tuple[str, str] = None
    _n_values_list: list[int] = None

    def __post_init__(self):
        if not self.repeated_record_for_cards:
            raise ValueError("repeated_record_for_cards is required for FortranFormatMultipleBasicCard")
        if not self.repeated_record_for_values:
            raise ValueError("repeated_record_for_values is required for FortranFormatMultipleBasicCard")

        if self.get_n_cards_and_values_from is None:
            raise ValueError("get_n_cards_and_values_from is required for FortranFormatMultipleBasicCard")
        assert type(self.get_n_cards_and_values_from) == tuple, "get_n_cards_and_values_from must be a tuple"
        assert len(self.get_n_cards_and_values_from) == 2, "get_n_cards_and_values_from must have length 2"

        if self._n_values_list is not None:
            raise ValueError("_n_values_list is not allowed to be set manually")

    def parse_card(self, card_data: str):
        all_results: list[dict[str, any]] = []

        parsed_card = self._reader.read(card_data)

        result = None

        counter = 0
        for record in self.records:
            if record.type == RecordType.NEWLINE or record.type == RecordType.EMPTY:
                continue

            if record.key == self.repeated_record_for_cards:
                result = {}
                all_results.append(result)
            elif result is None:
                raise ValueError(f"Record {record.key} parsed before repeated record {self.repeated_record_for_cards}")

            n_values = record.get_n_values()

            assert counter + n_values <= len(
                parsed_card
            ), f"Record {record.key} expected {n_values} values, but only {len(parsed_card) - counter} values left"

            if n_values == 1 and record.type == RecordType.SCALAR:
                result[record.key] = parsed_card[counter]
            else:
                result[record.key] = parsed_card[counter : counter + n_values]
            counter += n_values

        assert counter == len(
            parsed_card
        ), f"Expected {len(parsed_card)} values to be parsed, but only parsed {counter}"

        if self.expected_records is not None:
            for result in all_results:
                for key, expected_value in self.expected_records.items():
                    if key not in result:
                        raise ValueError(f"Expected record {key} not found in parsed card")
                    if result[key] != expected_value:
                        raise ValueError(f"Expected value {expected_value} for record {key}, but got {result[key]}")

        return all_results

    def _prepare_for_parse_card(self, previous_results: dict[str, any]):
        card_key, record_key = self.get_n_cards_and_values_from
        self._n_values_list = previous_results[card_key][record_key]

        record_for_repeating_card = next(
            (record for record in self.records if record.key == self.repeated_record_for_cards), None
        )
        record_for_repeating_values = next(
            (record for record in self.records if record.key == self.repeated_record_for_values), None
        )

        if record_for_repeating_card is None:
            raise ValueError(f"Record {self.repeated_record_for_cards} not found in records")
        if record_for_repeating_values is None:
            raise ValueError(f"Record {self.repeated_record_for_values} not found in records")

        new_records_lists: list[list[FortranFormatCardRecord]] = []
        for record in self.records:
            if record.key == self.repeated_record_for_cards:
                for card_idx in range(len(self._n_values_list)):
                    assert len(new_records_lists) == card_idx, "Length of new_records_lists is not equal to card_idx"
                    new_records_lists.append([])
                    new_records_lists[card_idx].append(record)
                continue
            if record.key == self.repeated_record_for_values:
                # Check that record does not start with integer
                if re.match(r"^\d+", record.format):
                    raise ValueError(f"Record {record.key} has format starting with an integer")

                for card_idx in range(len(self._n_values_list)):
                    new_record = FortranFormatCardRecord(
                        key=record.key,
                        format=f"{self._n_values_list[card_idx]}{record.format}",
                        type=record.type,
                    )

                    new_records_lists[card_idx].append(new_record)
                continue
            for card_idx in range(len(self._n_values_list)):
                new_records_lists[card_idx].append(record)

        # Add newline record between cards, except for the last card
        for i in range(len(new_records_lists) - 1):
            new_records_lists[i].append(FortranFormatCardRecord(key=None, format="/", type=RecordType.NEWLINE))

        # Flatten list of lists
        self.records = [record for sublist in new_records_lists for record in sublist]

        for record in self.records:
            if record.get_n_values_from:
                # Check that record does not start with integer
                if re.match(r"^\d+", record.format):
                    raise ValueError(f"Record {record.key} has format starting with an integer")

                card_key, record_key = record.get_n_values_from
                n_values = previous_results[card_key][record_key]
                record.format = f"{n_values}{record.format}"
                record.get_n_values_from = None

        self.set_reader()

        char_counter = 0
        new_records: list[FortranFormatCardRecord] = []
        for record in self.records:
            if record.type == RecordType.NEWLINE:
                new_records.append(record)
                char_counter = 0
                continue

            record_n_values = record.get_n_values()
            record_chars_per_value = record.get_chars_per_value()
            chars_for_record = record_n_values * record_chars_per_value

            if char_counter + chars_for_record <= MAX_LINE_LENGTH:
                char_counter += chars_for_record
                new_records.append(record)
                continue

            # Add records of the same type until the line is full
            for i in range(record_n_values):
                if char_counter + record_chars_per_value > MAX_LINE_LENGTH:
                    new_records.append(FortranFormatCardRecord(key=None, format="/", type=RecordType.NEWLINE))
                    char_counter = 0

                # Remove integers at beginning of string for format
                new_format = re.sub(r"^\d+", "", record.format)
                new_format = f"1{new_format}"  # Add 1 to format
                new_records.append(
                    FortranFormatCardRecord(
                        key=record.key,
                        format=new_format,
                        type=record.type,
                    )
                )
                char_counter += record_chars_per_value

        self.records = new_records
        self.set_reader()


@dataclass
class FortranFormatBlock:
    _cards: dict[str, FortranFormatBaseCard] = None
    _result: dict[str, any] = None

    def __post_init__(self):
        if self._cards is not None:
            raise ValueError("_cards is not allowed to be set manually")
        if self._result is not None:
            raise ValueError("_result is not allowed to be set manually")

        self._cards = {}

    def add_card(self, label: str, card: FortranFormatBaseCard):
        if label in self._cards:
            raise ValueError(f"Card with label {label} already exists in block")
        self._cards[label] = card

    def parse_block(self, block_data: str):
        lines = block_data.splitlines()
        if self._result is not None:
            return self._result
        self._result = {}
        current_line = 0

        for label, card in self._cards.items():
            match type(card).__qualname__:
                case FortranFormatBaseCard.__qualname__:
                    raise TypeError(f"Card {label} is of abstract type FortranFormatBaseCard")
                case FortranFormatBasicCard.__qualname__:
                    card: FortranFormatBasicCard

                    card._prepare_for_parse_card(self._result)

                    n_lines = len([card.records for record in card.records if record.type == RecordType.NEWLINE]) + 1
                    card_data = "\n".join(lines[current_line : current_line + n_lines])
                    current_line += n_lines
                    self._result[label] = card.parse_card(card_data)
                case FortranFormatMultipleBasicCard.__qualname__:
                    card: FortranFormatMultipleBasicCard

                    card._prepare_for_parse_card(self._result)

                    n_lines = len([card.records for record in card.records if record.type == RecordType.NEWLINE]) + 1
                    card_data = "\n".join(lines[current_line : current_line + n_lines])
                    current_line += n_lines
                    self._result[label] = card.parse_card(card_data)
                case _:
                    raise TypeError(f"Card {label} is of unknown type {type(card)}")

        return self._result
