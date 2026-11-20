from enum import Enum


class MockEnsembl(Enum):
    FTP = "https://ftp.ensembl.org/pub"
    # http://rest.ensembl.org
    REST = "http://{archive}.rest.ensembl.org".format
    ARCHIVE = "https://{archive}.archive.ensembl.org".format
    DATA = "info/data"
    ASM = "info/assembly"
    # current_assembly_chain
    ASM_MAPPING = "release-{release}/assembly_chain".format
    FASTA = "release-{release}/fasta".format
    ANNOTATION = "release-{release}/{fmt}".format
