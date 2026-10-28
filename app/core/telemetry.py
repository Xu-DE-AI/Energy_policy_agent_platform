"""Trace tool order, latency, failures, and estimated cost without storing private chain-of-thought."""
from datetime import datetime, timezone
from sqlalchemy import text
from app.core.db import engine

def utc_now(): return datetime.now(timezone.utc).isoformat()

def create_run(run_id, question, model="local-deterministic"):
    with engine.begin() as c:
        c.execute(text("""INSERT INTO agent_runs(run_id,created_at,question,status,model)
          VALUES(:id,:at,:q,'running',:model)"""), {"id":run_id,"at":utc_now(),"q":question,"model":model})

def record_tool(run_id, seq, name, status, started_at, duration_ms, cost, input_summary, output_summary, error=None):
    with engine.begin() as c:
        c.execute(text("""INSERT INTO tool_events(run_id,sequence_no,tool_name,status,started_at,duration_ms,
          estimated_cost_usd,input_summary,output_summary,error)
          VALUES(:run,:seq,:name,:status,:started,:duration,:cost,:ins,:outs,:error)"""),
          {"run":run_id,"seq":seq,"name":name,"status":status,"started":started_at,"duration":duration_ms,
           "cost":cost,"ins":input_summary[:500],"outs":output_summary[:800],"error":error})

def finish_run(run_id, status, answer, duration_ms, input_tokens=0, output_tokens=0, llm_cost=0.0, error=None):
    with engine.begin() as c:
        c.execute(text("""UPDATE agent_runs SET status=:status,answer=:answer,duration_ms=:duration,
          input_tokens=:it,output_tokens=:ot,llm_cost_usd=:llm,
          tool_cost_usd=(SELECT COALESCE(SUM(estimated_cost_usd),0) FROM tool_events WHERE run_id=:id),
          total_cost_usd=:llm+(SELECT COALESCE(SUM(estimated_cost_usd),0) FROM tool_events WHERE run_id=:id),
          tool_call_count=(SELECT COUNT(*) FROM tool_events WHERE run_id=:id),error=:error WHERE run_id=:id"""),
          {"id":run_id,"status":status,"answer":answer,"duration":duration_ms,"it":input_tokens,"ot":output_tokens,
           "llm":llm_cost,"error":error})
