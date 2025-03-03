import os
from pathlib import Path

from myskoxe.parse.fortran_format import (
    FortranFormatBasicCard,
    FortranFormatBlock,
    FortranFormatCardRecord,
    FortranFormatMultipleBasicCard,
    RecordType,
)

gendf_path = Path(f"/Users/sigge/projects/physics/myskoxe/myskoxe/frendy/tests/U235_MATXS_92235.09c.mg")


def test_fortran_format():
    ff_block = FortranFormatBlock()

    ff_block.add_card(
        "0v",
        FortranFormatBasicCard(
            records=[
                FortranFormatCardRecord(key="title", format="A4", type=RecordType.SCALAR),
                FortranFormatCardRecord(key="hname", format="A8", type=RecordType.SCALAR),
                FortranFormatCardRecord(key="sep1", format="A1", type=RecordType.SCALAR),
                FortranFormatCardRecord(key="huse1", format="A8", type=RecordType.SCALAR),
                FortranFormatCardRecord(key="huse2", format="A8", type=RecordType.SCALAR),
                FortranFormatCardRecord(key="sep2", format="A1", type=RecordType.SCALAR),
                FortranFormatCardRecord(key="ivers", format="I6", type=RecordType.SCALAR),
            ],
            expected_records={"title": " 0v "},
        ),
    )

    ff_block.add_card(
        "1d",
        FortranFormatBasicCard(
            records=[
                FortranFormatCardRecord(key="title", format="A6", type=RecordType.SCALAR),
                FortranFormatCardRecord(key="npart", format="I6", type=RecordType.SCALAR),
                FortranFormatCardRecord(key="ntype", format="I6", type=RecordType.SCALAR),
                FortranFormatCardRecord(key="nholl", format="I6", type=RecordType.SCALAR),
                FortranFormatCardRecord(key="nmat", format="I6", type=RecordType.SCALAR),
                FortranFormatCardRecord(key="maxw", format="I6", type=RecordType.SCALAR),
                FortranFormatCardRecord(key="length", format="I6", type=RecordType.SCALAR),
            ],
            expected_records={"title": " 1d   "},
        ),
    )

    ff_block.add_card(
        "2d",
        FortranFormatBasicCard(
            records=[
                FortranFormatCardRecord(key="title", format="A4", type=RecordType.SCALAR),
                FortranFormatCardRecord(key=None, format="/", type=RecordType.NEWLINE),
                FortranFormatCardRecord(key="hsetid", format="7A8", type=RecordType.ARRAY),
            ],
            expected_records={"title": " 2d "},
        ),
    )

    ff_block.add_card(
        "3d",
        FortranFormatBasicCard(
            records=[
                FortranFormatCardRecord(key="title", format="A4", type=RecordType.SCALAR),
                FortranFormatCardRecord(key=None, format="4X", type=RecordType.EMPTY),
                FortranFormatCardRecord(
                    key="hprt", format="A8", type=RecordType.ARRAY, get_n_values_from=("1d", "npart")
                ),
                FortranFormatCardRecord(
                    key="htype", format="A8", type=RecordType.ARRAY, get_n_values_from=("1d", "ntype")
                ),
                FortranFormatCardRecord(
                    key="hmatn", format="A8", type=RecordType.ARRAY, get_n_values_from=("1d", "nmat")
                ),
                FortranFormatCardRecord(key=None, format="/", type=RecordType.NEWLINE),
                FortranFormatCardRecord(
                    key="ngrp", format="I6", type=RecordType.ARRAY, get_n_values_from=("1d", "npart")
                ),
                FortranFormatCardRecord(
                    key="jinp", format="I6", type=RecordType.ARRAY, get_n_values_from=("1d", "ntype")
                ),
                FortranFormatCardRecord(
                    key="joutp", format="I6", type=RecordType.ARRAY, get_n_values_from=("1d", "ntype")
                ),
                FortranFormatCardRecord(
                    key="nsubm", format="I6", type=RecordType.ARRAY, get_n_values_from=("1d", "nmat")
                ),
                FortranFormatCardRecord(
                    key="locm", format="I6", type=RecordType.ARRAY, get_n_values_from=("1d", "nmat")
                ),
            ],
            expected_records={"title": " 3d "},
        ),
    )

    # !cr group structure
    # !c
    # !cl (gpb(i),i=1,ngr),emin
    # !c
    # !cc ngr=ngrp(j)
    # !c
    # !cw ngrp(j)+1
    # !c
    # !cb format(4h 4d ,8x,1p,5e12.5/(6e12.5))
    # !c
    # !cd gpb(i) maximum energy bound for group i for particle j
    # !cd emin minimum energy bound for particle j

    ff_block.add_card(
        "4d",
        FortranFormatMultipleBasicCard(
            records=[
                FortranFormatCardRecord(key="title", format="A4", type=RecordType.SCALAR),
                FortranFormatCardRecord(key=None, format="8X", type=RecordType.EMPTY),
                FortranFormatCardRecord(key="gpb", format="E12.5", type=RecordType.ARRAY),
                FortranFormatCardRecord(key="emin", format="E12.5", type=RecordType.SCALAR),
            ],
            expected_records={"title": " 4d "},
            get_n_cards_and_values_from=("3d", "ngrp"),
            repeated_record_for_cards="title",
            repeated_record_for_values="gpb",
        ),
    )

    results = ff_block.parse_block(gendf_path.read_text())

    print(results)


if __name__ == "__main__":
    test_fortran_format()
