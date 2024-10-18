from enum import Enum


class MockEnsembl(Enum):
    RELEASE = 110
    FTP = "https://ftp.ensembl.org/pub"
    # http://rest.ensembl.org
    REST = "http://jul2023.rest.ensembl.org"
    ARCHIVE = "https://jul2023.archive.ensembl.org"
    DATA = "info/data"
    ASM = "info/assembly"
    # current_assembly_chain
    ASM_MAPPING = f"release-{RELEASE}/assembly_chain"
