from pathlib import Path

from myskoxe.parse.parse_matxs import CardContainer, MATXSFile

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
