# QuoteLens — Aerchain Product Take-Home

A working prototype for the brief: AI-assisted RFx drafting, heterogeneous vendor response extraction, normalization, comparison, and natural-language procurement analysis.

## Run
```bash
python -m venv .venv
pip install -r requirements.txt
streamlit run app/app.py
```
Create a Gemini API key in Google AI Studio, then add `GEMINI_API_KEY` as an environment variable locally or as a Streamlit Secret when deployed. The app does not ask for the key in the UI.

## Demo data
Five intentionally messy responses are included under `sample_vendor_responses/`: Excel, Word, PDF, photographed rate card, and email/text.

## Deployment
Deploy this repository to Streamlit Community Cloud or another Streamlit host and add `GEMINI_API_KEY` as a secret. The resulting app URL is the live link/hosting link.

## Trust decisions
Missing is not zero; currency is preserved; quality eligibility is separate; extraction confidence/evidence is retained; analyst answers are instructed to surface assumptions.

## Deliberately stubbed/out of scope
SMTP/vendor portal, production auth/RBAC/audit, live FX, and production-grade OCR evaluation.


## Streamlit secret
In Community Cloud → App settings → Secrets, add:
```toml
GEMINI_API_KEY = "paste-your-key-here"
```
Do not commit the key to GitHub.
