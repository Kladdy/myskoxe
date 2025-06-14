from dataclasses import dataclass
from enum import StrEnum, auto

import numpy as np
from numpy.typing import NDArray
from scipy.sparse import csr_array


class ParticleLabel(StrEnum):
    n = auto()  # neutron
    g = auto()  # gamma
    p = auto()  # proton
    d = auto()  # deuteron
    t = auto()  # triton
    he3 = auto()  # 3He nucleus
    a = auto()  # alpha
    b = auto()  # beta
    r = auto()  # residual or recoil (heavier than α)
    no_particle = auto()  # no particle (e.g., for decay data)


class DataTypeLabel(StrEnum):
    nscat = auto()  # neutron scattering
    ng = auto()  # neutron induced gamma production
    np = auto()  # neutron-induced proton production
    nr = auto()  # neutron-to-recoil matrix
    gscat = auto()  # gamma scattering
    pscat = auto()  # proton scattering
    pn = auto()  # proton induced neutron production
    ntherm = auto()  # thermal scattering data
    dkn = auto()  # delayed neutron data
    dkhg = auto()  # decay heat and gamma data
    dkb = auto()  # decay beta data


@dataclass
class EnergyGroupStructure:
    boundaries: NDArray[np.float64]

    @property
    def number_of_groups(self) -> int:
        return self.boundaries.size - 1

    @property
    def bin_centers(self) -> NDArray[np.float64]:
        return (self.boundaries[:-1] + self.boundaries[1:]) / 2


@dataclass
class Particle:
    label: ParticleLabel
    energy_group_structure: EnergyGroupStructure


@dataclass
class DataType:
    label: DataTypeLabel
    incident_particle_index: int | None  # Can be None for decay data
    outgoing_particle_index: int


@dataclass
class Vector:
    label: str
    data: NDArray[np.float64]
    first_group_index: int
    last_group_index: int


@dataclass
class Matrix:
    label: str
    data: csr_array
    order: int


@dataclass
class SubMaterial:
    ambient_temperature: float
    dilution_factor: float
    data_type_index: int
    vectors: list[Vector]
    matrices: list[Matrix]


@dataclass
class Material:
    name: str
    atomic_weight_ratio: float
    submaterials: list[SubMaterial]


@dataclass
class NuclearData:
    particles: list[Particle]
    data_types: list[DataType]
    materials: list[Material]
