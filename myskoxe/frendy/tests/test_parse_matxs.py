from pathlib import Path

from myskoxe.parse.parse_matxs import MATXSFile

if __name__ == "__main__":
    gendf_path = Path(
        f"/Users/sigge/projects/physics/myskoxe/myskoxe/frendy/tests/U235_MATXS_92235.09c_modified_row_56.mg"
        # f"/Users/sigge/projects/physics/myskoxe/myskoxe/frendy/tests/U235_MATXS_92235.09c.mg"
    )

    parse_file = MATXSFile.parse_file(gendf_path)
