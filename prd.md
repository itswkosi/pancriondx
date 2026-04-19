PancrionDX — Product Requirements Document (PRD)
1. Product Overview
PancrionDX is a web-based AI-assisted system that analyzes genomic lab reports to estimate pancreatic ductal adenocarcinoma (PDAC) risk based on detected somatic mutations and disrupted biological pathways.
The system extracts mutation data from uploaded genomic reports, normalizes variants, maps genes to cancer-related pathways, and generates a risk score and interpretation.
The system is designed to be modular, enabling future integration of:
transcriptomic signatures
radiomic features from CT imaging
Initial deployment focuses on the genomic mutation analysis pipeline.
Target users:
patients with genomic test results
clinicians reviewing genomic panels
researchers exploring mutation patterns
2. Core Product Goals
The first version of PancrionDX should:
Accept uploaded genomic reports (PDF/text/image).
Extract mutation data using Gemini.
Normalize mutation formats.
Identify PDAC-associated genes.
Map mutations to biological pathways.
Generate a PDAC risk score.
Provide a readable interpretation of the findings.
The system should prioritize:
simplicity
speed
clean UI
future extensibility
3. System Architecture
The system is structured as a serverless AI pipeline.
User
 ↓
Next.js Frontend
 ↓
Upload API
 ↓
Document Parsing
 ↓
Mutation Extraction (Gemini)
 ↓
Mutation Normalization
 ↓
Genomic Risk Engine
 ↓
Interpretation Engine
 ↓
Results Interface
Future multimodal expansion:
Genomic Model
Transcriptomic Model
Radiomic Model
       ↓
 Multimodal Fusion Engine
       ↓
   Final Risk Score
4. Repository Architecture
GitHub repository structure:
pancriondx/

app/                      # Next.js frontend
  pages/
  components/
  styles/

api/                      # serverless endpoints
  upload/
  parse/
  extract/
  normalize/
  risk/
  explain/

core/

  ingestion/
    document_parser
    text_cleaner

  mutation_extraction/
    gemini_extractor
    extraction_schema

  mutation_processing/
    mutation_normalizer
    gene_mapper

models/

  genomic_model/
    gene_panel
    pathway_map
    risk_engine

  transcriptomic_model/   # placeholder
  radiomic_model/         # placeholder

fusion/
  multimodal_engine       # placeholder

ai/
  gemini_client
  prompt_templates
  explanation_engine

data/
  pdac_gene_panel
  pathway_definitions

tests/
Design principle:
UI layer → presentation only
Core layer → biology and mutation processing
Models layer → risk scoring
AI layer → LLM interaction
5. User Interface
Landing Page
Minimal design.
Content:
PancrionDX

AI-assisted genomic analysis
for early pancreatic cancer risk.

[ Analyze Lab Report ]
Upload Screen
Users upload genomic report.
Accepted formats:
PDF
text
image
Constraints:
maximum file size: 20MB
Mutation Extraction Preview
Detected mutations displayed to user.
Example:
Detected Mutations

KRAS G12D
TP53 R175H
RNF43 truncation
User can:
confirm mutations
edit mutations if extraction errors occur
Results Page
Outputs:
Risk Score
PDAC Risk Score: 63 / 100
Category: Moderate Risk
Mutation Summary
Detected Mutations
KRAS G12D
TP53 R175H
RNF43 truncation
Pathway Disruptions
Example:
MAPK signaling pathway disruption
Chromatin remodeling pathway alteration
Interpretation
AI-generated explanation summarizing biological implications.
Example:
Mutations affecting MAPK signaling and chromatin remodeling pathways were detected. These pathways are commonly altered during early pancreatic tumorigenesis.
Optional Detailed Analysis
User can open an expanded report explaining:
mutation roles
pathway functions
PDAC relevance
6. Data Processing Pipeline
Step 1 — Document Parsing
Extract text from uploaded report.
Purpose:
Convert PDFs or images into readable text.
Output:
clean_report_text
Step 2 — Mutation Extraction
Gemini analyzes parsed report text and extracts mutations.
Example input text:
KRAS G12D mutation detected.
TP53 R175H variant present.
RNF43 truncating mutation observed.
Output:
{
  mutations: [
    {gene: "KRAS", variant: "G12D"},
    {gene: "TP53", variant: "R175H"},
    {gene: "RNF43", variant: "truncation"}
  ]
}
Step 3 — Mutation Normalization
Normalize variant formats.
Example:
p.Gly12Asp
→
G12D
Output format:
GENE + ProteinChange
Step 4 — PDAC Gene Mapping
Detected genes are compared to a curated PDAC gene panel.
Example genes:
KRAS
TP53
SMAD4
CDKN2A
ARID1A
KMT2D
RNF43
GNAS
ATM
BRCA2
PALB2
Genes outside the panel are still recorded but weighted less heavily.
Step 5 — Pathway Mapping
Genes are grouped into biological pathways.
Example pathways:
MAPK Signaling
KRAS, BRAF
Chromatin Remodeling
ARID1A, KMT2D
DNA Repair
ATM, BRCA2, PALB2
WNT Signaling
RNF43
Cystic Neoplasm Signaling
GNAS
Output example:
disrupted_pathways = [
MAPK,
Chromatin_Remodeling
]
Step 6 — Risk Scoring
Risk score calculated from:
driver mutations
+
pathway disruptions
+
mutation combinations
Output:
risk_score = 0–100
risk_category = Low / Moderate / High
Step 7 — Interpretation
Gemini generates explanation using:
mutation list
pathway disruptions
risk score
Output:
Readable biological explanation.
7. API Endpoints
Serverless API structure:
/api/upload
/api/parse
/api/extract
/api/normalize
/api/risk
/api/explain
Each endpoint performs a single step in the pipeline.
8. Development Roadmap (Executable Chunks)
Each chunk must be completed and tested before moving forward.
Chunk 1 — Project Setup
Goal:
Create working Next.js app deployed to Vercel.
Deliverables:
landing page
analyze button
upload page
Test:
User can upload a file.
Chunk 2 — Document Parsing
Goal:
Convert uploaded report into text.
Test:
Upload PDF → display extracted text.
Chunk 3 — Mutation Extraction
Goal:
Use Gemini to extract mutations.
Test output:
KRAS G12D
TP53 R175H
Chunk 4 — Mutation Editing Interface
Goal:
Allow user to modify extracted mutations.
Test:
User edits mutation list before analysis.
Chunk 5 — Mutation Normalization
Goal:
Standardize mutation formats.
Test:
All mutations displayed consistently.
Chunk 6 — Gene Panel Detection
Goal:
Flag PDAC-associated genes.
Example output:
KRAS (PDAC-associated)
TP53 (PDAC-associated)
Chunk 7 — Pathway Mapping
Goal:
Identify disrupted biological pathways.
Test:
Mutations map to correct pathways.
Chunk 8 — Risk Engine
Goal:
Compute PDAC risk score.
Test:
Known mutation combinations produce expected scores.
Chunk 9 — Interpretation Engine
Goal:
Generate readable explanation.
Test:
Mutation set → AI explanation.
Chunk 10 — Results Interface
Goal:
Display final results cleanly.
Components:
risk score
pathway disruptions
mutation summary
explanation
Final Critique Before You Build
Your biggest potential mistake now is overusing Gemini.
Remember:
LLMs should handle:
text interpretation
explanations
They should not perform biomedical reasoning or scoring.
The risk engine must remain deterministic and transparent.
That distinction will make the difference between:
cool AI demo
and
credible scientific tool
