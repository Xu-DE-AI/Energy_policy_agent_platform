"""Executive-facing Streamlit dashboard for agent activity, cost, and retrieval quality."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent))
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import text
from app.core.db import engine, init_db, query_df
from app.agent.runner import run_agent
from app.rag.index import get_index

st.set_page_config(page_title="Energy Policy AgentOps",page_icon="⚡",layout="wide")
st.markdown("""<style>
:root { --ink:#10233f; --muted:#64748b; --teal:#0e8f87; }
.block-container {padding-top:1.5rem; max-width:1500px;}
[data-testid="stMetric"] {background:linear-gradient(135deg,#f5f9ff,#edf8f6);padding:16px;border:1px solid #dbe7f0;border-radius:16px;}
.hero {padding:24px 28px;border-radius:20px;background:linear-gradient(115deg,#10233f,#155e75 68%,#0e8f87);color:white;margin-bottom:18px;}
.hero h1 {color:white;margin:0;font-size:2rem;} .hero p {color:#dcecf5;margin:8px 0 0;}
.small-muted {color:#64748b;font-size:0.9rem;}
</style>""",unsafe_allow_html=True)
init_db()
st.markdown('<div class="hero"><h1>⚡ Energy Policy AgentOps</h1><p>Evidence-backed policy intelligence · tool observability · cost governance · RAG</p></div>',unsafe_allow_html=True)
with st.sidebar:
    st.header("Workspace")
    st.caption("Local mode works without an LLM API key. Configure .env to enable synthesis.")
    if st.button("Rebuild policy index",use_container_width=True):
        n=get_index().build(); st.success(f"Indexed {n} policy chunks")
    st.divider(); st.markdown("**Governance controls**")
    st.markdown("- Bounded tool calls\n- Per-tool cost ledger\n- Request budget guard\n- Source-linked retrieval\n- Run-level audit trail")

runs=query_df("SELECT * FROM agent_runs ORDER BY created_at DESC")
if runs.empty:
    total_runs=0; total_cost=0; avg_latency=0; calls=0
else:
    total_runs=len(runs); total_cost=float(runs.total_cost_usd.fillna(0).sum()); avg_latency=float(runs.duration_ms.fillna(0).mean()); calls=int(runs.tool_call_count.fillna(0).sum())
c1,c2,c3,c4=st.columns(4)
c1.metric("Agent runs",f"{total_runs:,}"); c2.metric("Tracked spend",f"${total_cost:.4f}"); c3.metric("Avg latency",f"{avg_latency:,.0f} ms"); c4.metric("Tool calls",f"{calls:,}")
left,right=st.columns([1.2,0.8],gap="large")
with left:
    st.subheader("Ask the energy-policy agent")
    prompt=st.text_area("Question",value="Summarise the EU renewable energy policy implications for a wind and battery portfolio in Germany, and identify what must be verified before making a compliance claim.",height=105)
    if st.button("Run agent",type="primary",use_container_width=True):
        with st.spinner("Retrieving evidence and executing bounded tools…"):
            try: st.session_state["last_result"]=run_agent(prompt)
            except Exception as e: st.error(f"Run failed: {e}")
    if "last_result" in st.session_state:
        r=st.session_state["last_result"]
        st.markdown("#### Answer")
        st.markdown(r["answer"])
        st.caption(f"Run `{r['run_id']}` · {r['model']} · {r['duration_ms']:.0f} ms")
        st.markdown("#### Observable tool sequence")
        if r["trace"]: st.dataframe(pd.DataFrame(r["trace"]),use_container_width=True,hide_index=True)
        st.markdown("#### Request cost")
        st.json(r["cost"])
with right:
    st.subheader("Spend over time")
    if not runs.empty:
        runs["created_at"]=pd.to_datetime(runs.created_at,errors="coerce",utc=True)
        spend=runs.dropna(subset=["created_at"]).set_index("created_at").resample("D").total_cost_usd.sum().reset_index()
        fig=px.area(spend,x="created_at",y="total_cost_usd",labels={"created_at":"Day","total_cost_usd":"USD"},template="plotly_white")
        fig.update_traces(line_color="#0e8f87",fillcolor="rgba(14,143,135,.16)"); fig.update_layout(margin=dict(l=0,r=0,t=15,b=0),height=260)
        st.plotly_chart(fig,use_container_width=True)
    else: st.info("Spend charts appear after the first agent run.")
    st.subheader("Tool reliability")
    events=query_df("SELECT tool_name,status,duration_ms,estimated_cost_usd FROM tool_events")
    if not events.empty:
        rel=events.groupby(["tool_name","status"]).size().reset_index(name="calls")
        fig2=px.bar(rel,x="tool_name",y="calls",color="status",barmode="group",template="plotly_white",color_discrete_sequence=["#0e8f87","#e9a23b","#c2414b"])
        fig2.update_layout(margin=dict(l=0,r=0,t=15,b=0),height=260,xaxis_title="Tool",yaxis_title="Calls")
        st.plotly_chart(fig2,use_container_width=True)
    else: st.info("No tool telemetry yet.")
st.divider()
tab1,tab2,tab3=st.tabs(["Run ledger","Tool telemetry","Policy corpus"])
with tab1:
    if not runs.empty:
        view=runs[["created_at","run_id","status","model","tool_call_count","duration_ms","total_cost_usd","question"]].copy()
        st.dataframe(view,use_container_width=True,hide_index=True)
with tab2:
    if not events.empty:
        st.dataframe(events,use_container_width=True,hide_index=True)
        st.caption("Tool order is persisted per run. The trace stores action names, inputs/outputs summaries, status, latency, and estimated costs—not private chain-of-thought.")
with tab3:
    docs=list(Path("data/policy_docs").glob("*.md"))
    st.metric("Policy briefs",len(docs)); st.write("Original analytical summaries linked to official EU/IEA source pages. Verify current official texts before legal/compliance use.")
    st.dataframe(pd.DataFrame([{"file":p.name,"title":next((x[2:].strip() for x in p.read_text().splitlines() if x.startswith('# ')),p.stem)} for p in docs]),use_container_width=True,hide_index=True)
