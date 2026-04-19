"""
Comprehensive test suite for genomics risk scoring engine
"""
import sys
import os

# ensure src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from pathlib import Path
import pytest
from src.data.gene_panel_loader import GenePanelLoader
from src.scoring.mutation_weight import MutationWeightCalculator
from src.variant_processing.variant_processor import VariantProcessor
from src.scoring.risk_engine import RiskEngine
from src.models.variant import Variant
from fastapi.testclient import TestClient
from src.api.main import app


# ============================================================================
# FIXTURES: Synthetic variant datasets
# ============================================================================

@pytest.fixture
def gene_panel_loader():
    """Load the gene panel from JSON file."""
    panel_path = Path(__file__).parent.parent / "src" / "data" / "gene_panel.json"
    return GenePanelLoader(panel_path)


@pytest.fixture
def pathogenic_brca1_variant():
    """Pathogenic BRCA1 mutation with high impact."""
    return Variant(
        gene="BRCA1",
        variant_id="chr17:43044295:A:T",
        clinvar_classification="pathogenic",
        predicted_impact="high",
        consequence="missense",
        allele_frequency=0.0001,
    )


@pytest.fixture
def benign_variant():
    """Benign variant in panel gene."""
    return Variant(
        gene="TP53",
        variant_id="chr17:7577121:G:A",
        clinvar_classification="benign",
        predicted_impact="low",
        consequence="synonymous",
        allele_frequency=0.15,
    )


@pytest.fixture
def variant_not_in_panel():
    """Variant in gene not present in panel."""
    return Variant(
        gene="UNKNOWN_GENE",
        variant_id="chr1:12345:C:G",
        clinvar_classification="pathogenic",
        predicted_impact="high",
        allele_frequency=0.001,
    )


@pytest.fixture
def mixed_variant_dataset(pathogenic_brca1_variant, benign_variant, variant_not_in_panel):
    """Dataset containing pathogenic, benign, and non-panel variants."""
    return [pathogenic_brca1_variant, benign_variant, variant_not_in_panel]


# ============================================================================
# TEST 1: Gene Panel Loading
# ============================================================================

class TestGenePanelLoading:
    """Test suite for gene panel loading and validation."""

    def test_panel_loads_successfully(self, gene_panel_loader):
        """Verify gene panel loads without errors."""
        assert gene_panel_loader.panel is not None
        assert len(gene_panel_loader.panel.genes) > 0

    def test_panel_contains_expected_genes(self, gene_panel_loader):
        """Verify panel contains key cancer and cardio genes."""
        expected_genes = ["BRCA1", "BRCA2", "TP53", "MYH7", "APOE"]
        panel_dict = gene_panel_loader.as_dict()
        for gene in expected_genes:
            assert gene in panel_dict

    def test_gene_lookup_case_insensitive(self, gene_panel_loader):
        """Verify gene lookup is case-insensitive."""
        brca1_upper = gene_panel_loader.get_gene("BRCA1")
        brca1_lower = gene_panel_loader.get_gene("brca1")
        assert brca1_upper is not None
        assert brca1_lower is not None
        assert brca1_upper.gene_symbol == brca1_lower.gene_symbol

    def test_gene_has_required_fields(self, gene_panel_loader):
        """Verify each gene has baseline_weight and pathogenicity_multiplier."""
        brca1 = gene_panel_loader.get_gene("BRCA1")
        assert brca1.baseline_weight > 0
        assert "pathogenic" in brca1.pathogenicity_multiplier
        assert brca1.disease_association is not None

    def test_missing_gene_returns_none(self, gene_panel_loader):
        """Verify lookup of non-existent gene returns None."""
        result = gene_panel_loader.get_gene("NONEXISTENT")
        assert result is None


# ============================================================================
# TEST 2: Mutation Weight Calculation
# ============================================================================

class TestMutationWeightCalculation:
    """Test suite for mutation weight calculation logic."""

    def test_pathogenic_high_impact_weight(self, gene_panel_loader, pathogenic_brca1_variant):
        """Pathogenic BRCA1 variant should have high weight."""
        panel_map = gene_panel_loader.as_dict()
        calc = MutationWeightCalculator(panel_map)
        weight = calc.calculate(pathogenic_brca1_variant)
        # Expected: baseline 2.0 * pathogenic 5.0 * high 1.5 = 15.0
        assert weight == 15.0

    def test_benign_variant_weight(self, gene_panel_loader, benign_variant):
        """Benign variant should have zero or minimal weight."""
        panel_map = gene_panel_loader.as_dict()
        calc = MutationWeightCalculator(panel_map)
        weight = calc.calculate(benign_variant)
        # Benign multiplier is 0, so weight should be 0
        assert weight == 0.0

    def test_variant_not_in_panel_weight(self, gene_panel_loader, variant_not_in_panel):
        """Variant in non-panel gene should have zero weight."""
        panel_map = gene_panel_loader.as_dict()
        calc = MutationWeightCalculator(panel_map)
        weight = calc.calculate(variant_not_in_panel)
        assert weight == 0.0

    def test_vus_classification_weight(self, gene_panel_loader):
        """VUS (variant of uncertain significance) should have intermediate weight."""
        vus_variant = Variant(
            gene="BRCA2",
            variant_id="v1",
            clinvar_classification="vus",
            predicted_impact="moderate",
        )
        panel_map = gene_panel_loader.as_dict()
        calc = MutationWeightCalculator(panel_map)
        weight = calc.calculate(vus_variant)
        # baseline 2.0 * vus 1.5 * (moderate defaults to 1.0) = 3.0
        assert weight > 0
        assert weight < 15.0  # less than pathogenic


# ============================================================================
# TEST 3: Variant Filtering
# ============================================================================

class TestVariantFiltering:
    """Test suite for variant filtering and annotation."""

    def test_filter_removes_non_panel_variants(self, gene_panel_loader, mixed_variant_dataset):
        """Non-panel variants should be filtered out."""
        panel_map = gene_panel_loader.as_dict()
        calc = MutationWeightCalculator(panel_map)
        processor = VariantProcessor(gene_panel_loader, calc)
        annotated = processor.filter_and_annotate(mixed_variant_dataset)
        # Only BRCA1 and TP53 should remain, UNKNOWN_GENE filtered
        assert len(annotated) == 2
        assert all(v.gene in ["BRCA1", "TP53"] for v in annotated)

    def test_annotated_variants_have_weights(self, gene_panel_loader, pathogenic_brca1_variant):
        """Annotated variants should include mutation_weight field."""
        panel_map = gene_panel_loader.as_dict()
        calc = MutationWeightCalculator(panel_map)
        processor = VariantProcessor(gene_panel_loader, calc)
        annotated = processor.filter_and_annotate([pathogenic_brca1_variant])
        assert len(annotated) == 1
        assert annotated[0].mutation_weight == 15.0

    def test_annotated_variants_have_gene_metadata(self, gene_panel_loader, pathogenic_brca1_variant):
        """Annotated variants should include gene metadata."""
        panel_map = gene_panel_loader.as_dict()
        calc = MutationWeightCalculator(panel_map)
        processor = VariantProcessor(gene_panel_loader, calc)
        annotated = processor.filter_and_annotate([pathogenic_brca1_variant])
        assert annotated[0].gene_metadata["gene_symbol"] == "BRCA1"
        assert "disease_association" in annotated[0].gene_metadata

    def test_parse_json_variants(self, gene_panel_loader):
        """JSON variant input should be parsed correctly."""
        panel_map = gene_panel_loader.as_dict()
        calc = MutationWeightCalculator(panel_map)
        processor = VariantProcessor(gene_panel_loader, calc)
        json_input = [
            {
                "gene": "BRCA1",
                "variant_id": "v1",
                "clinvar": "pathogenic",
                "impact": "high",
            }
        ]
        variants = processor.parse(json_input)
        assert len(variants) == 1
        assert variants[0].gene == "BRCA1"


# ============================================================================
# TEST 4: Risk Scoring Aggregation
# ============================================================================

class TestRiskScoringAggregation:
    """Test suite for risk score calculation and classification."""

    def test_no_variants_yields_low_risk(self, gene_panel_loader):
        """Empty variant list should result in Low risk."""
        panel_map = {k: v.model_dump() for k, v in gene_panel_loader.as_dict().items()}
        engine = RiskEngine(panel_map)
        result = engine.calculate("patient1", [])
        assert result["score"] == 0.0
        assert result["risk_level"] == "Low"

    def test_single_pathogenic_variant_risk(self, gene_panel_loader, pathogenic_brca1_variant):
        """Single pathogenic BRCA1 variant should yield Elevated risk."""
        panel_map = {k: v.model_dump() for k, v in gene_panel_loader.as_dict().items()}
        engine = RiskEngine(panel_map)
        result = engine.calculate("patient2", [pathogenic_brca1_variant])
        assert result["score"] > 0
        # log(1+15) ~= 2.77 -> Elevated
        assert result["risk_level"] == "Elevated"

    def test_benign_variant_minimal_impact(self, gene_panel_loader, benign_variant):
        """Benign variant should not contribute to risk score."""
        panel_map = {k: v.model_dump() for k, v in gene_panel_loader.as_dict().items()}
        engine = RiskEngine(panel_map)
        result = engine.calculate("patient3", [benign_variant])
        assert result["score"] == 0.0
        assert result["risk_level"] == "Low"

    def test_multiple_pathogenic_variants_high_risk(self, gene_panel_loader):
        """Multiple pathogenic variants should yield High risk."""
        variants = [
            Variant(gene="BRCA1", variant_id="v1", clinvar_classification="pathogenic", consequence="frameshift"),
            Variant(gene="BRCA2", variant_id="v2", clinvar_classification="pathogenic", consequence="nonsense"),
            Variant(gene="TP53", variant_id="v3", clinvar_classification="pathogenic", consequence="missense"),
        ]
        panel_map = {k: v.model_dump() for k, v in gene_panel_loader.as_dict().items()}
        engine = RiskEngine(panel_map)
        result = engine.calculate("patient4", variants)
        assert result["score"] > 20
        assert result["risk_level"] in ["Elevated", "High"]

    def test_variant_contributions_tracked(self, gene_panel_loader, pathogenic_brca1_variant):
        """Individual variant contributions should be tracked."""
        panel_map = {k: v.model_dump() for k, v in gene_panel_loader.as_dict().items()}
        engine = RiskEngine(panel_map)
        result = engine.calculate("patient5", [pathogenic_brca1_variant])
        assert len(result["variant_contributions"]) == 1
        contrib = result["variant_contributions"][0]
        assert contrib["gene"] == "BRCA1"
        assert contrib["score"] > 0


# ============================================================================
# TEST 5: API Endpoint Response
# ============================================================================

class TestAPIEndpoint:
    """Test suite for FastAPI endpoint integration."""

    @pytest.fixture
    def client(self):
        """Create test client for FastAPI app."""
        return TestClient(app)

    def test_analyze_endpoint_success(self, client):
        """Valid request should return 200 with risk analysis."""
        payload = {
            "patient_id": "TEST001",
            "variants": [
                {
                    "gene": "BRCA1",
                    "variant_id": "chr17:43044295:A:T",
                    "clinvar": "pathogenic",
                    "impact": "high",
                    "allele_frequency": 0.0001,
                }
            ],
        }
        response = client.post("/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["patient_id"] == "TEST001"
        assert "risk_score" in data
        assert "risk_level" in data
        assert data["risk_level"] in ["Low", "Moderate", "Elevated", "High"]

    def test_analyze_endpoint_no_variants(self, client):
        """Request with empty variants should return error."""
        payload = {"patient_id": "TEST002", "variants": []}
        response = client.post("/analyze", json=payload)
        assert response.status_code == 400

    def test_analyze_endpoint_filters_non_panel_genes(self, client):
        """Non-panel variants should be filtered from results."""
        payload = {
            "patient_id": "TEST003",
            "variants": [
                {"gene": "BRCA1", "variant_id": "v1", "clinvar": "pathogenic"},
                {"gene": "FAKE_GENE", "variant_id": "v2", "clinvar": "pathogenic"},
            ],
        }
        response = client.post("/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Only BRCA1 should be analyzed
        assert len(data["variants_analyzed"]) == 1
        assert data["variants_analyzed"][0]["gene"] == "BRCA1"

    def test_analyze_endpoint_returns_interpretation(self, client):
        """Response should include interpretation text."""
        payload = {
            "patient_id": "TEST004",
            "variants": [
                {
                    "gene": "BRCA1",
                    "variant_id": "v1",
                    "clinvar": "pathogenic",
                    "impact": "high",
                }
            ],
        }
        response = client.post("/analyze", json=payload)
        data = response.json()
        assert "report_text" in data
        assert "BRCA1" in data["report_text"]
        assert "genomic risk detected" in data["report_text"].lower()

    def test_analyze_endpoint_mixed_variants(self, client):
        """Request with mixed pathogenic and benign variants."""
        payload = {
            "patient_id": "TEST005",
            "variants": [
                {"gene": "BRCA1", "variant_id": "v1", "clinvar": "pathogenic", "impact": "high"},
                {"gene": "TP53", "variant_id": "v2", "clinvar": "benign", "impact": "low"},
            ],
        }
        response = client.post("/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["risk_score"] > 0  # pathogenic BRCA1 contributes
        assert len(data["variants_analyzed"]) == 2


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
