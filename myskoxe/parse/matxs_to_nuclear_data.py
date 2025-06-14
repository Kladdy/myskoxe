import warnings

import numpy as np
from numpy.typing import NDArray
from scipy.sparse import csr_array

from myskoxe.models.nuclear_data import (
    DataType,
    DataTypeLabel,
    EnergyGroupStructure,
    Material,
    Matrix,
    NuclearData,
    Particle,
    ParticleLabel,
    SubMaterial,
    Vector,
)
from myskoxe.parse.parse_matxs import MATXSFile, MATXSMaterial, MATXSSubMaterial


def parse_matxs_to_nuclear_data(matxs_file: MATXSFile):
    """
    Convert a MATXSFile to a NuclearData object.

    Args:
        matxs_file (MATXSFile): The MATXS file to convert.

    Returns:
        NuclearData: The converted nuclear data.
    """

    particles = list(get_particles(matxs_file))
    data_types = list(get_data_types(matxs_file))
    materials = list(get_materials(matxs_file, particles, data_types))

    nuclear_data = NuclearData(
        particles=particles,
        data_types=data_types,
        materials=materials,
    )

    return nuclear_data


def get_data_types(matxs_file: MATXSFile):
    assert matxs_file.file_control is not None, "MATXS file control is None"
    assert matxs_file.file_data is not None, "MATXS file data is None"

    ntype: int = matxs_file.file_control.data["ntype"]
    htype: list[str] = matxs_file.file_data.data["htype"]
    jinp: list[int] = matxs_file.file_data.data["jinp"]
    joutp: list[int] = matxs_file.file_data.data["joutp"]

    assert len(htype) == ntype, f"Number of data types {len(htype)} does not match {ntype=}"
    assert len(jinp) == ntype, f"Number of incident particle labels {len(jinp)} does not match {ntype=}"
    assert len(joutp) == ntype, f"Number of outgoing particle labels {len(joutp)} does not match {ntype=}"

    for data_type_label, incident_particle_index, outgoing_particle_index in zip(htype, jinp, joutp, strict=True):
        data_type_label = data_type_label.strip()

        assert data_type_label in DataTypeLabel.__members__, f"Unknown data type label: '{data_type_label}'"

        # Special case: For decay data, the incident particle is is "0". Set to None.
        yield DataType(
            label=DataTypeLabel[data_type_label],
            incident_particle_index=(
                None if incident_particle_index == 0 else incident_particle_index - 1
            ),  # Convert to zero-based index
            outgoing_particle_index=outgoing_particle_index - 1,  # Convert to zero-based index
        )


def get_particles(matxs_file: MATXSFile):
    assert matxs_file.file_control is not None, "MATXS file control is None"
    assert matxs_file.file_data is not None, "MATXS file data is None"

    npart: int = matxs_file.file_control.data["npart"]
    hprt: list[str] = matxs_file.file_data.data["hprt"]
    ngrp: list[int] = matxs_file.file_data.data["ngrp"]

    assert len(hprt) == npart, f"Number of particle labels {len(hprt)} does not match {npart=}"
    assert len(ngrp) == npart, f"Number of energy groups {len(ngrp)} does not match {npart=}"
    assert (
        len(matxs_file.particles) == npart
    ), f"Number of particles {len(matxs_file.particles)} does not match {npart=}"

    for particle_label, number_of_energy_groups, matxs_particle in zip(hprt, ngrp, matxs_file.particles, strict=True):
        particle_label = particle_label.strip()

        assert matxs_particle.group_structure is not None, f"Particle '{particle_label}' has no energy group structure"

        gpb = matxs_particle.group_structure.data["gpb"]
        emin = matxs_particle.group_structure.data["emin"]

        assert particle_label in ParticleLabel.__members__, f"Unknown particle label: '{particle_label}'"

        assert number_of_energy_groups == len(
            gpb
        ), f"Number of energy groups {number_of_energy_groups} does not match length of gpb {len(gpb)} for particle '{particle_label}'"

        yield Particle(
            label=ParticleLabel[particle_label],
            energy_group_structure=EnergyGroupStructure(boundaries=np.append(np.array(gpb, dtype=np.float64), emin)),
        )


def get_materials(matxs_file: MATXSFile, particles: list[Particle], data_types: list[DataType]):
    assert matxs_file.file_control is not None, "MATXS file control is None"
    assert matxs_file.file_data is not None, "MATXS file data is None"

    nmat: int = matxs_file.file_control.data["nmat"]
    hmatn: list[str] = matxs_file.file_data.data["hmatn"]

    assert len(hmatn) == nmat, f"Number of material labels {len(hmatn)} does not match {nmat=}"

    for material_label, matxs_material in zip(hmatn, matxs_file.materials, strict=True):
        material_label = material_label.strip()

        assert matxs_material.material_control is not None, f"Material '{material_label}' has no material control data"

        hmat: str = matxs_material.material_control.data["hmat"]
        amass: float = matxs_material.material_control.data["amass"]
        temp: list[float] = matxs_material.material_control.data["temp"]
        sigz: list[float] = matxs_material.material_control.data["sigz"]
        itype: list[int] = matxs_material.material_control.data["itype"]

        hmat = hmat.strip()

        assert hmat == material_label, f"Material label '{hmat}' does not match expected label '{material_label}'"

        yield Material(
            name=material_label,
            atomic_weight_ratio=amass,
            submaterials=list(get_submaterials(matxs_file, matxs_material, temp, sigz, itype, particles, data_types)),
        )


def get_submaterials(
    matxs_file: MATXSFile,
    matxs_material: MATXSMaterial,
    temp: list[float],
    sigz: list[float],
    itype: list[int],
    particles: list[Particle],
    data_types: list[DataType],
):

    for submaterial_idx, (matxs_submaterial, temperature, dilution_factor, data_type_index) in enumerate(
        zip(matxs_material.submaterials, temp, sigz, itype, strict=True)
    ):

        # If matxs_submaterial.vector_control is None but we have more than 0 matxs_submaterial.vector_blocks,
        # we should raise an exception. Vice versa as well, if matxs_submaterial.vector_control is not None but
        # we have 0 vector_blocks.
        if matxs_submaterial.vector_control is None and len(matxs_submaterial.vector_blocks) > 0:
            raise ValueError(f"Submaterial with index {submaterial_idx} has vector blocks but no vector control data.")
        if matxs_submaterial.vector_control is not None and len(matxs_submaterial.vector_blocks) == 0:
            raise ValueError(f"Submaterial  with index {submaterial_idx} has vector control data but no vector blocks.")

        data_type_index = data_type_index - 1  # Convert to zero-based index

        data_type = data_types[data_type_index]
        incoming_particle = (
            particles[data_type.incident_particle_index] if data_type.incident_particle_index is not None else None
        )
        if incoming_particle is None:
            raise ValueError(
                f"Data type index {data_type_index} for submaterial {submaterial_idx} does not have a valid incident particle."
            )
        outgoing_particle = particles[data_type.outgoing_particle_index]
        if outgoing_particle is None:
            raise ValueError(
                f"Data type index {data_type_index} for submaterial {submaterial_idx} does not have a valid outgoing particle."
            )

        yield SubMaterial(
            ambient_temperature=temperature,
            dilution_factor=dilution_factor,
            data_type_index=data_type_index,
            vectors=(
                list(get_vectors(matxs_file, matxs_submaterial)) if matxs_submaterial.vector_control is not None else []
            ),
            matrices=(list(get_matrices(matxs_file, matxs_submaterial, incoming_particle, outgoing_particle))),
        )


def get_vectors(matxs_file: MATXSFile, matxs_submaterial: MATXSSubMaterial):
    assert matxs_submaterial.vector_control is not None, "MATXS submaterial vector control is None"

    hvps: list[str] = matxs_submaterial.vector_control.data["hvps"]
    nfg: list[int] = matxs_submaterial.vector_control.data["nfg"]
    nlg: list[int] = matxs_submaterial.vector_control.data["nlg"]

    vps_all = np.concatenate([vector_block.data["vps"] for vector_block in matxs_submaterial.vector_blocks])

    assert (
        len(hvps) == len(nfg) == len(nlg)
    ), f"Number of vector labels {len(hvps)} does not match number of fine groups {len(nfg)} and number of large groups {len(nlg)}"

    data_index = 0  # Position at which to start reading data from vps_all
    for vector_label, first_group_index, last_group_index in zip(hvps, nfg, nlg, strict=True):
        vector_label = vector_label.strip()

        assert (
            first_group_index <= last_group_index
        ), f"First group index {first_group_index} must be less than or equal to last group index {last_group_index}"

        number_of_data_points = last_group_index - first_group_index + 1
        data = vps_all[data_index : data_index + number_of_data_points]
        data_index += number_of_data_points

        yield Vector(
            label=vector_label,
            data=data.astype(np.float64),
            first_group_index=first_group_index - 1,  # Convert to zero-based index
            last_group_index=last_group_index - 1,  # Convert to zero-based index
        )


def get_matrices(
    matxs_file: MATXSFile, matxs_submaterial: MATXSSubMaterial, incoming_particle: Particle, outgoing_particle: Particle
):
    for matxs_matrix_block in matxs_submaterial.matrix_blocks:
        assert matxs_matrix_block.matrix_control is not None, "MATXS matrix control is None"

        hmtx: str = matxs_matrix_block.matrix_control.data["hmtx"]
        lord: int = matxs_matrix_block.matrix_control.data["lord"]
        jconst: int = matxs_matrix_block.matrix_control.data["jconst"]
        jband: list[int] = matxs_matrix_block.matrix_control.data["jband"]
        ijj: list[int] = matxs_matrix_block.matrix_control.data["ijj"]

        hmtx = hmtx.strip()

        assert len(jband) == len(ijj), f"Length of jband {len(jband)} does not match length of ijj {len(ijj)}"

        scat_all = np.concatenate(
            [matrix_sub_block.data["scat"] for matrix_sub_block in matxs_matrix_block.matrix_sub_blocks]
        )

        jband_cumulative_sum = np.cumulative_sum(jband)

        band_start_indexes = np.concatenate(([0], jband_cumulative_sum[:-1])) * lord
        band_end_indexes = jband_cumulative_sum * lord

        band_data = [
            np.zeros(
                (
                    outgoing_particle.energy_group_structure.number_of_groups,
                    incoming_particle.energy_group_structure.number_of_groups,
                ),
                dtype=np.float64,
            )
            for _ in range(lord)
        ]
        for band_index, (band_start_index, band_end_index, index_for_highest_group) in enumerate(
            zip(band_start_indexes, band_end_indexes, ijj, strict=True)
        ):
            band_width_including_orders = band_end_index - band_start_index
            if band_width_including_orders % lord != 0:
                raise ValueError(
                    f"Band width {band_width_including_orders} is not divisible by order {lord} for matrix '{hmtx}'"
                )
            band_width_excluding_orders = band_width_including_orders // lord

            # Extract the relevant data for this band
            band_data_for_outgoing = scat_all[band_start_index:band_end_index]

            # Split the data to get one batch for each order
            band_data_for_outgoing_per_order = split_into_batches_strict(band_data_for_outgoing, lord)

            for order in range(lord):
                # Each order has a band of data
                band_data[order][
                    band_index, index_for_highest_group - band_width_excluding_orders : index_for_highest_group
                ] = band_data_for_outgoing_per_order[order].astype(np.float64)

        for order, S in enumerate(band_data):
            S_csr = csr_array(S)

            yield Matrix(label=hmtx, data=S_csr, order=order)

        if matxs_matrix_block.constant_sub_block is not None:
            warnings.warn(
                f"Matrix '{hmtx}' has a constant sub-block, which is not yet supported. Will be ignored.", UserWarning
            )


def split_into_batches_strict(array: NDArray, batch_count: int):
    if array.size % batch_count != 0:
        raise ValueError("Array size must be divisible by batch count")
    return np.split(array, batch_count)
