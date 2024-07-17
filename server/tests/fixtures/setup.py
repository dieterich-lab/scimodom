import pytest

from scimodom.database.models import (
    RNAType,
    Modomics,
    Taxonomy,
    Taxa,
    Assembly,
    AssemblyVersion,
    Annotation,
    AnnotationVersion,
    DetectionMethod,
)


@pytest.fixture()
def setup():
    add = []
    rna_types = [RNAType(id="WTS", name="whole transcriptome")]
    add.extend(rna_types)
    modomics = [
        Modomics(
            id="2000000006A",
            name="N6-methyladenosine",
            short_name="m6A",
            moiety="nucleoside",
            reference_id=96,
        ),
        Modomics(
            id="2000000005C",
            name="5-methylcytidine",
            short_name="m5C",
            moiety="nucleoside",
            reference_id=18,
        ),
        Modomics(
            id="2000000009U",
            name="pseudouridine",
            short_name="Y",
            moiety="nucleoside",
            reference_id=118,
        ),
    ]
    add.extend(modomics)
    taxonomy = [
        Taxonomy(
            id="a1b240af", domain="Eukarya", kingdom="Animalia", phylum="Chordata"
        ),
        Taxonomy(
            id="455a3823", domain="Eukarya", kingdom="Animalia", phylum="Arthropoda"
        ),
    ]
    add.extend(taxonomy)
    taxa = [
        Taxa(
            id=9606,
            name="Homo sapiens",
            short_name="H. sapiens",
            taxonomy_id="a1b240af",
        ),
        Taxa(
            id=10090,
            name="Mus musculus",
            short_name="M. musculus",
            taxonomy_id="a1b240af",
        ),
        Taxa(
            id=7227,
            name="Drosophila melanogaster",
            short_name="D. melanogaster",
            taxonomy_id="455a3823",
        ),
    ]
    add.extend(taxa)
    assembly_version = [
        AssemblyVersion(version_num="GcatSmFcytpU"),
    ]
    add.extend(assembly_version)
    assembly = [
        Assembly(name="GRCh38", alt_name="hg38", taxa_id=9606, version="GcatSmFcytpU"),
        Assembly(name="GRCm38", alt_name="mm10", taxa_id=10090, version="GcatSmFcytpU"),
        Assembly(name="GRCh37", alt_name="hg19", taxa_id=9606, version="J9dit7Tfc6Sb"),
    ]
    add.extend(assembly)
    annotation_version = [
        AnnotationVersion(version_num="EyRBnPeVwbzW"),
    ]
    add.extend(annotation_version)
    annotation = [
        Annotation(release=110, taxa_id=9606, source="ensembl", version="EyRBnPeVwbzW"),
        Annotation(
            release=110, taxa_id=10090, source="ensembl", version="EyRBnPeVwbzW"
        ),
        Annotation(release=109, taxa_id=9606, source="ensembl", version="A8syx5TzWlK0"),
    ]
    add.extend(annotation)
    method = [
        DetectionMethod(
            id="0ee048bc", cls="NGS 2nd generation", meth="Chemical-assisted sequencing"
        ),
        DetectionMethod(
            id="91b145ea", cls="NGS 2nd generation", meth="Antibody-based sequencing"
        ),
        DetectionMethod(
            id="01d26feb",
            cls="NGS 2nd generation",
            meth="Enzyme/protein-assisted sequencing",
        ),
    ]
    add.extend(method)
    return add
