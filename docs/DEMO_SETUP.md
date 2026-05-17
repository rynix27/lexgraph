# Demo Setup Guide

## Option A: Full live demo (requires TigerGraph + OpenAI)

1. Follow README setup steps 1–4
2. Run: `streamlit run dashboard/app.py`
3. Open http://localhost:8501

## Option B: Offline demo with mock results (for recording video without live infra)

```bash
# Generate realistic mock results
python eval/mock_results.py

# Generate the benchmark report from mock data
python eval/generate_report.py

# Run dashboard — it will load mock results in the benchmark section
streamlit run dashboard/app.py
```

The mock results are seeded deterministically so they look the same every run.

## Recording tips

- Use Option B if your TigerGraph instance is cold or you want a reliable recording
- The graph traversal viz works fully offline (it's client-side D3.js)
- Entity extraction requires an OpenAI key but can be mocked by setting `MOCK_ENTITIES=true` in `.env`
- Streamlit dark mode looks better on video: Settings → Theme → Dark

## Screen layout for recording

```
┌─────────────────────────────────────────────────────┐
│  Browser: localhost:8501 (zoom 110%)                │
│  ┌─────────────────────────────────────────────────┐ │
│  │ ⚖️ LexGraph · Explainable Legal AI              │ │
│  │                                                  │ │
│  │  [Query input + Run button]                     │ │
│  │                                                  │ │
│  │  [Graph traversal animation - D3.js]            │ │
│  │                                                  │ │
│  │  [3 answer columns side by side]                │ │
│  │                                                  │ │
│  │  [Token reduction metrics]                      │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```
