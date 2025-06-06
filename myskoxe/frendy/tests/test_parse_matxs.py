from pathlib import Path

from myskoxe.parse.matxs_to_nuclear_data import parse_matxs_to_nuclear_data
from myskoxe.parse.parse_matxs import MATXSFile

if __name__ == "__main__":
    gendf_path = Path(
        # f"/Users/sigge/projects/physics/myskoxe/myskoxe/frendy/tests/U235_MATXS_92235.09c_modified_row_56.mg"
        f"/Users/sigge/projects/physics/myskoxe/myskoxe/frendy/tests/U235_MATXS_92235.09c.mg"
    )

    parsed_file = MATXSFile.parse_file(gendf_path)
    print(parsed_file.messages)

    nuclear_data = parse_matxs_to_nuclear_data(parsed_file)

    print(nuclear_data)
