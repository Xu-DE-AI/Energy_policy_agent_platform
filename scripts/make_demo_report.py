"""Generate a lightweight data quality and portfolio report from sample data."""
import pandas as pd
from pathlib import Path
Path("artifacts").mkdir(exist_ok=True)
df=pd.read_csv("data/sample_data/energy_assets.csv")
report={"rows":len(df),"duplicate_asset_ids":int(df.asset_id.duplicated().sum()),
        "null_cells":int(df.isna().sum().sum()),"capacity_mw":round(float(df.capacity_mw.sum()),2),
        "generation_mwh":round(float(df.annual_generation_mwh.sum()),2),
        "asset_mix":df.groupby("asset_type").capacity_mw.sum().round(2).to_dict()}
pd.Series(report,dtype=object).to_json("artifacts/data_quality_report.json",indent=2)
print(report)
