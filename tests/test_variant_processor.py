import sys
import os

# ensure src package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from pathlib import Path
from src.data.gene_panel_loader import GenePanelLoader
from src.scoring.mutation_weight import MutationWeightCalculator
from src.variant_processing.variant_processor import VariantProcessor, AnnotatedVariant


# dummy variant examples
json_variants = [
    {
        "gene": "BRCA1",
        "variant_id": "chr17:43044295:A:T",
        "clinvar": "pathogenic",
        "impact": "high",
        "allele_frequency": 0.0001,
    },
    {
        "gene": "FOO",
        "variant_id": "v2",
        "clinvar": "benign",
        "impact": "low",
    },
]

vcf_text = """
# example VCF
17	43044295	rs123	A	T	GENE=BRCA1;CLINVAR=pathogenic;IMPACT=high;AF=0.0001
1	1000	.	G	C	GENE=FOO;CLINVAR=pathogenic;IMPACT=low
"""


def setup_processor():
    panel_path = Path(__file__).parent.parent / "src" / "data" / "gene_panel.json"
    loader = GenePanelLoader(panel_path)
    calc = MutationWeightCalculator(loader.as_dict())
    return VariantProcessor(loader, calc)


def test_parse_json():
    proc = setup_processor()
    vars = proc.parse(json_variants)
    assert len(vars) == 2
    assert vars[0].gene == "BRCA1"


def test_parse_vcf():
    proc = setup_processor()
    vars = proc.parse(vcf_text)
    assert any(v.gene == "BRCA1" for v in vars)
    assert vars[0].allele_frequency == 0.0001


def test_parse_json_preserves_zero_af_and_consequence():
    proc = setup_processor()
    variants = proc.parse(
        [
            {
                "gene": "BRCA1",
                "variant_id": "v-zero",
                "clinvar": "pathogenic",
                "impact": "high",
                "consequence": "frameshift",
                "allele_frequency": 0.0,
            }
        ]
    )
    assert variants[0].allele_frequency == 0.0
    assert variants[0].consequence == "frameshift"


def test_filter_and_annotate():
    proc = setup_processor()
    annotated = proc.process(json_variants)
    assert isinstance(annotated[0], AnnotatedVariant)
    assert annotated[0].gene_metadata["gene_symbol"] == "BRCA1"
    # second variant not in panel gets filtered out
    assert all(v.gene == "BRCA1" for v in annotated)
    assert annotated[0].mutation_weight > 0
