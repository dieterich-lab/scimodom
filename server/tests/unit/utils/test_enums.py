from scimodom.utils.specs.enums import (
    UserState,
    Strand,
    AnnotationSource,
    AssemblyFileType,
    TargetsFileType,
    SunburstChartType,
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
