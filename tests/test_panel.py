import sys
import os

# ensure src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from pathlib import Path

from src.data.gene_panel_loader import GenePanelLoader
from src.scoring.mutation_weight import MutationWeightCalculator
from src.models.variant import Variant


def test_gene_panel_loading():
    panel_path = Path(__file__).parent.parent / "src" / "data" / "gene_panel.json"
    loader = GenePanelLoader(panel_path)
    gene = loader.get_gene("BRCA1")
    assert gene is not None
    assert gene.disease_association.startswith("Breast")

    mapping = loader.as_dict()
    assert "BRCA1" in mapping
    assert mapping["BRCA1"].baseline_weight == 2.0


def test_mutation_weight_calculation():
    panel_path = Path(__file__).parent.parent / "src" / "data" / "gene_panel.json"
    loader = GenePanelLoader(panel_path)
    panel_map = loader.as_dict()
    calc = MutationWeightCalculator(panel_map)

    var = Variant(
        gene="BRCA1",
        variant_id="v1",
        consequence="missense_variant",
        clinvar_classification="pathogenic",
        allele_frequency=0.001,
        predicted_impact="high",
    )
    weight = calc.calculate(var)
    expected = 2.0 * 5.0 * 1.5
    assert weight == expected

    # unknown gene
    var2 = Variant(gene="FOO", variant_id="v2")
    assert calc.calculate(var2) == 0.0
