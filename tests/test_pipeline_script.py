from run_pipeline import load_variants, main
from src.scoring.risk_engine import calculate_risk


def test_load_variants_fallback():
    variants = load_variants(None)
    assert len(variants) == 3
    assert {variant.gene for variant in variants} == {"KRAS", "TP53", "CDKN2A"}



def test_calculate_risk_cli_shape():
    variants = load_variants(None)
    result = calculate_risk(variants)
    assert set(result) == {"score", "classification", "top_genes"}
    assert result["classification"] in {"Early-stage likely", "Late-stage likely"}
    assert isinstance(result["top_genes"], list)
