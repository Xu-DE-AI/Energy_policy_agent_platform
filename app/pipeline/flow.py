"""Repeatable ingestion/indexing flow; Prefect is optional for local execution."""
from pathlib import Path
import json, hashlib
from app.rag.index import PolicyIndex

def validate_policy_corpus():
    docs=sorted(Path("data/policy_docs").glob("*.md"))
    if len(docs)<5: raise ValueError("Policy corpus is unexpectedly small")
    missing=[]
    for p in docs:
        raw=p.read_text(encoding="utf-8")
        if "**Source:**" not in raw or len(raw)<250: missing.append(p.name)
    if missing: raise ValueError(f"Missing source metadata or content: {missing}")
    return {"document_count":len(docs),"sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in docs}}

def build_index():
    index=PolicyIndex(); count=index.build()
    return {"chunks_indexed":count}

def run_pipeline():
    report={"validation":validate_policy_corpus(),"index":build_index()}
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/pipeline_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    return report

try:
    from prefect import flow, task
    @task(retries=2, retry_delay_seconds=3)
    def validate_task(): return validate_policy_corpus()
    @task(retries=2, retry_delay_seconds=3)
    def index_task(): return build_index()
    @flow(name="energy-policy-rag-ingestion",log_prints=True)
    def energy_policy_ingestion_flow():
        validation=validate_task(); index=index_task()
        Path("artifacts").mkdir(exist_ok=True)
        Path("artifacts/pipeline_report.json").write_text(json.dumps({"validation":validation,"index":index},indent=2),encoding="utf-8")
        return {"validation":validation,"index":index}
except ImportError:
    energy_policy_ingestion_flow=None

if __name__ == "__main__":
    print(energy_policy_ingestion_flow() if energy_policy_ingestion_flow else run_pipeline())
