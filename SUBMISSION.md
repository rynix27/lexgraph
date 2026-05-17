# LexGraph — Hackathon Submission Checklist

**Hackathon:** GraphRAG Inference Hackathon by TigerGraph
**Team / Author:** [Your name]
**Submission deadline:** [Date]

---

## Required Deliverables

- [ ] **Architecture diagram** → `assets/architecture.svg` ✅
- [ ] **Comparison dashboard** → `streamlit run dashboard/app.py` ✅
- [ ] **Benchmark report** → run `python eval/generate_report.py` → `eval/benchmark_report.md`
- [ ] **Demo video** → record using `docs/demo_video_script.md`, upload to YouTube (unlisted)
- [ ] **Public GitHub repo** → push this repo, add link here: `[YOUR GITHUB URL]`
- [ ] **Blog post** → `docs/blog_post.md` → publish to Dev.to / Medium, add link: `[YOUR BLOG URL]`
- [ ] **Social media post** → `docs/social_posts.md` → post on LinkedIn + Twitter, screenshot URL
- [ ] **Product feedback interview** → only required for Top 5–10; schedule via Calendly if selected

---

## Pre-submission Steps

### 1. Fill in all placeholder links

Search the repo for `[link]`, `your-username`, `[YOUR GITHUB URL]`, `[YOUR BLOG URL]` and replace with real URLs.

Files to update:
- `README.md`
- `docs/blog_post.md`
- `docs/social_posts.md`
- `docs/demo_video_script.md`
- `SUBMISSION.md` (this file)

### 1b. Mention TigerGraph MCP in your demo video

The hackathon brief explicitly calls out MCP as a differentiator. A 30-second mention adds signal.
See: docs/MCP_SETUP.md for setup details.

### 2. Run the full benchmark

```bash
python eval/benchmark.py        # ~5 min, saves eval/results.csv
python eval/generate_report.py  # produces eval/benchmark_report.md
```

Confirm both bonus thresholds appear in the report:
- LLM-as-a-Judge pass rate ≥ 90%
- BERTScore F1 rescaled ≥ 0.55

### 3. Record the demo video

Follow `docs/demo_video_script.md`. Target 5–7 minutes.

Checklist before recording:
- [ ] Terminal font size 16+
- [ ] Browser zoom 110%
- [ ] Run one warm-up query (ChromaDB + TigerGraph cache)
- [ ] Have `eval/benchmark_report.md` open in a tab
- [ ] Notifications muted
- [ ] Resolution 1920×1080

### 4. Publish blog post

Copy `docs/blog_post.md` to Dev.to / Medium / Hashnode. Add the published URL to README and social posts.

### 5. Post on social media

Use posts from `docs/social_posts.md`. Tag @TigerGraph. Use #GraphRAGInferenceHackathon.

**Post BEFORE the deadline** — judges check social posts as part of evaluation.

Screenshot the post URL and include in your Unstop submission form.

### 6. Submit on Unstop

Upload:
1. GitHub repo URL
2. Demo video URL
3. Blog post URL
4. Social media post screenshot
5. `eval/benchmark_report.md` (the generated report)
6. `assets/architecture.svg`

---

## Submission Links (fill in)

| Deliverable | Link / Status |
|---|---|
| GitHub repo | [YOUR GITHUB URL] |
| Demo video | [YOUR VIDEO URL] |
| Blog post | [YOUR BLOG URL] |
| LinkedIn post | [YOUR LINKEDIN POST URL] |
| Twitter/X post | [YOUR TWEET URL] |

---

## Final Score Self-Assessment

| Criteria | Weight | Self-Assessment |
|---|---|---|
| Token Reduction | 30% | ~65% reduction expected |
| Answer Accuracy | 30% | ≥90% judge pass rate targeted |
| Performance | 20% | Throughput benchmark included |
| Engineering & Storytelling | 20% | Dashboard, blog, video, graph viz |
| Bonus | +extra | Both thresholds targeted |
