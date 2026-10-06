# QuoteLens — Gemini deployment

1. Create a Gemini API key in Google AI Studio.
2. Push this folder to GitHub. Keep `requirements.txt` at repository root and `app/app.py` as the entrypoint.
3. In Streamlit Community Cloud create a new app from that repository.
4. Main file path: `app/app.py`.
5. In **App settings → Secrets**, add:

```toml
GEMINI_API_KEY = "your-key-here"
```

6. Save secrets/reboot the app. The sidebar should show **Gemini connected**.
7. Upload the five files from `sample_vendor_responses/` and click **Extract & normalize**.
8. Validate the Comparison tab, then ask a new question in Analyst to demonstrate that reasoning is live rather than hardcoded.

Security: never place the key in app.py, README, GitHub, screenshots, or the recorded walkthrough.
