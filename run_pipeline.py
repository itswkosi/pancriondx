from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, List

from src.models.variant import Variant
from src.scoring.risk_engine import calculate_risk
from src.variant_processing.variant_processor import VariantProcessor
from src.variant_processing.vcf_parser import parse_vcf
from src.data.gene_panel_loader import GenePanelLoader
from src.scoring.mutation_weight import MutationWeightCalculator


MOCK_VARIANTS = [
    {"gene": "KRAS", "mutation": "G12D"},
    {"gene": "TP53", "mutation": "R175H"},
    {"gene": "CDKN2A", "mutation": "loss"},
]


def _build_variant_processor() -> VariantProcessor:
    panel_path = Path(__file__).resolve().parent / "src" / "data" / "gene_panel.json"
    loader = GenePanelLoader(panel_path)
    weight_calc = MutationWeightCalculator(loader.as_dict())
    return VariantProcessor(loader, weight_calc)


def _mock_variants_to_models(mock_variants: Iterable[dict]) -> List[Variant]:
    variant_processor = _build_variant_processor()
    normalized = []
    for item in mock_variants:
        normalized.append(
            {
                "gene": item["gene"],
                "variant_id": f"{item['gene']}:{item['mutation']}",
                "consequence": item.get("mutation"),
            }
        )
    return variant_processor.parse(normalized)


def load_variants(vcf_path: str | None) -> List[Variant]:
    if not vcf_path:
        return _mock_variants_to_models(MOCK_VARIANTS)

    input_path = Path(vcf_path)
    if not input_path.exists():
        raise FileNotFoundError(f"VCF file not found: {vcf_path}")

    try:
        return parse_vcf(str(input_path))
    except Exception as exc:
        raise ValueError(f"Failed to parse VCF: {exc}") from exc


def print_report(total_variants: int, result: dict) -> None:
    print("=== PancrionDX Risk Report ===")
    print(f"Total Variants: {total_variants}")
    print()
    print(f"Risk Score: {result['score']:.2f}")
    print(f"Classification: {result['classification']}")
    print()
    print("Top Contributing Genes:")
    if result["top_genes"]:
        for gene in result["top_genes"]:
            print(f"- {gene}")
    else:
        print("- None")


def main() -> int:
    vcf_path = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        variants = load_variants(vcf_path)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not variants:
        print("Warning: No variants found in input.")
        return 0

    result = calculate_risk(variants)
    print_report(len(variants), result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())