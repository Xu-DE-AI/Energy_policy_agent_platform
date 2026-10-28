from app.agent.tools import run_policy_scenario, calculate_energy_metrics

def test_scenario_has_explicit_assumptions():
    out=run_policy_scenario(.4,40000,80)
    assert out["assumptions"]["renewable_share"] == .4
    assert "not an operational forecast" in out["model_type"]

def test_metrics_label_synthetic_data():
    out=calculate_energy_metrics("DE")
    assert out["is_synthetic"] is True
    assert out["asset_count"] > 0

def test_scenario_rejects_invalid_share():
    try: run_policy_scenario(1.2,40000,80)
    except ValueError: pass
    else: raise AssertionError("Invalid share should be rejected")
