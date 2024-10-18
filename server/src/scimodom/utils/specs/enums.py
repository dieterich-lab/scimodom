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


# Specifications


class Value:
    def __init__(self, value: int):
        self.value = value


class Identifiers(Enum):
    """Define properties for identifiers."""

    SMID = Value(8)
    EUFID = Value(12)
    ASSEMBLY = Value(12)

    @property
    def length(self):
        return self.value.value


# Annotation and assembly


class Ensembl(Enum):
    """Define release and destination for Ensembl services."""

    RELEASE = 110
    FTP = "https://ftp.ensembl.org/pub"
    # http://rest.ensembl.org
    REST = "http://jul2023.rest.ensembl.org"
    ARCHIVE = "https://jul2023.archive.ensembl.org"
    DATA = "info/data"
    ASM = "info/assembly"
    # current_assembly_chain
    ASM_MAPPING = f"release-{RELEASE}/assembly_chain"


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
