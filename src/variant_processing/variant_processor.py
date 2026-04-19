from typing import List, Dict, Any, Union

from ..models.variant import Variant
from ..data.gene_panel_loader import GenePanelLoader
from ..scoring.mutation_weight import MutationWeightCalculator
from .vcf_parser import parse_vcf


class AnnotatedVariant(Variant):
    mutation_weight: float = 0.0
    gene_metadata: Dict[str, Any] = {}


class VariantProcessor:
    def __init__(self, panel_loader: GenePanelLoader, weight_calc: MutationWeightCalculator):
        self.panel_loader = panel_loader
        self.weight_calc = weight_calc

    def parse(self, input_data: Union[List[Dict[str, Any]], str]) -> List[Variant]:
        """Turn provided JSON or VCF-like data into Variant objects."""
        if isinstance(input_data, str):
            return parse_vcf(input_data)

        variants: List[Variant] = []
        for item in input_data:
            allele_frequency = item.get("allele_frequency")
            if allele_frequency is None:
                allele_frequency = item.get("af")

            data = {
                "gene": item.get("gene") or item.get("GENE"),
                "variant_id": item.get("variant_id") or item.get("id") or item.get("ID"),
                "consequence": item.get("consequence") or item.get("CONSEQUENCE") or item.get("csq") or item.get("CSQ"),
                "clinvar_classification": item.get("clinvar") or item.get("clinvar_classification"),
                "predicted_impact": item.get("impact") or item.get("predicted_impact"),
                "allele_frequency": allele_frequency,
            }
            variants.append(Variant(**{k: v for k, v in data.items() if v is not None}))
        return variants

    def filter_and_annotate(self, variants: List[Variant]) -> List[AnnotatedVariant]:
        """Keep only panel genes and attach weight + metadata."""
        annotated: List[AnnotatedVariant] = []
        panel_map = self.panel_loader.as_dict()
        for var in variants:
            gene_obj = panel_map.get(var.gene.upper())
            if not gene_obj:
                continue
            weight = self.weight_calc.calculate(var)
            annotated.append(
                AnnotatedVariant(
                    **var.model_dump(),
                    mutation_weight=weight,
                    gene_metadata=gene_obj.model_dump()
                )
            )
        return annotated

    def process(self, input_data: Union[List[Dict[str, Any]], str]) -> List[AnnotatedVariant]:
        """Convenience method performing parse + filter/annotate."""
        variants = self.parse(input_data)
        return self.filter_and_annotate(variants)
