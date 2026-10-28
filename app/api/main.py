"""HTTP interface for the agent, audit history, and readiness checks."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from app.agent.runner import run_agent
from app.core.db import engine, init_db

app=FastAPI(title="Energy Policy Agent Platform",version="1.0.0",description="Evidence-backed policy RAG, bounded tools, and cost telemetry")
class AskRequest(BaseModel):
    question: str = Field(min_length=3,max_length=4000)
class AskResponse(BaseModel):
    run_id: str; answer: str; trace: list[dict]; cost: dict; duration_ms: float; model: str

@app.on_event("startup")
def startup(): init_db()

@app.get("/health")
def health(): return {"status":"ok"}

@app.get("/ready")
def ready():
    try:
        with engine.connect() as c: c.execute(text("SELECT 1"))
        return {"status":"ready","database":"ok"}
    except Exception as exc: raise HTTPException(503,detail=str(exc))

@app.post("/ask",response_model=AskResponse)
def ask(req: AskRequest):
    try: return run_agent(req.question)
    except Exception as exc: raise HTTPException(500,detail=f"Agent request failed: {type(exc).__name__}")

@app.get("/runs")
def runs(limit:int=50):
    from app.core.db import query_df
    df=query_df("SELECT run_id,created_at,status,model,total_cost_usd,duration_ms,tool_call_count,question FROM agent_runs ORDER BY created_at DESC LIMIT :n",{"n":min(max(limit,1),500)})
    return df.to_dict(orient="records")

@app.get("/runs/{run_id}/trace")
def trace(run_id:str):
    from app.core.db import query_df
    df=query_df("SELECT sequence_no,tool_name,status,started_at,duration_ms,estimated_cost_usd,input_summary,output_summary,error FROM tool_events WHERE run_id=:id ORDER BY sequence_no",{"id":run_id})
    if df.empty: raise HTTPException(404,"Run trace not found")
    return df.to_dict(orient="records")
