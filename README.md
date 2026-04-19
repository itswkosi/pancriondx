# PancrionDX Clinical Decision Support

This repository implements a genomics clinical decision support system.

## Structure

```
/src
  /models
  /data
  /variant_processing
  /scoring
  /interpretation
  /api
/tests
```

## Getting Started

1. Create virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Run the API:
   ```bash
   uvicorn src.api.main:app --reload
   ```
3. Run the CLI pipeline:
   ```bash
   python run_pipeline.py sample.vcf
   ```
   Omit the VCF path to use the built-in mock variants.
4. Run tests (ensure `src` directory is on PYTHONPATH):
   ```bash
   PYTHONPATH=src pytest
   ```
