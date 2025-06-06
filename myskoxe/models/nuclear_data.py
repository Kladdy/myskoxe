from dataclasses import dataclass
from enum import StrEnum, auto

import numpy as np
from numpy.typing import NDArray


@dataclass
class MyData:
    data: NDArray[np.float64]


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


from enum import StrEnum, auto


class ReactionChannelLabel(StrEnum):
    # Table references from NJOY 2016 documentation

    # Table 14: Simple Neutron-Emitting Reactions
    nelas = auto()  # neutron elastic scattering
    nnonel = auto()  # neutron nonelastic (MT=1–MT=2)
    ninel = auto()  # neutron inelastic sum (MT=51–91)
    n2n = auto()  # (n,2n)
    n3n = auto()  # (n,3n)
    nna = auto()  # (n,n′α)
    nnp = auto()  # (n,n′p)
    n01 = auto()  # (n,n1)
    n02 = auto()  # (n,n2)
    ncn = auto()  # (n,n′) to continuum

    # Table 15: Breakup Reactions (LR flags)
    n07a = auto()  # (n,n7)α
    n51p = auto()  # (n,n15)p
    n02aa = auto()  # (n,n2)2α
    ncnaaa = auto()  # (n,n′)3α
    n06na = auto()  # (n,n5)nα
    n01ee = auto()  # (n,n1)ee

    # Table 16: Neutron-Absorption Reactions
    nabs = auto()  # total absorption
    ng = auto()  # radiative capture
    np = auto()  # (n,p)
    na = auto()  # (n,α)

    # Table 17: Fission Reactions
    nftot = auto()  # total fission
    nf = auto()  # (n,f) first-chance fission
    nnf = auto()  # (n,n′f) second-chance fission
    n2nf = auto()  # (n,n2f) third-chance fission
    n3nf = auto()  # (n,n3f) fourth-chance fission
    nudel = auto()  # delayed-neutron yield (MF=3)
    chid = auto()  # delayed-neutron spectrum (MF=5)

    # Table 18: Special NJOY Names
    ntot0 = auto()  # P0 total cross section
    ntot1 = auto()  # P1 total cross section
    nwt0 = auto()  # P0 weight function (flux)
    nwt1 = auto()  # P1 weight function (flux)
    mubar = auto()  # scattering bar(µ)
    xi = auto()  # scattering ξ
    invel = auto()  # inverse velocity (sec/m)
    heat = auto()  # energy-balance heat production
    kerma = auto()  # kinematic KERMA factor
    dame = auto()  # damage-energy production

    # Table 19: Gas-Production Reactions
    n_neut = auto()  # total neutron production
    n_gam = auto()  # total γ production
    n_h1 = auto()  # hydrogen production
    n_h3 = auto()  # tritium production
    n_HE4 = auto()  # helium production

    # Table 20: Incident-Proton Reactions
    pelas = auto()  # proton elastic scattering
    p01 = auto()  # discrete-level (p,p1) scattering
    n00 = auto()  # discrete-level (p,n0)
    # n01 = auto()        # discrete-level (p,n1)
    p2n = auto()  # (p,2n)
    pg = auto()  # (p,γ)
    pt = auto()  # (p,t)

    # Table 21: Thermal Material Names for ENDF/B-VII
    free = auto()  # free-gas scattering
    hh2o = auto()  # H in H2O
    poly = auto()  # H in polyethylene (CH2) incoherent
    poly_ = auto()  # H in polyethylene (CH2) coherent
    hzrh = auto()  # H in ZrH incoherent
    hzrh_ = auto()  # H in ZrH coherent
    benz = auto()  # Benzene incoherent
    dd2o = auto()  # D in D2O
    graph = auto()  # C in graphite incoherent
    graph_ = auto()  # C in graphite coherent
    be = auto()  # Be metal incoherent
    be_ = auto()  # Be metal coherent
    bebeo = auto()  # Be in BeO incoherent
    bebeo_ = auto()  # Be in BeO coherent
    zrzrh = auto()  # Zr in ZrH incoherent
    zrzrh_ = auto()  # Zr in ZrH coherent
    obeo = auto()  # O in BeO incoherent
    obeo_ = auto()  # O in BeO coherent
    ouo2 = auto()  # O in UO2 incoherent
    ouo2_ = auto()  # O in UO2 coherent
    uuo2 = auto()  # U in UO2 incoherent
    uuo2_ = auto()  # U in UO2 coherent
    al = auto()  # Al metal incoherent
    al_ = auto()  # Al metal coherent
    fe = auto()  # Fe metal incoherent
    fe_ = auto()  # Fe metal coherent

    # Table 22: Photoatomic Cross Sections
    gtot0 = auto()  # P0 total
    gwt0 = auto()  # P0 weight function (flux)
    gcoh = auto()  # coherent scattering
    ginch = auto()  # incoherent scattering
    gpair = auto()  # pair production (γ,2γ)
    gabs = auto()  # photoelectric absorption
    gheat = auto()  # heating


@dataclass
class EnergyGroupStructure:
    boundaries: NDArray[np.float64]

    @property
    def number_of_groups(self) -> int:
        return self.boundaries.size - 1


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
class Submaterial:
    ambient_temperature: float
    dilution_factor: float
    data_type_index: int


@dataclass
class Material:
    name: str
    atomic_weight_ratio: float
    submaterials: list[Submaterial]


@dataclass
class NuclearData:
    particles: list[Particle]
    data_types: list[DataType]
    materials: list[Material]
