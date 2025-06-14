from pathlib import Path

import numpy as np

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

    # Print first example of matrix
    print(nuclear_data.materials[0].submaterials[0].matrices[0].data)

    import os

    from matplotlib import pyplot as plt

    PLOT_DIR = Path("plots")

    os.makedirs(PLOT_DIR, exist_ok=True)

    # exit()

    for material in nuclear_data.materials:
        print(f"Material: {material.name}, Atomic Weight Ratio: {material.atomic_weight_ratio}")

        for submaterial_idx, submaterial in enumerate(material.submaterials):
            print(
                f"  Submaterial: Ambient Temperature: {submaterial.ambient_temperature}, Dilution Factor: {submaterial.dilution_factor}, Data Type Index: {submaterial.data_type_index}"
            )

            for vector in submaterial.vectors:

                incident_particle_index = nuclear_data.data_types[submaterial.data_type_index].incident_particle_index
                incident_particle = (
                    nuclear_data.particles[incident_particle_index] if incident_particle_index is not None else None
                )

                if not incident_particle:
                    print(f"  Vector: {vector.label} - no incident particle, skipping plot")
                    continue

                energy = incident_particle.energy_group_structure.bin_centers

                plt.plot(
                    energy[vector.first_group_index : vector.last_group_index + 1],
                    vector.data,
                    "|-",
                    label=f"{vector.label} (Groups {vector.first_group_index + 1} to {vector.last_group_index + 1})",
                )
                plt.xlabel("Energy [eV]")
                plt.ylabel("Cross Section [barns]")
                plt.title(
                    f"Cross Section for {incident_particle.label.name} in {material.name}, submaterial {submaterial_idx}, vector {vector.label}"
                )
                plt.xscale("log")
                plt.yscale("log")
                plt.legend()
                plt.grid(True)
                plt.savefig(
                    f"{PLOT_DIR}/cross_section_{material.name}_submaterial-{submaterial_idx}_{incident_particle.label.name}_{vector.label}.png"
                )
                plt.close()

            for matrix in submaterial.matrices:
                plt.spy(matrix.data, markersize=1)
                plt.title("Sparsity pattern of the matrix")
                plt.xlabel("Incoming Energy Group Index")
                plt.ylabel("Outgoing Energy Group Index")

                plt.savefig(
                    f"{PLOT_DIR}/sparsity_pattern_{material.name}_submaterial-{submaterial_idx}_{matrix.label}.png"
                )
                plt.close()

                # if submaterial_idx == 0 and matrix.label == "nftot":
                #     # Example of how to access the data
                #     print(f"Matrix {matrix.label} data:\n{matrix.data.toarray()}")

            # total_dense_bytes = 0
            # total_sparse_bytes = 0

            # for matrix in submaterial.matrices:
            #     sparse = matrix.data

            #     # Dense size: all entries (rows × cols) × size of float64 (8 bytes)
            #     dense_size = sparse.shape[0] * sparse.shape[1] * np.dtype(np.float64).itemsize
            #     total_dense_bytes += dense_size

            #     # Sparse size: size of data + indices + indptr
            #     sparse_size = sparse.data.nbytes + sparse.indices.nbytes + sparse.indptr.nbytes
            #     total_sparse_bytes += sparse_size

            # # Calculate savings
            # savings = 100 * (total_dense_bytes - total_sparse_bytes) / total_dense_bytes
            # print(f"Total memory savings: {savings:.2f}%")

            #     break  # TODO: Remove
            # break  # TODO: Remove
