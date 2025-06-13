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

    import os

    from matplotlib import pyplot as plt

    PLOT_DIR = Path("plots")

    os.makedirs(PLOT_DIR, exist_ok=True)

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
                    f"{PLOT_DIR}/{material.name}_submaterial-{submaterial_idx}_{incident_particle.label.name}_{vector.label}_cross_section.png"
                )
                plt.close()
