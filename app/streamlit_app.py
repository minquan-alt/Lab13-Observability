"""
Day 13 – Observability Dashboard
Navigation: st.tabs (not selectbox) to avoid input-field confusion.
"""
from __future__ import annotations

import json
import os

import httpx
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from jsonschema import validate, ValidationError

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="Observability Hub · Day 13",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 2rem; }
    .score-good  { color: #22c55e; font-weight: bold; }
    .score-mid   { color: #f59e0b; font-weight: bold; }
    .score-bad   { color: #ef4444; font-weight: bold; }
    div[data-testid="stTab"] button { font-size: 0.95rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── Constants ───────────────────────────────────────────────────
API_URL      = "http://127.0.0.1:8000"
TRACE_FILE   = "data/trace_history.jsonl"
MOCK_FILE    = "data/mock_traces.jsonl"
SCHEMA_FILE  = "config/logging_schema.json"

# ── Helpers ────────────────────────────────────────────────────
def load_jsonl(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    df = pd.DataFrame(rows)
    if not df.empty and "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    return df


def load_schema() -> dict | None:
    if os.path.exists(SCHEMA_FILE):
        with open(SCHEMA_FILE) as f:
            return json.load(f)
    return None


def score_badge(v: float) -> str:
    cls = "score-good" if v >= 0.75 else ("score-mid" if v >= 0.5 else "score-bad")
    return f'<span class="{cls}">{v:.2f}</span>'


def validate_and_inject(raw: str) -> tuple[bool, list[str]]:
    """Parse + validate a JSON record and append to trace file."""
    errors: list[str] = []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return False, [f"JSON syntax error: {e}"]

    records = data if isinstance(data, list) else [data]

    required = ["ts", "user_id_hash", "session_id", "feature", "model",
                 "message", "answer", "latency_ms", "tokens_in", "tokens_out",
                 "cost_usd", "quality", "relevancy", "faithfulness"]

    for i, rec in enumerate(records):
        prefix = f"Record {i}: " if len(records) > 1 else ""
        for field in required:
            if field not in rec:
                errors.append(f"{prefix}Missing required field: `{field}`")
        if "latency_ms" in rec and not isinstance(rec["latency_ms"], int):
            errors.append(f"{prefix}`latency_ms` must be int, got {type(rec['latency_ms']).__name__}")
        if "quality" in rec and isinstance(rec["quality"], (int, float)):
            if not 0.0 <= rec["quality"] <= 1.0:
                errors.append(f"{prefix}`quality` must be 0.0–1.0, got {rec['quality']}")
        if "latency_ms" in rec and isinstance(rec["latency_ms"], int) and rec["latency_ms"] < 0:
            errors.append(f"{prefix}`latency_ms` must be ≥ 0, got {rec['latency_ms']}")

    if errors:
        return False, errors

    os.makedirs("data", exist_ok=True)
    with open(TRACE_FILE, "a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    return True, []


# ── Sidebar ─────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔭 Observability Hub")
    st.caption("Day 13 · Lab Framework")
    st.divider()

    # Backend status
    backend_ok = False
    try:
        r = httpx.get(f"{API_URL}/health", timeout=4.0)
        health = r.json()
        backend_ok = health.get("ok", False)
        tracing_on = health.get("tracing_enabled", False)
        incidents  = health.get("incidents", {})
        st.success("🟢 Backend Online")
        st.caption(f"Langfuse tracing: {'✅ ON' if tracing_on else '⛔ OFF (no keys)'}")
    except Exception as exc:
        st.error("🔴 Backend Offline")
        st.caption(f"Detail: {exc}")
        incidents = {}

    if incidents:
        st.divider()
        st.subheader("⚡ Incident Injection")
        for name, enabled in incidents.items():
            new_val = st.toggle(name.replace("_", " ").title(), value=enabled, key=f"inc_{name}")
            if new_val != enabled:
                endpoint = "enable" if new_val else "disable"
                try:
                    httpx.post(f"{API_URL}/incidents/{name}/{endpoint}", timeout=3.0)
                    st.rerun()
                except Exception:
                    pass

    st.divider()
    use_mock = st.checkbox("📦 Use Mock Data (demo)", value=not os.path.exists(TRACE_FILE))
    data_path = MOCK_FILE if use_mock else TRACE_FILE
    st.caption(f"Source: `{data_path}`")

# ── Main tabs ───────────────────────────────────────────────────
tab_dash, tab_chat, tab_inject, tab_traces = st.tabs([
    "📊 Dashboard",
    "💬 Chat Terminal",
    "🔍 JSON Inspector",
    "📂 Trace Explorer",
])

# ═══════════════════════════════════════════════════════════════
# TAB 1 – DASHBOARD
# ═══════════════════════════════════════════════════════════════
with tab_dash:
    st.header("📊 System Health & Evaluation Dashboard")

    df = load_jsonl(data_path)

    if df.empty:
        st.info("No trace data yet. Chat with the agent or use **Mock Data** from the sidebar.")
        st.stop()

    # ── KPI row ────────────────────────────────────────────────
    req_count  = len(df)
    avg_q      = df["quality"].mean()     if "quality"     in df.columns else 0.0
    avg_rel    = df["relevancy"].mean()   if "relevancy"   in df.columns else 0.0
    avg_faith  = df["faithfulness"].mean() if "faithfulness" in df.columns else 0.0
    p95_lat    = df["latency_ms"].quantile(0.95) if "latency_ms" in df.columns else 0
    total_cost = df["cost_usd"].sum()    if "cost_usd"    in df.columns else 0.0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Requests",       req_count)
    c2.metric("Avg Quality",    f"{avg_q:.2f}")
    c3.metric("Avg Relevancy",  f"{avg_rel:.2f}")
    c4.metric("Avg Faithfulness", f"{avg_faith:.2f}")
    c5.metric("P95 Latency",    f"{p95_lat:.0f} ms",
              delta="SLO: 2000ms" if p95_lat > 2000 else None,
              delta_color="inverse")
    c6.metric("Total Cost",     f"${total_cost:.4f}")

    st.divider()

    # ── Evaluation Trends ───────────────────────────────────────
    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.subheader("🎯 Evaluation Scores Over Time")
        fig = go.Figure()
        for col, color, dash in [
            ("quality",     "#22c55e", "solid"),
            ("relevancy",   "#3b82f6", "dot"),
            ("faithfulness","#f59e0b", "dash"),
        ]:
            if col in df.columns:
                fig.add_trace(go.Scatter(
                    x=df["ts"], y=df[col], name=col.title(),
                    line=dict(color=color, width=2.5, dash=dash),
                    hovertemplate=f"{col.title()}: %{{y:.2f}}<extra></extra>",
                ))
        fig.add_hrect(y0=0.75, y1=1.0, fillcolor="#22c55e", opacity=0.05, line_width=0)
        fig.add_hrect(y0=0.5, y1=0.75, fillcolor="#f59e0b", opacity=0.05, line_width=0)
        fig.add_hrect(y0=0.0, y1=0.5, fillcolor="#ef4444", opacity=0.05, line_width=0)
        fig.update_layout(
            hovermode="x unified", yaxis=dict(range=[0, 1.05], title="Score"),
            legend=dict(orientation="h", y=1.05), height=300,
            margin=dict(t=20, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("⚖️ Quality Distribution")
        if "quality" in df.columns:
            fig_hist = px.histogram(
                df, x="quality", nbins=10,
                color_discrete_sequence=["#3b82f6"],
                labels={"quality": "Quality Score", "count": "Requests"},
            )
            fig_hist.update_layout(height=300, margin=dict(t=10, b=10), bargap=0.1)
            st.plotly_chart(fig_hist, use_container_width=True)

    st.divider()

    # ── Latency & Cost row ──────────────────────────────────────
    c_lat, c_cost = st.columns(2)

    with c_lat:
        st.subheader("⏱️ Quality vs. Latency")
        if "latency_ms" in df.columns and "quality" in df.columns:
            fig_scatter = px.scatter(
                df, x="latency_ms", y="quality",
                color="feature" if "feature" in df.columns else None,
                size="tokens_out" if "tokens_out" in df.columns else None,
                hover_data=["model"] if "model" in df.columns else [],
                labels={"latency_ms": "Latency (ms)", "quality": "Quality Score"},
            )
            fig_scatter.add_vline(
                x=2000, line_dash="dash", line_color="red",
                annotation_text="SLO 2s", annotation_position="top right",
            )
            fig_scatter.update_layout(height=300, margin=dict(t=10, b=10))
            st.plotly_chart(fig_scatter, use_container_width=True)

    with c_cost:
        st.subheader("💰 Cost by Feature")
        if "feature" in df.columns and "cost_usd" in df.columns:
            cost_df = df.groupby("feature")["cost_usd"].sum().reset_index()
            fig_pie = px.pie(
                cost_df, values="cost_usd", names="feature",
                hole=0.45, color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            fig_pie.update_layout(height=300, margin=dict(t=10, b=10), showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# TAB 2 – CHAT TERMINAL
# ═══════════════════════════════════════════════════════════════
with tab_chat:
    st.header("💬 AI Agent Console")
    if not backend_ok:
        st.warning("Backend is offline. Start the FastAPI server first.")
    else:
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant" and "meta" in msg:
                    m = msg["meta"]
                    st.caption(
                        f"✨ Quality **{m.get('quality_score', '?')}** · "
                        f"⏱️ {m.get('latency_ms', '?')} ms · "
                        f"🪙 ${m.get('cost_usd', 0):.5f} · "
                        f"🔗 `{m.get('correlation_id', '?')[:12]}…`"
                    )

        prompt = st.chat_input("Ask the agent something…")
        if prompt:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking…"):
                    try:
                        resp = httpx.post(
                            f"{API_URL}/chat",
                            json={"user_id": "lab_user", "session_id": "dash_session",
                                  "feature": "terminal", "message": prompt},
                            timeout=60.0,
                        )
                        data = resp.json()
                        answer = data.get("answer", str(data))
                        st.markdown(answer)
                        st.caption(
                            f"✨ Quality **{data.get('quality_score', '?')}** · "
                            f"⏱️ {data.get('latency_ms', '?')} ms · "
                            f"🪙 ${data.get('cost_usd', 0):.5f} · "
                            f"🔗 `{data.get('correlation_id', '?')[:12]}…`"
                        )
                        st.session_state.chat_history.append({
                            "role": "assistant", "content": answer, "meta": data,
                        })
                    except Exception as e:
                        st.error(f"Request failed: {e}")


# ═══════════════════════════════════════════════════════════════
# TAB 3 – JSON INSPECTOR / INJECTOR
# ═══════════════════════════════════════════════════════════════
with tab_inject:
    st.header("🔍 JSON Inspector & Injector")
    st.caption(
        "Paste a single JSON object or a JSON array. "
        "Valid records are saved to `data/trace_history.jsonl` and will appear in the Dashboard."
    )

    # Sample chooser  ← fixed: uses radio, not a text-input
    sample_choice = st.radio(
        "Load a sample:",
        ["— blank —", "✅ Valid record", "❌ Missing field (ts)", "❌ Wrong type (latency_ms)", "❌ Out-of-range (quality)"],
        horizontal=True,
        key="sample_radio",
    )

    SAMPLES = {
        "✅ Valid record": json.dumps({
            "ts": "2026-04-20T10:00:00Z",
            "user_id_hash": "demo_user",
            "session_id": "demo_session",
            "feature": "qa",
            "model": "claude-sonnet-4-5",
            "message": "What is observability?",
            "answer": "Observability is the ability to understand a system from its outputs.",
            "latency_ms": 320,
            "tokens_in": 40,
            "tokens_out": 85,
            "cost_usd": 0.000795,
            "quality": 0.9,
            "relevancy": 0.8,
            "faithfulness": 0.9,
        }, indent=2),
        "❌ Missing field (ts)": json.dumps({
            "user_id_hash": "err_user",
            "session_id": "err_session",
            "feature": "qa",
            "model": "claude-sonnet-4-5",
            "message": "Missing ts field",
            "answer": "This record is missing the ts field.",
            "latency_ms": 100,
            "tokens_in": 20, "tokens_out": 30, "cost_usd": 0.0002,
            "quality": 0.5, "relevancy": 0.5, "faithfulness": 0.5,
        }, indent=2),
        "❌ Wrong type (latency_ms)": json.dumps({
            "ts": "2026-04-20T10:01:00Z",
            "user_id_hash": "err_user",
            "session_id": "err_session",
            "feature": "qa",
            "model": "claude-sonnet-4-5",
            "message": "Wrong latency type",
            "answer": "latency_ms should be an integer.",
            "latency_ms": "very_slow",
            "tokens_in": 20, "tokens_out": 30, "cost_usd": 0.0002,
            "quality": 0.5, "relevancy": 0.5, "faithfulness": 0.5,
        }, indent=2),
        "❌ Out-of-range (quality)": json.dumps({
            "ts": "2026-04-20T10:02:00Z",
            "user_id_hash": "err_user",
            "session_id": "err_session",
            "feature": "summary",
            "model": "claude-sonnet-4-5",
            "message": "Quality > 1",
            "answer": "Quality score is out of range.",
            "latency_ms": 200,
            "tokens_in": 20, "tokens_out": 30, "cost_usd": 0.0002,
            "quality": 9.5, "relevancy": 0.5, "faithfulness": 0.5,
        }, indent=2),
    }

    default_text = SAMPLES.get(sample_choice, "")
    json_input = st.text_area(
        "JSON payload",
        value=default_text,
        height=280,
        placeholder='{"ts": "2026-04-20T…", "latency_ms": 300, …}',
        key="json_input_area",
    )

    uploaded = st.file_uploader("Or upload a .json / .jsonl file", type=["json", "jsonl"])
    if uploaded:
        json_input = uploaded.read().decode("utf-8")
        st.text_area("Uploaded content (preview)", json_input[:600], height=150, disabled=True)

    col_btn1, col_btn2, _ = st.columns([1, 1, 4])
    inject_btn    = col_btn1.button("✅ Validate & Inject", type="primary")
    dryrun_btn    = col_btn2.button("🔎 Dry-run (validate only)")

    if inject_btn or dryrun_btn:
        if not json_input.strip():
            st.warning("Please provide JSON input.")
        else:
            ok, errs = validate_and_inject(json_input) if inject_btn else (None, None)
            # For dry-run we only validate, not write
            if dryrun_btn:
                try:
                    data = json.loads(json_input)
                    records = data if isinstance(data, list) else [data]
                    errs = []
                    required = ["ts","user_id_hash","session_id","feature","model",
                                "message","answer","latency_ms","tokens_in","tokens_out",
                                "cost_usd","quality","relevancy","faithfulness"]
                    for i, rec in enumerate(records):
                        prefix = f"Record {i}: " if len(records)>1 else ""
                        for field in required:
                            if field not in rec:
                                errs.append(f"{prefix}Missing required field: `{field}`")
                        if "latency_ms" in rec and not isinstance(rec["latency_ms"], int):
                            errs.append(f"{prefix}`latency_ms` must be int")
                        if "quality" in rec and isinstance(rec["quality"], (int,float)):
                            if not 0<=rec["quality"]<=1:
                                errs.append(f"{prefix}`quality` must be 0–1, got {rec['quality']}")
                    ok = len(errs) == 0
                except json.JSONDecodeError as e:
                    errs = [f"JSON syntax error: {e}"]
                    ok = False

            if ok:
                st.success("✅ JSON is valid!" + (" Record injected into trace history." if inject_btn else " (Dry-run only — not saved.)"))
                if inject_btn:
                    st.balloons()
            else:
                st.error(f"❌ Validation failed with {len(errs)} error(s):")
                for e in errs:
                    st.markdown(f"- {e}")

                st.markdown("---")
                st.subheader("💡 How to fix:")
                err_str = " ".join(errs)
                if "ts" in err_str and "Missing" in err_str:
                    st.info('Add `"ts": "2026-04-20T10:00:00Z"` (ISO-8601 UTC timestamp).')
                if "latency_ms" in err_str and "int" in err_str:
                    st.info('Change `latency_ms` to an integer, e.g. `320` (not `"320"` or `"high"`).')
                if "quality" in err_str and "0" in err_str:
                    st.info("`quality`, `relevancy`, and `faithfulness` must be floats between 0.0 and 1.0.")
                st.caption("See `docs/schema_document.md` for the full field reference.")

# ═══════════════════════════════════════════════════════════════
# TAB 4 – TRACE EXPLORER
# ═══════════════════════════════════════════════════════════════
with tab_traces:
    st.header("📂 Trace Explorer")
    df_trace = load_jsonl(data_path)

    if df_trace.empty:
        st.warning("No traces found. Use mock data or chat with the agent.")
    else:
        # ── Filters ────────────────────────────────────────────
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            features = ["All"] + sorted(df_trace["feature"].dropna().unique().tolist()) \
                if "feature" in df_trace.columns else ["All"]
            sel_feat = st.selectbox("Filter by Feature", features)
        with fc2:
            models = ["All"] + sorted(df_trace["model"].dropna().unique().tolist()) \
                if "model" in df_trace.columns else ["All"]
            sel_model = st.selectbox("Filter by Model", models)
        with fc3:
            min_q = st.slider("Min Quality Score", 0.0, 1.0, 0.0, 0.05)

        view = df_trace.copy()
        if sel_feat != "All":
            view = view[view["feature"] == sel_feat]
        if sel_model != "All":
            view = view[view["model"] == sel_model]
        if "quality" in view.columns:
            view = view[view["quality"] >= min_q]

        st.caption(f"Showing {len(view)} / {len(df_trace)} records")

        # ── Table ───────────────────────────────────────────────
        display_cols = [c for c in
            ["ts","feature","model","latency_ms","quality","relevancy","faithfulness","cost_usd","session_id"]
            if c in view.columns]
        st.dataframe(
            view[display_cols].sort_values("ts", ascending=False).reset_index(drop=True),
            use_container_width=True,
            height=400,
        )

        # ── Row detail expander ─────────────────────────────────
        with st.expander("🔍 View row details (enter row index above)"):
            row_idx = st.number_input("Row index", min_value=0,
                                       max_value=max(0, len(view)-1), step=1)
            if not view.empty:
                row = view.sort_values("ts", ascending=False).iloc[int(row_idx)]
                st.json(row.to_dict())

        st.download_button(
            "⬇️ Export CSV",
            view.to_csv(index=False),
            file_name="trace_export.csv",
            mime="text/csv",
        )
