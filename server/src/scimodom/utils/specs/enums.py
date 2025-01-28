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


class IntValue:
    def __init__(self, value: int):
        self.value = value


class FloatValue:
    def __init__(self, value: float):
        self.value = value


class Identifiers(Enum):
    """Define properties for identifiers."""

    SMID = IntValue(8)
    EUFID = IntValue(12)
    ASSEMBLY = IntValue(12)

    @property
    def length(self):
        return self.value.value


class ImportLimits(Enum):
    """Define error thresholds for data import."""

    BED = FloatValue(0.05)
    LIFTOVER = FloatValue(0.3)

    @property
    def max(self):
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
    INFO = "info.json"
    RELEASE = "release.json"
    CHROM = "chrom.sizes"
    CHAIN = "{source_assembly}_to_{target_assembly}.chain.gz".format
    DNA = "{organism}.{assembly}.dna.chromosome.{chrom}.fa.gz".format
    DNA_IDX = "{organism}.{assembly}.dna.chromosome.{chrom}.fa.gz.fai".format
    DNA_BGZ = "{organism}.{assembly}.dna.chromosome.{chrom}.fa.gz.gzi".format

    @classmethod
    def common(cls):
        return cls.INFO, cls.RELEASE, cls.CHROM

    @classmethod
    def fasta(cls):
        return cls.DNA, cls.DNA_IDX, cls.DNA_BGZ

    @classmethod
    def is_chain(cls, file_type):
        return file_type == cls.CHAIN

    @classmethod
    def is_fasta(cls, file_type):
        return file_type in cls.fasta()


class TargetsFileType(Enum):
    MIRNA = "mirna.bed".format
    RBP = "rbp_{chrom}.bed".format


# Misc. e.g. charts


class SunburstChartType(Enum):
    search = "search"
    browse = "browse"
