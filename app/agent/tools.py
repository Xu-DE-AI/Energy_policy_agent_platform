"""Typed, bounded tools used by the agent. Each tool has an explicit cost policy."""
from pathlib import Path
import pandas as pd
from app.rag.index import get_index

TOOL_COST_USD = {"search_policy_docs": 0.0002, "calculate_energy_metrics": 0.0001,
                 "run_policy_scenario": 0.0005, "get_market_snapshot": 0.0002}

def search_policy_docs(query: str, top_k: int = 4):
    """Retrieve relevant energy-policy evidence with source URLs and relevance scores."""
    hits = get_index().search(query, top_k=min(max(int(top_k),1),5))
    return {"results":[{"title":h["title"],"topic":h["topic"],"source":h["source_url"],
                         "score":round(h["score"],4),"excerpt":h["text"][:700]} for h in hits]}

def calculate_energy_metrics(country: str | None = None):
    """Aggregate synthetic asset data; output is labelled illustrative, never official statistics."""
    path = Path("data/sample_data/energy_assets.csv")
    df = pd.read_csv(path)
    if country: df = df[df.country.str.upper() == country.upper()]
    if df.empty: return {"error":f"No sample assets for country={country}","is_synthetic":True}
    return {"country_filter":country,"asset_count":int(len(df)),"capacity_mw":round(float(df.capacity_mw.sum()),2),
            "annual_generation_mwh":round(float(df.annual_generation_mwh.sum()),2),
            "weighted_co2_intensity_t_mwh":round(float((df.co2_intensity_t_mwh*df.annual_generation_mwh).sum()/max(df.annual_generation_mwh.sum(),1)),4),
            "asset_mix":df.groupby('asset_type').capacity_mw.sum().round(2).to_dict(),"is_synthetic":True}

def run_policy_scenario(renewable_share: float, demand_mw: float, carbon_price_eur_t: float):
    """Transparent toy scenario model; coefficients are illustrative, not a forecast."""
    if not 0 <= renewable_share <= 1: raise ValueError("renewable_share must be between 0 and 1")
    if demand_mw <= 0 or carbon_price_eur_t < 0: raise ValueError("demand must be positive and carbon price non-negative")
    baseline = 35 + 0.001*demand_mw + 0.28*carbon_price_eur_t
    estimated_price = max(-10, baseline - 65*renewable_share)
    return {"assumptions":{"renewable_share":renewable_share,"demand_mw":demand_mw,"carbon_price_eur_t":carbon_price_eur_t},
            "estimated_wholesale_price_eur_mwh":round(estimated_price,2),"baseline_before_renewables_eur_mwh":round(baseline,2),
            "model_type":"illustrative linear scenario; not an operational forecast"}

def get_market_snapshot(country: str = "DE"):
    """Read latest synthetic market record for a supported country."""
    df = pd.read_csv("data/sample_data/market_prices.csv", parse_dates=["timestamp_utc"])
    df = df[df.country.str.upper() == country.upper()].sort_values("timestamp_utc")
    if df.empty: return {"error":"Country not present in synthetic sample data"}
    row = df.iloc[-1]
    return {"country":country.upper(),"timestamp_utc":row.timestamp_utc.isoformat(),
            "wholesale_price_eur_mwh":float(row.wholesale_price_eur_mwh),"demand_mw":float(row.demand_mw),
            "renewable_share":float(row.renewable_share),"carbon_price_eur_t":float(row.carbon_price_eur_t),
            "is_synthetic":True}

TOOLS = {"search_policy_docs":search_policy_docs,"calculate_energy_metrics":calculate_energy_metrics,
         "run_policy_scenario":run_policy_scenario,"get_market_snapshot":get_market_snapshot}
