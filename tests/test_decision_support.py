"""
test_decision_support.py
-------------------------
Unit tests for the Decision Support Module (SRS FR-3.1 - FR-3.4).
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import decision_support as ds


# ---------------------------------------------------------------------
# compute_priority
# ---------------------------------------------------------------------

def test_priority_zero_when_no_indicators():
    priority = ds.compute_priority(flood_ratio=0.0, person_count=0, damage_score=0.0)
    assert priority == 0.0


def test_priority_increases_with_person_count():
    p0 = ds.compute_priority(0.0, 0, 0.0)
    p1 = ds.compute_priority(0.0, 1, 0.0)
    p2 = ds.compute_priority(0.0, 2, 0.0)
    assert p0 < p1 < p2, "Priority must strictly increase as more people are detected"


def test_priority_increases_with_flood_ratio():
    p_low = ds.compute_priority(0.1, 0, 0.0)
    p_high = ds.compute_priority(0.5, 0, 0.0)
    assert p_high > p_low


def test_priority_increases_with_damage_score():
    p_low = ds.compute_priority(0.0, 0, 0.1)
    p_high = ds.compute_priority(0.0, 0, 0.6)
    assert p_high > p_low


def test_priority_saturates_at_100():
    priority = ds.compute_priority(flood_ratio=1.0, person_count=20, damage_score=1.0)
    assert priority <= 100.0


def test_priority_never_negative():
    priority = ds.compute_priority(flood_ratio=0.0, person_count=0, damage_score=0.0)
    assert priority >= 0.0


def test_priority_max_case_hits_100():
    """With all three factors maxed out, priority should reach exactly 100."""
    priority = ds.compute_priority(flood_ratio=0.5, person_count=4, damage_score=0.6)
    assert priority == 100.0


# ---------------------------------------------------------------------
# classify_risk
# ---------------------------------------------------------------------

@pytest.mark.parametrize("priority,expected", [
    (0, "Low"),
    (25, "Low"),
    (25.1, "Medium"),
    (50, "Medium"),
    (50.1, "High"),
    (75, "High"),
    (75.1, "Critical"),
    (100, "Critical"),
])
def test_classify_risk_thresholds(priority, expected):
    assert ds.classify_risk(priority) == expected


def test_risk_levels_are_monotonic_with_priority():
    """Higher priority scores should never map to a lower risk category."""
    order = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
    priorities = [0, 10, 25, 30, 50, 60, 75, 90, 100]
    levels = [order[ds.classify_risk(p)] for p in priorities]
    assert levels == sorted(levels), "classify_risk must be monotonic non-decreasing"


# ---------------------------------------------------------------------
# suggest_response
# ---------------------------------------------------------------------

def test_suggest_response_critical_mentions_immediate_dispatch():
    text = ds.suggest_response("Critical", person_count=3, damage_flag=True)
    assert "immediately" in text.lower() or "critical" in text.lower() or "dispatch" in text.lower()
    assert "3 person(s) detected" in text
    assert "structural damage" in text


def test_suggest_response_low_mentions_monitor():
    text = ds.suggest_response("Low", person_count=0, damage_flag=False)
    assert "monitor" in text.lower()
    # no extras should be appended when person_count is 0 and no damage
    assert "person(s) detected" not in text
    assert "structural damage" not in text


def test_suggest_response_always_returns_nonempty_string():
    for risk in ["Low", "Medium", "High", "Critical"]:
        text = ds.suggest_response(risk, person_count=0, damage_flag=False)
        assert isinstance(text, str) and len(text) > 0


# ---------------------------------------------------------------------
# evaluate (full Decision Support pipeline)
# ---------------------------------------------------------------------

def test_evaluate_returns_expected_keys():
    result = ds.evaluate(flood_ratio=0.3, person_count=2, damage_score=0.2, damage_flag=False)
    assert set(result.keys()) == {"rescue_priority", "risk_level", "suggested_response", "rescue_plan"}


def test_generate_actionable_rescue_plan_structure():
    plan = ds.generate_actionable_rescue_plan(flood_ratio=0.5, person_count=3, damage_score=0.5, damage_flag=True, risk_level="Critical", priority_score=95.0)
    assert "primary_asset" in plan
    assert "vehicle_type" in plan
    assert "extraction_method" in plan
    assert "required_personnel" in plan
    assert "equipment_checklist" in plan
    assert "execution_steps" in plan
    assert len(plan["execution_steps"]) == 4
    assert "Helicopter" in plan["primary_asset"]


def test_evaluate_consistency_between_priority_and_risk_level():
    """The risk_level returned by evaluate() must always be consistent
    with what classify_risk() would independently compute for the same
    priority score (no drift between the two functions)."""
    for flood, people, damage in [(0.0, 0, 0.0), (0.2, 1, 0.1), (0.5, 4, 0.6), (0.5, 2, 0.3)]:
        result = ds.evaluate(flood, people, damage, damage_flag=(damage > 0.35))
        assert result["risk_level"] == ds.classify_risk(result["rescue_priority"])


def test_evaluate_critical_case_end_to_end():
    """A severe scene (high flood coverage, multiple people, visible
    damage) should end up classified as Critical risk."""
    result = ds.evaluate(flood_ratio=0.5, person_count=4, damage_score=0.6, damage_flag=True)
    assert result["risk_level"] == "Critical"
    assert result["rescue_priority"] == 100.0


def test_evaluate_safe_case_end_to_end():
    """An empty scene (no water, no people, no damage) should be Low risk
    with a 'monitor' style response."""
    result = ds.evaluate(flood_ratio=0.0, person_count=0, damage_score=0.0, damage_flag=False)
    assert result["risk_level"] == "Low"
    assert result["rescue_priority"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
