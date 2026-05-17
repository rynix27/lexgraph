"""
LexGraph — Explainable Legal AI Dashboard
Run: streamlit run dashboard/app.py
Works out of the box with mock data. Set LIVE_MODE=true in .env for real pipelines.
"""

import sys, os, time, random
from pathlib import Path
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

LIVE_MODE = os.environ.get("LIVE_MODE", "false").lower() == "true"

st.set_page_config(
    page_title="LexGraph · Explainable Legal AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.big-metric   { font-size:36px; font-weight:700; line-height:1; }
.metric-label { font-size:12px; color:#888; margin-top:2px; }
.pill { display:inline-block; padding:2px 10px; border-radius:12px; font-size:12px; font-weight:500; margin:2px; }
.pill-article { background:#EEEDFE; color:#3C3489; }
.pill-case    { background:#E1F5EE; color:#085041; }
.pill-concept { background:#FAEEDA; color:#633806; }
.pill-act     { background:#FAECE7; color:#712B13; }
.pill-judge   { background:#E6F1FB; color:#0C447C; }
.winner-badge { background:#1D9E75; color:white; padding:3px 10px; border-radius:20px; font-weight:600; font-size:12px; }
.answer-box   { border-radius:10px; padding:16px; border:1px solid #333; min-height:200px; font-size:14px; line-height:1.75; }
.graphrag-box { border:2px solid #1D9E75 !important; }
</style>
""", unsafe_allow_html=True)

# ── mock data ─────────────────────────────────────────────────────────────────

EXAMPLE_QUERIES = [
    "Which judges consistently expanded Article 21 rights and which cases established those precedents?",
    "Which acts have been challenged most frequently under Article 14 in the Supreme Court?",
    "What is the basic structure doctrine and which cases applied it to strike down constitutional amendments?",
    "How has the right to privacy evolved from the 1950s to the Puttaswamy judgment?",
    "How has proportionality been applied in fundamental rights cases after 2017?",
]

MOCK_ANSWERS = {
    "llm_only": [
        "Article 21 guarantees the right to life and personal liberty. Several Supreme Court judges expanded its scope over the decades through landmark rulings, though I cannot cite specific cases without access to a retrieval system. The right has been interpreted to include dignity, livelihood, health, and education among other facets.",
        "Article 14 guarantees equality before law and equal protection. Acts frequently challenged under it include anti-terror legislation, money laundering statutes, and land acquisition laws. Courts apply the non-arbitrariness doctrine to evaluate such challenges.",
        "The basic structure doctrine holds that Parliament cannot amend the Constitution to destroy its essential features. It emerged from a landmark 1973 thirteen-judge bench decision and has since been applied to strike down several constitutional amendments.",
        "Privacy was initially not recognized as a fundamental right by the Supreme Court. However, a landmark 2017 nine-judge bench decision unanimously reversed this position, holding privacy to be intrinsic to life and liberty under Article 21.",
        "Proportionality as a constitutional test requires that state action be suitable, necessary, and balanced. Indian courts have adopted this framework increasingly in fundamental rights cases, particularly those involving surveillance and speech restrictions.",
    ],
    "basic_rag": [
        "Retrieved chunks (ILDC corpus): Justice P.N. Bhagwati and Justice V.R. Krishna Iyer expanded Article 21 through multiple judgments. Maneka Gandhi v. Union of India (1978) held that procedure under Article 21 must be fair, just and reasonable, overruling A.K. Gopalan. Francis Coralie Mullin (1981) extended this to include the right to live with human dignity. These form the foundational precedents for the expansive Article 21 interpretation applied today.",
        "Retrieved cases show: PMLA (2002) — 47 cases challenging Article 14; AFSPA (1958) — 31 cases; Land Acquisition Act — 28 cases; UAPA — 19 cases. The Article 14 non-arbitrariness doctrine from E.P. Royappa v. State of Tamil Nadu (1974) is the primary framework applied in these challenges. Nikesh Tarachand Shah v. Union of India (2017) struck down PMLA Section 45 as violating Article 14.",
        "Kesavananda Bharati v. State of Kerala (1973) by a 13-judge bench established the basic structure doctrine. Subsequent cases: Indira Nehru Gandhi v. Raj Narain (1975) struck down Article 329A; Minerva Mills v. Union of India (1980) invalidated 42nd Amendment clauses; I.R. Coelho v. State of Tamil Nadu (2007) extended it to the 9th Schedule. The doctrine is now firmly embedded in Indian constitutionalism.",
        "M.P. Sharma (1954) and Kharak Singh (1963) held privacy was not a fundamental right. Gobind v. State of M.P. (1975) recognised a limited implied right. R. Rajagopal (1994) extended it to personal records. K.S. Puttaswamy v. Union of India (2017) — nine-judge bench, unanimous — overruled the earlier cases and held privacy is an intrinsic part of Article 21.",
        "Post-Puttaswamy cases: Anuradha Bhasin v. Union of India (2020) applied proportionality to internet shutdowns and held blanket shutdowns fail the necessity test. Vijay Madanlal Choudhary v. Union of India (2022) tested PMLA powers — survived on 3 of 4 proportionality limbs. Common Cause (2018) upheld passive euthanasia. Shafin Jahan (2018) protected right to choose a partner.",
    ],
    "graphrag": [
        "**Graph traversal: Article 21 → Judge nodes → Case nodes → Citation edges**\n\n**Justice P.N. Bhagwati** (23 Article 21 judgments):\n→ *Maneka Gandhi v. Union of India* (1978) — procedure must be fair, just, reasonable\n→ *Sunil Batra v. Delhi Administration* (1978) — prison conditions under Article 21\n→ *Francis Coralie Mullin* (1981) — right to live with dignity\n\n**Justice V.R. Krishna Iyer** (18 Article 21 judgments):\n→ *Hussainara Khatoon v. State of Bihar* (1979) — speedy trial as Article 21 right\n→ *Babu Singh v. State of UP* (1978) — bail and personal liberty\n\n**Multi-hop finding**: These two judges cited each other across 11 cases (1975–1984), creating a reinforcing precedent network. Citation chain: Maneka Gandhi → Sunil Batra → Francis Coralie → Olga Tellis (livelihood, 1985) → Unni Krishnan (education, 1993).\n\n**Token efficiency**: GraphRAG retrieved 6 targeted nodes vs Basic RAG's 38 chunks.",
        "**Graph traversal: Article 14 → Act nodes → Case count aggregation**\n\n**Top challenged acts (graph aggregation):**\n1. **PMLA 2002** — 47 Article 14 cases; Nikesh Tarachand Shah (2017) struck down S.45\n2. **AFSPA 1958** — 31 cases; Extra Judicial Execution Victim Families (2016) landmark\n3. **Land Acquisition Act 1894/2013** — 28 cases; equal protection in compensation\n4. **UAPA 1967** — 19 cases; bail denial arbitrariness challenges\n5. **Forest Rights Act 2006** — 12 cases; tribal equality claims\n\n**Graph-exclusive insight**: PMLA is uniquely challenged under both Article 14 (equal treatment of accused) AND Article 21 (bail restrictions) — the only statute in the corpus with dual fundamental rights challenges in >40 cases.\n\n**Token efficiency**: 1,380 prompt tokens vs Basic RAG's 4,350 — **68% reduction**.",
        "**Graph traversal: Kesavananda Bharati → cites → downstream cases → constitutional_amendment edges**\n\n**Origin**: *Kesavananda Bharati v. State of Kerala* (1973) — 13-judge bench, 7:6.\n\n**Amendment cases citing Kesavananda (graph traversal result):**\n• *Indira Nehru Gandhi v. Raj Narain* (1975) → struck down Art. 329A\n• *Minerva Mills v. Union of India* (1980) → struck down 42nd Amendment, clauses 4 & 55\n• *Waman Rao v. Union of India* (1981) → clarified doctrine applies to all post-1973 amendments\n• *S.P. Sampath Kumar v. Union of India* (1987) → extended to tribunal legislation\n• *I.R. Coelho v. State of Tamil Nadu* (2007) → 9-judge bench, extended to 9th Schedule\n\n**Graph-exclusive finding**: Kesavananda appears in 340+ judgments — most-cited case in the 70k ILDC corpus. Second is Maneka Gandhi (287 citations).",
        "**Graph traversal: Privacy concept → citation chain → temporal filter**\n\n**Full citation chain (reconstructed from graph edges):**\n1. *M.P. Sharma v. Satish Chandra* (1954) — 8-judge bench: no privacy right\n2. *Kharak Singh v. State of U.P.* (1963) — 6-judge bench: reaffirmed\n3. *Gobind v. State of M.P.* (1975) — Justice Mathew: limited implied right\n4. *R. Rajagopal v. State of TN* (1994) — privacy in public records\n5. *K.S. Puttaswamy v. Union of India* (2017) — **9-judge bench, unanimous** → overruled M.P. Sharma and Kharak Singh\n\n**Post-2017 applications (2-hop from Puttaswamy):**\n• *Anuradha Bhasin* (2020) — internet + privacy\n• *Puttaswamy (Aadhaar)* (2018) — data privacy, S.57 struck down\n• *Common Cause* (2018) — right to die with dignity\n\n**Token efficiency**: 6 graph nodes retrieved vs 42 RAG chunks — **67% token reduction**.",
        "**Graph traversal: Puttaswamy → cites → cases[year>2017] → Articles[19,21]**\n\n**4-part proportionality test applied post-2017:**\n\n**1. Legality** — does law exist? **2. Legitimate aim** — valid state interest? **3. Necessity** — least restrictive means? **4. Proportionality stricto sensu** — balance of harm?\n\n**Cases (graph traversal):**\n• *Anuradha Bhasin v. UoI* (2020): Internet shutdown — **FAILED necessity** (blanket ban not least restrictive)\n• *Vijay Madanlal Choudhary v. UoI* (2022): PMLA — passed 3/4 limbs, twin conditions upheld\n• *Common Cause v. UoI* (2018): Passive euthanasia — state interest does not override autonomy absolutely\n• *Shafin Jahan v. Asokan* (2018): Right to choose partner — family court surveillance fails proportionality\n• *Puttaswamy (Aadhaar)* (2018): S.57 struck down — private entities cannot invoke Aadhaar\n\n**Graph insight**: Proportionality applied in 91% of post-2017 Article 19/21 cases in corpus.",
    ],
}

MOCK_ENTITIES = [
    {"articles": ["21", "14", "19"], "cases": ["Maneka Gandhi v. UoI", "Francis Coralie Mullin", "Sunil Batra v. Delhi Admin"], "acts": ["Constitution of India"], "concepts": ["personal liberty", "due process", "human dignity"], "judges": ["Justice P.N. Bhagwati", "Justice V.R. Krishna Iyer"]},
    {"articles": ["14"], "cases": ["Nikesh Tarachand Shah v. UoI", "E.P. Royappa v. State of TN", "Extra Judicial Execution Victim Families"], "acts": ["PMLA 2002", "AFSPA 1958", "Land Acquisition Act"], "concepts": ["non-arbitrariness", "equal protection"], "judges": []},
    {"articles": ["368", "13"], "cases": ["Kesavananda Bharati v. State of Kerala", "Minerva Mills v. UoI", "I.R. Coelho v. State of TN"], "acts": ["42nd Amendment", "9th Schedule"], "concepts": ["basic structure", "constituent power", "implied limitations"], "judges": ["Chief Justice S.M. Sikri"]},
    {"articles": ["21"], "cases": ["K.S. Puttaswamy v. UoI", "M.P. Sharma v. Satish Chandra", "Kharak Singh v. State of UP", "Gobind v. State of MP"], "acts": ["Aadhaar Act 2016", "IT Act 2000"], "concepts": ["right to privacy", "informational self-determination"], "judges": ["Justice D.Y. Chandrachud", "Justice Chelameswar"]},
    {"articles": ["19", "21"], "cases": ["Anuradha Bhasin v. UoI", "Vijay Madanlal Choudhary v. UoI", "Shafin Jahan v. Asokan"], "acts": ["PMLA", "IT Act", "UAPA"], "concepts": ["proportionality", "necessity test", "legitimate aim", "stricto sensu"], "judges": ["Justice N.V. Ramana", "Justice D.Y. Chandrachud"]},
]

PIPELINE_TOKENS = {
    "llm_only":  {"prompt": 310, "completion": 265},
    "basic_rag": {"prompt": 4350, "completion": 390},
    "graphrag":  {"prompt": 1380, "completion": 355},
}
PIPELINE_LATENCY = {"llm_only": 1.2, "basic_rag": 2.6, "graphrag": 1.8}
PRICE_IN, PRICE_OUT = 0.075 / 1e6, 0.30 / 1e6

PIPELINE_META = {
    "llm_only":  {"label": "LLM Only",  "icon": "🤖"},
    "basic_rag": {"label": "Basic RAG", "icon": "🔍"},
    "graphrag":  {"label": "GraphRAG",  "icon": "🕸️"},
}

# ── session state init ────────────────────────────────────────────────────────
if "history"      not in st.session_state: st.session_state.history      = []
if "last_results" not in st.session_state: st.session_state.last_results = None
if "last_query"   not in st.session_state: st.session_state.last_query   = ""

def get_mock_result(pipeline: str, query: str, idx: int) -> dict:
    rng   = random.Random(hash(query + pipeline) & 0xFFFFFF)
    p_tok = PIPELINE_TOKENS[pipeline]["prompt"]     + rng.randint(-60, 120)
    c_tok = PIPELINE_TOKENS[pipeline]["completion"] + rng.randint(-30, 50)
    lat   = max(0.4, PIPELINE_LATENCY[pipeline] + rng.gauss(0, 0.25))
    return {
        "pipeline":      pipeline,
        "answer":        MOCK_ANSWERS[pipeline][idx % 5],
        "total_tokens":  p_tok + c_tok,
        "prompt_tokens": p_tok,
        "completion_tokens": c_tok,
        "latency_s":     round(lat, 2),
        "cost_usd":      round(p_tok * PRICE_IN + c_tok * PRICE_OUT, 6),
        "context_used":  "(graph traversal context)" if pipeline == "graphrag" else "(top-5 semantic chunks)",
        "entities":      MOCK_ENTITIES[idx % 5] if pipeline == "graphrag" else {},
        "traversal_hops": ["Article 21", "Case: Maneka Gandhi", "Case: Francis Coralie", "Judge: P.N. Bhagwati"] if pipeline == "graphrag" else [],
    }

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚖️ LexGraph")
    st.markdown("*GraphRAG Inference Hackathon · TigerGraph*")
    st.divider()
    st.info("🎭 **Demo mode** — realistic mock data\n\nSet `LIVE_MODE=true` in `.env` for real pipelines.")
    st.markdown("GraphRAG traverses a knowledge graph of **cases → articles → judges → citations** instead of dumping similar chunks. Fewer tokens, traceable reasoning.")
    st.divider()
    st.markdown("**Dataset:** OpenNyai ILDC · 70k SC judgments")
    st.markdown("**Graph:** TigerGraph · multi-hop traversal")
    st.markdown("**Eval:** BERTScore + LLM-as-a-Judge")
    st.divider()
    show_entities = st.toggle("Show extracted entities", True)
    show_graph    = st.toggle("Show graph traversal",   True)
    show_context  = st.toggle("Show retrieved context", False)
    st.divider()
    if st.session_state.history:
        df_h = pd.DataFrame(st.session_state.history)
        st.markdown("**Session summary**")
        st.markdown(f"Avg token reduction: **{df_h['reduction_pct'].mean():.1f}%**")
        st.markdown(f"Queries run: **{len(df_h)}**")

# ── header ────────────────────────────────────────────────────────────────────
st.title("⚖️ LexGraph · Explainable Legal AI")
st.caption("Graph-powered retrieval that reduces token cost while preserving constitutional accuracy — Indian Supreme Court judgments.")

if st.session_state.history:
    df_h = pd.DataFrame(st.session_state.history)
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Avg token reduction",  f"{df_h['reduction_pct'].mean():.1f}%")
    s2.metric("Avg Basic RAG tokens", f"{df_h['rag_tokens'].mean():,.0f}")
    s3.metric("Avg GraphRAG tokens",  f"{df_h['graph_tokens'].mean():,.0f}")
    s4.metric("Queries run",          len(df_h))
    st.divider()

# ── query input ───────────────────────────────────────────────────────────────
st.markdown("### Ask a legal question")
example = st.selectbox("Pick an example", ["(type your own below)"] + EXAMPLE_QUERIES,
                        label_visibility="collapsed")
answer_idx = EXAMPLE_QUERIES.index(example) if example in EXAMPLE_QUERIES else 0

query = st.text_area(
    "Question",
    value="" if example == "(type your own below)" else example,
    height=80,
    placeholder="e.g. Which judges expanded Article 21 rights and which cases established the precedents?",
    label_visibility="collapsed",
)

run_btn = st.button("▶ Run all 3 pipelines", type="primary")

# ── run pipelines ─────────────────────────────────────────────────────────────
if run_btn and query.strip():
    with st.spinner("Running all 3 pipelines..."):
        time.sleep(1.4)   # realistic feel
        results = {p: get_mock_result(p, query, answer_idx) for p in PIPELINE_META}

    # Store in session state so results survive reruns
    st.session_state.last_results = results
    st.session_state.last_query   = query

    rag_tok   = results["basic_rag"]["total_tokens"]
    graph_tok = results["graphrag"]["total_tokens"]
    reduction = (rag_tok - graph_tok) / max(rag_tok, 1) * 100

    st.session_state.history.append({
        "query":         query[:55] + "…",
        "llm_tokens":    results["llm_only"]["total_tokens"],
        "rag_tokens":    rag_tok,
        "graph_tokens":  graph_tok,
        "reduction_pct": round(reduction, 1),
        "graph_cost":    round(results["graphrag"]["cost_usd"], 6),
        "rag_cost":      round(results["basic_rag"]["cost_usd"], 6),
        "graph_latency": round(results["graphrag"]["latency_s"], 2),
        "rag_latency":   round(results["basic_rag"]["latency_s"], 2),
    })

# ── display results ───────────────────────────────────────────────────────────
if st.session_state.last_results:
    results = st.session_state.last_results
    gr      = results["graphrag"]

    # Entity pills
    if show_entities and gr.get("entities"):
        ents  = gr["entities"]
        pills = "<div style='margin:14px 0 8px'><b style='font-size:13px'>Extracted entities: </b>"
        for a in ents.get("articles", []):
            pills += f'<span class="pill pill-article">Art. {a}</span>'
        for c in ents.get("cases", [])[:4]:
            pills += f'<span class="pill pill-case">{c[:32]}</span>'
        for act in ents.get("acts", [])[:3]:
            pills += f'<span class="pill pill-act">{act[:30]}</span>'
        for co in ents.get("concepts", [])[:3]:
            pills += f'<span class="pill pill-concept">{co[:28]}</span>'
        for j in ents.get("judges", [])[:2]:
            pills += f'<span class="pill pill-judge">{j[:24]}</span>'
        pills += "</div>"
        st.markdown(pills, unsafe_allow_html=True)

    # Graph viz
    if show_graph and gr.get("entities"):
        from dashboard.graph_viz import render_graph_html
        st.markdown("#### 🕸️ Graph traversal")
        st.caption("Nodes light up as GraphRAG traverses: query → entities → cases → precedents. Drag nodes to explore.")
        components.html(render_graph_html(st.session_state.last_query, gr["entities"]), height=490, scrolling=False)

    # Side-by-side answers
    st.markdown("#### Side-by-side answers")
    cols = st.columns(3)
    for i, (p_name, meta) in enumerate(PIPELINE_META.items()):
        r = results[p_name]
        with cols[i]:
            if p_name == "graphrag":
                st.markdown(f"**{meta['icon']} {meta['label']}** <span class='winner-badge'>graph-powered ✓</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"**{meta['icon']} {meta['label']}**")

            box_cls = "answer-box graphrag-box" if p_name == "graphrag" else "answer-box"
            content = r["answer"].replace("\n", "<br>")
            st.markdown(f"<div class='{box_cls}'>{content}</div>", unsafe_allow_html=True)
            st.markdown("")
            m1, m2 = st.columns(2)
            m1.metric("Tokens",  f"{r['total_tokens']:,}")
            m2.metric("Latency", f"{r['latency_s']:.1f}s")
            st.metric("Cost (USD)", f"${r['cost_usd']:.5f}")
            if show_context:
                with st.expander("Context"):
                    st.text(r.get("context_used", "—"))

    # Summary metrics
    st.divider()
    llm_tok   = results["llm_only"]["total_tokens"]
    rag_tok   = results["basic_rag"]["total_tokens"]
    graph_tok = results["graphrag"]["total_tokens"]
    reduction = (rag_tok - graph_tok) / max(rag_tok, 1) * 100
    cost_saved = results["basic_rag"]["cost_usd"] - results["graphrag"]["cost_usd"]

    r1, r2, r3 = st.columns(3)
    for col, val, label, color in [
        (r1, f"{reduction:.1f}%",      "token reduction vs Basic RAG", "#1D9E75"),
        (r2, f"{rag_tok-graph_tok:,}", "tokens saved this query",      "#378ADD"),
        (r3, f"${cost_saved:.5f}",     "cost saved this query",        "#BA7517"),
    ]:
        col.markdown(
            f"<div style='text-align:center;padding:18px;background:rgba(255,255,255,0.05);"
            f"border-radius:10px;border:1px solid #333'>"
            f"<div class='big-metric' style='color:{color}'>{val}</div>"
            f"<div class='metric-label'>{label}</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.bar_chart(
        pd.DataFrame({"Tokens": [llm_tok, rag_tok, graph_tok]},
                     index=["LLM Only", "Basic RAG", "GraphRAG"]),
        color="#1D9E75",
    )

# ── session history ───────────────────────────────────────────────────────────
if st.session_state.history:
    st.divider()
    with st.expander("📊 Session history", expanded=False):
        df_h = pd.DataFrame(st.session_state.history)
        st.dataframe(df_h, use_container_width=True)
        st.download_button("Export CSV", df_h.to_csv(index=False),
                           "lexgraph_session.csv", "text/csv")

# ── full benchmark ────────────────────────────────────────────────────────────
st.divider()
with st.expander("📈 Full 10-query benchmark (BERTScore + LLM-as-a-Judge)"):
    if st.button("Load mock benchmark results"):
        from eval.queries import QUERIES
        rows = []
        rng2 = random.Random(42)
        BERT = {
            "llm_only":  {"rescaled": 0.41, "raw": 0.882, "pass": 0.40},
            "basic_rag": {"rescaled": 0.58, "raw": 0.894, "pass": 0.70},
            "graphrag":  {"rescaled": 0.71, "raw": 0.907, "pass": 0.92},
        }
        for q in QUERIES:
            for p_name in PIPELINE_META:
                p_tok = PIPELINE_TOKENS[p_name]["prompt"]     + rng2.randint(-100, 200)
                c_tok = PIPELINE_TOKENS[p_name]["completion"] + rng2.randint(-30, 60)
                bp    = BERT[p_name]
                rows.append({
                    "query_id":         q["id"],
                    "query":            q["query"][:60] + "…",
                    "pipeline":         p_name,
                    "total_tokens":     p_tok + c_tok,
                    "latency_s":        round(max(0.4, PIPELINE_LATENCY[p_name] + rng2.gauss(0, 0.3)), 2),
                    "cost_usd":         round(p_tok * PRICE_IN + c_tok * PRICE_OUT, 6),
                    "bertscore_f1":     round(min(1, max(0, bp["rescaled"] + rng2.gauss(0, 0.04))), 4),
                    "bertscore_f1_raw": round(min(1, max(0, bp["raw"]      + rng2.gauss(0, 0.03))), 4),
                    "judge_verdict":    "PASS" if rng2.random() < bp["pass"] else "FAIL",
                })
        df = pd.DataFrame(rows)
        summary = df.groupby("pipeline").agg(
            avg_tokens         = ("total_tokens",     "mean"),
            avg_latency        = ("latency_s",        "mean"),
            avg_cost           = ("cost_usd",         "mean"),
            bertscore_rescaled = ("bertscore_f1",     "mean"),
            bertscore_raw      = ("bertscore_f1_raw", "mean"),
            judge_pass_rate    = ("judge_verdict",    lambda x: f"{(x=='PASS').mean()*100:.0f}%"),
        ).round(3).rename(index={"llm_only": "🤖 LLM Only", "basic_rag": "🔍 Basic RAG", "graphrag": "🕸️ GraphRAG"})
        st.dataframe(summary, use_container_width=True)

        rag_t  = df[df.pipeline=="basic_rag"]["total_tokens"].mean()
        gr_t   = df[df.pipeline=="graphrag"]["total_tokens"].mean()
        tok_rd = (rag_t - gr_t) / rag_t * 100
        pass_p = df[df.pipeline=="graphrag"]["judge_verdict"].eq("PASS").mean() * 100
        bs_r   = df[df.pipeline=="graphrag"]["bertscore_f1"].mean()
        bs_raw = df[df.pipeline=="graphrag"]["bertscore_f1_raw"].mean()

        judge_hit = pass_p >= 90
        bert_hit  = bs_r >= 0.55 or bs_raw >= 0.88

        st.markdown("#### 🏆 Hackathon bonus thresholds")
        b1, b2, b3 = st.columns(3)
        for col, hit, val, label, target in [
            (b1, judge_hit, f"{pass_p:.0f}%",              "LLM Judge pass rate",       "Target ≥ 90%"),
            (b2, bert_hit,  f"{bs_r:.3f} / {bs_raw:.3f}",  "BERTScore rescaled / raw",  "≥0.55 or ≥0.88"),
            (b3, judge_hit and bert_hit,
             "🎯 Max bonus!" if (judge_hit and bert_hit) else "⚠️ Partial",
             "Bonus status", "Hit both = max bonus"),
        ]:
            bg = "#1a3d2e" if hit else "#3d1a1a"
            tc = "#4ade80" if hit else "#f87171"
            ic = "✅" if hit else "❌"
            col.markdown(
                f"<div style='background:{bg};border-radius:10px;padding:16px;text-align:center'>"
                f"<div style='font-size:22px'>{ic}</div>"
                f"<div style='font-weight:700;color:{tc};font-size:20px'>{val}</div>"
                f"<div style='font-size:11px;color:{tc};margin-top:4px'>{label}<br><b>{target}</b></div></div>",
                unsafe_allow_html=True,
            )

        st.success(f"GraphRAG: **{tok_rd:.1f}% token reduction** · **{pass_p:.0f}% judge pass** · **BERTScore {bs_r:.3f}**")
        st.download_button("📥 Download full results CSV", df.to_csv(index=False), "lexgraph_benchmark.csv", "text/csv")
