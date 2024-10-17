from enum import Enum


# Data and models


class UserState(Enum):
    """Define state for declarative model User."""

    wait_for_confirmation = 0
    active = 1


class Strand(Enum):
    """Define strand for declarative model Data.
    This is also used to define data-related DTOs."""

    FORWARD = "+"
    REVERSE = "-"
    UNDEFINED = "."


# Annotation and assembly


class AnnotationSource(Enum):
    ENSEMBL = "ensembl"
    GTRNADB = "gtrnadb"


class AssemblyFileType(Enum):
    CHROM = "chrom.sizes"
    INFO = "info.json"
    RELEASE = "release.json"
    CHAIN = "__CHAIN__"
    DNA = "{organism}.{assembly}.dna.chromosome.{chrom}.fa.gz".format


class TargetsFileType(Enum):
    MIRNA = "mirna.bed".format
    RBP = "rbp_{chrom}.bed".format


# Misc. e.g. charts


class SunburstChartType(Enum):
    search = "search"
    browse = "browse"
