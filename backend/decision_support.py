"""
decision_support.py
--------------------
Decision Support Module for IFRDSS (SRS Section 3.1.3, FR-3.1 - FR-3.4).

Converts raw computer-vision detections into:
  - a risk_level        (Low / Medium / High / Critical)
  - a rescue_priority    (0-100 numeric score, for ranking submissions)
  - a suggested_response (short actionable text for the dashboard)

The weighting below is this project's own research contribution
(SRS Section 8: "an improved rescue-priority algorithm"), and is exposed
as configurable constants so it can be tuned/justified in the final report.
"""

# ---- Configurable weights (sum to 100) -------------------------------
WEIGHT_FLOOD = 35      # contribution of flood-water extent
WEIGHT_PEOPLE = 45     # contribution of detected person count (most urgent factor)
WEIGHT_DAMAGE = 20     # contribution of structural-damage indicators

# ---- Risk-level thresholds on the 0-100 priority score ----------------
THRESH_LOW = 25
THRESH_MEDIUM = 50
THRESH_HIGH = 75


def compute_priority(flood_ratio: float, person_count: int, damage_score: float):
    """Combine detection outputs into a single 0-100 rescue-priority score.

    flood_ratio   : 0-1, fraction of image classified as flood water
    person_count  : integer count of detected people
    damage_score  : 0-1, structural-damage indicator strength
    """
    flood_component = min(flood_ratio / 0.5, 1.0) * WEIGHT_FLOOD
    # each additional detected person adds urgency, saturating at 4+ people
    people_component = min(person_count / 4.0, 1.0) * WEIGHT_PEOPLE
    damage_component = min(damage_score / 0.6, 1.0) * WEIGHT_DAMAGE

    priority = flood_component + people_component + damage_component
    return round(min(priority, 100.0), 1)


def classify_risk(priority: float) -> str:
    if priority <= THRESH_LOW:
        return "Low"
    elif priority <= THRESH_MEDIUM:
        return "Medium"
    elif priority <= THRESH_HIGH:
        return "High"
    else:
        return "Critical"


def suggest_response(risk_level: str, person_count: int, damage_flag: bool) -> str:
    if risk_level == "Critical":
        base = "Dispatch rescue team immediately \u2014 highest priority."
    elif risk_level == "High":
        base = "Dispatch rescue team as soon as available."
    elif risk_level == "Medium":
        base = "Schedule rescue/assessment team within routine response window."
    else:
        base = "Monitor situation; no immediate rescue dispatch required."

    extras = []
    if person_count > 0:
        extras.append(f"{person_count} person(s) detected in frame")
    if damage_flag:
        extras.append("possible structural damage present")

    if extras:
        base += " (" + "; ".join(extras) + ")"
    return base


def generate_actionable_rescue_plan(flood_ratio: float, person_count: int, damage_score: float, damage_flag: bool, risk_level: str, priority_score: float):
    """Generate intelligent, scene-tailored tactical rescue protocols and execution steps
    ('suggesting the way to save the people').
    """
    if risk_level == "Critical" or (person_count > 0 and flood_ratio > 0.4):
        primary_asset = "Aerial Rescue Helicopter (Sikorsky S-92 / CH-47) with Winch Hoist"
        vehicle_type = "Helicopter / Air Hoist"
        extraction_method = "Aerial Rooftop/Water Hoist Extraction"
    elif flood_ratio > 0.25:
        primary_asset = "Rigid Inflatable Motorboat (RIB) & Swiftwater Rescue Vessel"
        vehicle_type = "Swiftwater Motorboat"
        extraction_method = "Water-Surface Vessel Transfer"
    elif damage_flag or damage_score > 0.4:
        primary_asset = "High-Clearance Amphibious Rescue Vehicle (ARV)"
        vehicle_type = "Amphibious ARV"
        extraction_method = "Urban Debris Wading & Structural Access"
    else:
        primary_asset = "Field Mobile Patrol & Shallow-Water Wading Unit"
        vehicle_type = "Shallow Patrol Unit"
        extraction_method = "Guided Shoreline Evacuation"

    required_personnel = []
    if person_count > 0:
        required_personnel.append("Swiftwater Rescue Technicians (SRT)")
        required_personnel.append("Emergency Paramedics / Triage Specialists")
    if risk_level in ["High", "Critical"]:
        required_personnel.append("Flight Crew & Rescue Swimmers")
    if damage_flag:
        required_personnel.append("Structural Collapse & Search Engineers (USAR)")
    if not required_personnel:
        required_personnel.append("Disaster Assessment & Telemetry Monitors")

    equipment_checklist = [
        "Personal Flotation Devices (PFDs / Life Vests)",
        "Hypothermia Thermal Blankets",
        "Floating Throw Bags & Rescue Lines"
    ]
    if person_count > 0:
        equipment_checklist.append("Medical Trauma & Oxygen Response Kits")
        equipment_checklist.append("Child / Infant Safety Harnesses")
    if risk_level in ["High", "Critical"]:
        equipment_checklist.append("Aviation Winch Harness & Rescue Basket")
        equipment_checklist.append("High-Lumen Searchlights & Thermal Cameras")
    if damage_flag:
        equipment_checklist.append("Heavy Debris Cutters & Structural Shoring Gear")

    execution_steps = [
        f"Phase 1 (Approach): Deploy {primary_asset} toward target GPS coordinates; establish 2-way comms channel.",
        "Phase 2 (Stabilize): Conduct immediate hazard assessment (current speed, electrical grid hazards, structural integrity).",
        f"Phase 3 (Extraction): Execute {extraction_method} to secure {person_count} victim(s) with safety harnesses.",
        "Phase 4 (Triage & Evacuation): Transport evacuees to designated emergency shelter; initiate medical triage."
    ]

    return {
        "primary_asset": primary_asset,
        "vehicle_type": vehicle_type,
        "extraction_method": extraction_method,
        "required_personnel": required_personnel,
        "equipment_checklist": equipment_checklist,
        "execution_steps": execution_steps,
        "evacuation_protocol": f"Priority evacuation to designated shelter via {vehicle_type}"
    }


def evaluate(flood_ratio: float, person_count: int, damage_score: float, damage_flag: bool):
    """Full decision-support evaluation, returned as a dict ready for
    JSON serialization / database storage."""
    priority = compute_priority(flood_ratio, person_count, damage_score)
    risk_level = classify_risk(priority)
    response = suggest_response(risk_level, person_count, damage_flag)
    rescue_plan = generate_actionable_rescue_plan(flood_ratio, person_count, damage_score, damage_flag, risk_level, priority)

    return {
        "rescue_priority": priority,
        "risk_level": risk_level,
        "suggested_response": response,
        "rescue_plan": rescue_plan
    }
