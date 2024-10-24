from scimodom.utils.specs.enums import (
    UserState,
    Strand,
    Identifiers,
    Ensembl,
    AnnotationSource,
    AssemblyFileType,
    TargetsFileType,
    SunburstChartType,
    ImportLimits,
)


def test_user_state():
    assert UserState.wait_for_confirmation == UserState(0)
    assert UserState.active == UserState(1)
    assert len(UserState) == 2


def test_strand():
    assert Strand.FORWARD == Strand("+")
    assert Strand.REVERSE == Strand("-")
    assert Strand.UNDEFINED == Strand(".")
    assert len(Strand) == 3


def test_identifiers():
    assert Identifiers.SMID.length == 8
    assert Identifiers.EUFID.length == 12
    assert Identifiers.ASSEMBLY.length == 12
    assert len(Identifiers) == 3


def test_import_limits():
    assert ImportLimits.BED.max == 0.05
    assert ImportLimits.LIFTOVER.max == 0.3
    assert len(ImportLimits) == 2


def test_ensembl():
    CURRENT_RELEASE = 110
    assert Ensembl.RELEASE == Ensembl(CURRENT_RELEASE)
    assert Ensembl.FTP.value == "https://ftp.ensembl.org/pub"
    assert Ensembl.REST.value == "http://jul2023.rest.ensembl.org"
    assert Ensembl.ARCHIVE.value == "https://jul2023.archive.ensembl.org"
    assert Ensembl.DATA.value == "info/data"
    assert Ensembl.ASM.value == "info/assembly"
    assert Ensembl.ASM_MAPPING.value == f"release-{CURRENT_RELEASE}/assembly_chain"


def test_annotation_source():
    assert AnnotationSource.ENSEMBL == AnnotationSource("ensembl")
    assert AnnotationSource.GTRNADB == AnnotationSource("gtrnadb")
    assert len(AnnotationSource) == 2


def test_assembly_file_type():
    assert AssemblyFileType.CHROM == AssemblyFileType("chrom.sizes")
    assert AssemblyFileType.INFO == AssemblyFileType("info.json")
    assert AssemblyFileType.RELEASE == AssemblyFileType("release.json")
    assert AssemblyFileType.CHAIN == AssemblyFileType("__CHAIN__")
    assert (
        AssemblyFileType.DNA.value(
            organism="organism", assembly="assembly", chrom="chrom"
        )
        == "organism.assembly.dna.chromosome.chrom.fa.gz"
    )
    assert len(AssemblyFileType) == 5


def test_targets_fie_type():
    assert TargetsFileType.MIRNA.value("any") == "mirna.bed"
    assert TargetsFileType.RBP.value(chrom="chrom") == "rbp_chrom.bed"
    assert len(TargetsFileType) == 2


def test_sunburst_chart_type():
    assert SunburstChartType.search == SunburstChartType("search")
    assert SunburstChartType.browse == SunburstChartType("browse")
    assert len(SunburstChartType) == 2
