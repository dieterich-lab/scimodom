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
    release = 110
    archive = "jul2023"
    assert Ensembl.FTP.value == "https://ftp.ensembl.org/pub"
    assert Ensembl.REST.value(archive=archive) == "http://jul2023.rest.ensembl.org"
    assert (
        Ensembl.ARCHIVE.value(archive=archive) == "https://jul2023.archive.ensembl.org"
    )
    assert Ensembl.DATA.value == "info/data"
    assert Ensembl.ASM.value == "info/assembly"
    assert (
        Ensembl.ASM_MAPPING.value(release=release)
        == f"release-{release}/assembly_chain"
    )
    assert Ensembl.FASTA.value(release=release) == f"release-{release}/fasta"
    assert (
        Ensembl.ANNOTATION.value(release=release, fmt="gtf") == f"release-{release}/gtf"
    )
    assert len(Ensembl) == 8


def test_annotation_source():
    assert AnnotationSource.ENSEMBL == AnnotationSource("ensembl")
    assert AnnotationSource.GTRNADB == AnnotationSource("gtrnadb")
    assert len(AnnotationSource) == 2


def test_assembly_file_type():
    assert AssemblyFileType.MANIFEST == AssemblyFileType("manifest.json")
    assert AssemblyFileType.INFO == AssemblyFileType("info.json")
    assert AssemblyFileType.RELEASE == AssemblyFileType("release.json")
    assert AssemblyFileType.CHROM == AssemblyFileType("chrom.sizes")
    assert (
        AssemblyFileType.CHAIN.value(source_assembly="source", target_assembly="target")
        == "source_to_target.chain.gz"
    )
    assert (
        AssemblyFileType.DNA.value(
            organism="organism", assembly="assembly", chrom="chrom"
        )
        == "organism.assembly.dna.chromosome.chrom.fa.gz"
    )
    assert (
        AssemblyFileType.get_alt_name(
            AssemblyFileType.DNA.value(
                organism="organism", assembly="assembly", chrom="chrom"
            )
        )
        == "organism.assembly.dna.primary_assembly.chrom.fa.gz"
    )
    assert (
        AssemblyFileType.DNA_IDX.value(
            organism="organism", assembly="assembly", chrom="chrom"
        )
        == "organism.assembly.dna.chromosome.chrom.fa.gz.fai"
    )
    assert (
        AssemblyFileType.DNA_BGZ.value(
            organism="organism", assembly="assembly", chrom="chrom"
        )
        == "organism.assembly.dna.chromosome.chrom.fa.gz.gzi"
    )
    assert AssemblyFileType.common() == (
        AssemblyFileType.MANIFEST,
        AssemblyFileType.CHROM,
    )
    assert AssemblyFileType.legacy() == (
        AssemblyFileType.INFO,
        AssemblyFileType.RELEASE,
    )
    assert AssemblyFileType.fasta() == (
        AssemblyFileType.DNA,
        AssemblyFileType.DNA_IDX,
        AssemblyFileType.DNA_BGZ,
    )
    assert AssemblyFileType.is_chain(AssemblyFileType.CHAIN) is True
    assert AssemblyFileType.is_chain("test") is False
    assert AssemblyFileType.is_fasta(AssemblyFileType.DNA) is True
    assert AssemblyFileType.is_fasta(AssemblyFileType.DNA_IDX) is True
    assert AssemblyFileType.is_fasta(AssemblyFileType.DNA_BGZ) is True
    assert AssemblyFileType.is_fasta("test") is False
    assert len(AssemblyFileType) == 8


def test_targets_fie_type():
    assert TargetsFileType.MIRNA.value("any") == "mirna.bed"
    assert TargetsFileType.RBP.value(chrom="chrom") == "rbp_chrom.bed"
    assert len(TargetsFileType) == 2


def test_sunburst_chart_type():
    assert SunburstChartType.search == SunburstChartType("search")
    assert SunburstChartType.browse == SunburstChartType("browse")
    assert len(SunburstChartType) == 2
