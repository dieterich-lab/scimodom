from enum import Enum

# Data and models


class UserState(Enum):
    """Define state for declarative model User."""

    wait_for_confirmation = 0
    active = 1


class Strand(Enum):
    """Define strand for declarative model Data.

    This is also used to define data-related DTOs.
    """

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


# The Ensembl release and archive that are currently installed.
#
# These describe this installation, not Ensembl: which snapshot the
# reference files were obtained from. They are passed to the services
# that build URLs rather than baked into the URLs themselves, so that
# they can be supplied per invocation and recorded with the data.
#
# TODO: supply these as CLI arguments, validate them against the REST
# API and persist them at creation time, cf. #157, #201.
CURRENT_ENSEMBL_RELEASE = 110
CURRENT_ENSEMBL_ARCHIVE = "jul2023"


class Ensembl(Enum):
    """Define the Ensembl URL layout.

    Members describe where Ensembl serves data and how its URLs are
    built. They deliberately do not record which release or archive is
    installed: that is a property of the installation, cf.
    CURRENT_ENSEMBL_RELEASE and CURRENT_ENSEMBL_ARCHIVE, and is passed
    in by the caller.

    The archive token e.g. "jul2023" is shared by the REST and the web
    archive hosts, so both are built from it.
    """

    FTP = "https://ftp.ensembl.org/pub"
    # the unarchived hosts are http://rest.ensembl.org and
    # https://www.ensembl.org
    REST = "http://{archive}.rest.ensembl.org".format
    ARCHIVE = "https://{archive}.archive.ensembl.org".format
    DATA = "info/data"
    ASM = "info/assembly"
    # current_assembly_chain
    ASM_MAPPING = "release-{release}/assembly_chain".format
    FASTA = "release-{release}/fasta".format
    ANNOTATION = "release-{release}/{fmt}".format


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

    @staticmethod
    def get_alt_name(name):
        return name.replace("chromosome", "primary_assembly")

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

    @classmethod
    def list(cls):
        return list(map(lambda c: c.name, cls))


# Misc. e.g. charts


class IndexCacheType(Enum):
    """Caches of the index (main page), generated in the background.

    The values are the names of the commands to update them
    (``flask cache update-<value>``).
    """

    SUNBURST = "sunburst"
    AGGREGATES = "aggregates"


class SunburstChartType(Enum):
    """Sunburst charts type for the index (main page)."""

    search = "search"
    browse = "browse"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.name, cls))
