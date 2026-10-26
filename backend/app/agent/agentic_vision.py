"""
AegisVision - Autonomous Agentic Vision Engine (See -> Reason -> Act)
Orchestrates multi-step reasoning over OpenCV 5 visual telemetry, evaluates regulatory
policies (OSHA, ISO, NFPA), formulates mitigation action plans, and dispatches tools.
"""

import time
import logging
from typing import Dict, Any, List
from backend.app.agent.tools import actuator_tools
from backend.app.aws.aws_client import aws_client

logger = logging.getLogger("aegis_vision.agent")

class AgenticVisionEngine:
    def __init__(self):
        self.reasoning_log: List[Dict[str, Any]] = []
        self.regulatory_policies = {
            "OSHA_1910_212": "Machine Guarding: Operators & personnel must be physically shielded or machines halted upon breach of the point of operation envelope.",
            "ISO_14644_1": "Cleanroom Class 4 Standards: Wafer defect contamination exceeding 120px² requires batch quarantine and laser recalibration.",
            "NFPA_704_SPILL": "Hazardous Fluid Protocol: Chemical leaks expanding over 1000px² demand immediate negative pressure HVAC isolation and AGV corridor evacuation.",
            "OSHA_1910_132": "PPE General Requirements: Eye, head, and high-visibility apparel mandatory prior to entering high-risk cleanroom airlock boundaries."
        }

    def reason_and_act(self, channel_id: str, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the autonomous See -> Reason -> Act loop for a given vision telemetry frame.
        """
        cycle_start = time.perf_counter()
        cycle_id = f"CYC-{int(time.time()*1000)}"

        # Step 1: Perceive (Structured OpenCV Telemetry)
        observations = []
        risk_level = "LOW"
        applicable_policy = None
        action_plan = []
        tool_results = []

        # Step 2: Reason based on visual telemetry
        if channel_id == "wafer":
            defect_cnt = telemetry.get("defect_count", 0)
            yield_score = telemetry.get("wafer_yield_score", 100.0)
            critical_cnt = telemetry.get("critical_violations", 0)
            
            observations.append(f"OpenCV 5 identified {defect_cnt} structural anomalies (Yield: {yield_score}%).")
            if critical_cnt > 0:
                observations.append(f"Detected {critical_cnt} critical micro-crack/void breaches.")
                risk_level = "HIGH"
                applicable_policy = "ISO_14644_1"
                action_plan.append({"tool": "emergency_halt_conveyor", "args": {"zone_id": "CLEANROOM_LINE_1", "reason": "Wafer micro-crack exceeds ISO 14644 yield limits"}})
                action_plan.append({"tool": "trigger_aws_sns_alert", "args": {"target_role": "QA_LEAD", "priority": "HIGH", "message": f"Wafer contamination breach detected. Batch quarantined.", "incident_payload": telemetry}})
            else:
                observations.append("Wafer defect rate is within nominal silicon tolerance.")

        elif channel_id == "robot":
            danger_breached = telemetry.get("danger_zone_breached", False)
            max_speed = telemetry.get("max_arm_velocity_px_s", 0)
            intrusions = telemetry.get("active_intrusions", [])
            
            observations.append(f"Optical Flow velocity magnitude: {max_speed} px/s across robotic envelope.")
            if danger_breached:
                risk_level = "CRITICAL"
                observations.append(f"OSHA Point-of-Operation safety perimeter breached by {len(intrusions)} personnel.")
                applicable_policy = "OSHA_1910_212"
                action_plan.append({"tool": "emergency_halt_conveyor", "args": {"zone_id": "ROBOT_WORKCELL_04", "reason": "Worker intrusion into active articulated arm envelope"}})
                action_plan.append({"tool": "trigger_aws_sns_alert", "args": {"target_role": "FLOOR_SAFETY_MARSHAL", "priority": "CRITICAL", "message": "Emergency Arm Interlock engaged due to personnel proximity.", "incident_payload": telemetry}})
            else:
                observations.append("Dynamic safety perimeter is clear of unauthorized objects.")

        elif channel_id == "chemical":
            spill_detected = telemetry.get("spill_detected", False)
            spill_area = telemetry.get("total_spill_area_px", 0)
            rate = telemetry.get("expansion_rate_px_per_frame", 0)

            observations.append(f"Chemical bay fluid contour area: {spill_area} px² (Expansion rate: {rate} px/frame).")
            if spill_detected and spill_area > 800:
                risk_level = "CRITICAL"
                observations.append("Hazardous liquid spill detected with positive expansion rate.")
                applicable_policy = "NFPA_704_SPILL"
                action_plan.append({"tool": "engage_hvac_containment", "args": {"room_id": "CHEM_BAY_03", "mode": "NEGATIVE_PRESSURE"}})
                action_plan.append({"tool": "reroute_agv_fleet", "args": {"agv_id": "AGV-101", "detour_waypoint": "CORRIDOR_NORTH_4", "hazard_coords": [250, 300, 180, 120]}})
                action_plan.append({"tool": "trigger_aws_sns_alert", "args": {"target_role": "HAZMAT_DISPATCH", "priority": "CRITICAL", "message": f"Chemical leak in Bay 03. HVAC sealed. AGVs detour.", "incident_payload": telemetry}})

        elif channel_id == "ppe":
            violation_cnt = telemetry.get("violation_count", 0)
            workers = telemetry.get("workers", [])
            observations.append(f"Airlock monitoring identified {len(workers)} workers; {violation_cnt} compliance violations.")
            if violation_cnt > 0:
                risk_level = "MEDIUM"
                observations.append("Worker missing mandatory hardhat or high-vis attire at security turnstile.")
                applicable_policy = "OSHA_1910_132"
                action_plan.append({"tool": "trigger_aws_sns_alert", "args": {"target_role": "SECURITY_GATE", "priority": "MEDIUM", "message": "Access denied at Airlock Gate. PPE violation.", "incident_payload": telemetry}})

        # Step 3: Actuate Physical & Cloud Tools
        for planned_action in action_plan:
            tool_name = planned_action["tool"]
            args = planned_action["args"]
            if hasattr(actuator_tools, tool_name):
                func = getattr(actuator_tools, tool_name)
                res = func(**args)
                tool_results.append({"tool": tool_name, "execution": res})

        # Calculate agent reasoning latency
        reasoning_latency_ms = (time.perf_counter() - cycle_start) * 1000

        # Construct Agent Thought Payload
        thought_package = {
            "cycle_id": cycle_id,
            "channel": channel_id,
            "timestamp": time.time(),
            "timestamp_iso": time.strftime("%H:%M:%S"),
            "risk_assessment": risk_level,
            "observations": observations,
            "policy_applied": {
                "id": applicable_policy,
                "text": self.regulatory_policies.get(applicable_policy, "Standard Operating Baseline") if applicable_policy else None
            },
            "planned_actions": action_plan,
            "actuations_executed": tool_results,
            "agent_latency_ms": round(reasoning_latency_ms, 2),
            "autonomous_status": "INTERVENTION_EXECUTED" if tool_results else "OBSERVING_NOMINAL"
        }

        # Store in rolling reasoning log
        self.reasoning_log.insert(0, thought_package)
        if len(self.reasoning_log) > 50:
            self.reasoning_log.pop()

        return thought_package

    def get_recent_thoughts(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self.reasoning_log[:limit]

# Global agent singleton
agent_engine = AgenticVisionEngine()
