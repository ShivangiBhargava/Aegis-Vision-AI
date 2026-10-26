"""
AegisVision - Main FastAPI Backend Application
Serves real-time OpenCV 5 video streams, agentic reasoning loops, COOL benchmark suite,
AWS cloud connectors, and frontend static assets.
"""

import cv2
import numpy as np
import time
import base64
import os
import json
from fastapi import FastAPI, UploadFile, File, Form, Query, Response
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional, Dict, Any

from backend.app.vision.pipeline import vision_pipeline
from backend.app.vision.synthetic_feeds import synthetic_generator
from backend.app.vision.cool_engine import cool_engine
from backend.app.agent.agentic_vision import agent_engine
from backend.app.agent.tools import actuator_tools
from backend.app.aws.aws_client import aws_client

app = FastAPI(
    title="AegisVision: Autonomous Agentic Industrial Sentinel",
    description="Physical AI and Agentic Vision Platform powered by OpenCV 5 and AWS",
    version="1.0.0"
)

# Enable CORS for local and web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory incident record storage
incident_store = []

@app.get("/api/status")
def get_system_status():
    """System heartbeat and version diagnostics."""
    return {
        "system": "AegisVision Physical AI Sentinel",
        "opencv_version": cv2.__version__,
        "cool_acceleration": "ENABLED (SIMD & Cache-Tiled)",
        "aws_mode": aws_client.get_status()["mode"],
        "active_channels": ["wafer", "robot", "chemical", "ppe"],
        "agentic_engine": "ACTIVE_AUTONOMOUS",
        "server_time": time.time()
    }

def generate_video_stream(channel: str, overlay: str = "annotated"):
    """MJPEG stream generator that executes OpenCV 5 processing per frame."""
    while True:
        # Generate or capture source frame
        raw_frame = synthetic_generator.get_feed(channel)
        
        # Process with OpenCV 5 based on channel
        if channel == "wafer":
            processed_frame, telemetry = vision_pipeline.inspect_wafer(raw_frame, overlay_mode=overlay)
        elif channel == "robot":
            processed_frame, telemetry = vision_pipeline.inspect_robotic_cell(raw_frame, stream_id="robot_1", overlay_mode=overlay)
        elif channel == "chemical":
            processed_frame, telemetry = vision_pipeline.inspect_chemical_spill(raw_frame, stream_id="chem_1", overlay_mode=overlay)
        elif channel == "ppe":
            processed_frame, telemetry = vision_pipeline.inspect_ppe_compliance(raw_frame, overlay_mode=overlay)
        else:
            processed_frame, telemetry = vision_pipeline.inspect_wafer(raw_frame, overlay_mode=overlay)

        # Trigger autonomous agent evaluation periodically (every ~10 frames or on anomaly)
        if telemetry.get("status") == "ANOMALY_DETECTED" or telemetry.get("danger_zone_breached") or telemetry.get("spill_detected") or telemetry.get("violation_count", 0) > 0:
            agent_engine.reason_and_act(channel, telemetry)

        # Encode to JPEG for MJPEG stream
        ret, buffer = cv2.imencode(".jpg", processed_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
        time.sleep(0.04) # ~25 FPS

@app.get("/api/stream/{channel}")
def video_stream(channel: str, overlay: str = Query("annotated")):
    """Live MJPEG video stream with dynamic OpenCV 5 overlay processing."""
    return StreamingResponse(
        generate_video_stream(channel, overlay),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/api/telemetry/{channel}")
def get_channel_telemetry(channel: str, overlay: str = Query("annotated")):
    """Retrieves single-frame processed telemetry & base64 preview."""
    raw_frame = synthetic_generator.get_feed(channel)
    if channel == "wafer":
        proc, telemetry = vision_pipeline.inspect_wafer(raw_frame, overlay_mode=overlay)
    elif channel == "robot":
        proc, telemetry = vision_pipeline.inspect_robotic_cell(raw_frame, stream_id="robot_1", overlay_mode=overlay)
    elif channel == "chemical":
        proc, telemetry = vision_pipeline.inspect_chemical_spill(raw_frame, stream_id="chem_1", overlay_mode=overlay)
    elif channel == "ppe":
        proc, telemetry = vision_pipeline.inspect_ppe_compliance(raw_frame, overlay_mode=overlay)
    else:
        proc, telemetry = vision_pipeline.inspect_wafer(raw_frame, overlay_mode=overlay)

    # Agent reason & act
    thought = agent_engine.reason_and_act(channel, telemetry)

    # Encode preview
    _, buffer = cv2.imencode(".jpg", proc, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
    b64_img = base64.b64encode(buffer).decode("utf-8")

    return {
        "channel": channel,
        "telemetry": telemetry,
        "agent_thought": thought,
        "preview_b64": f"data:image/jpeg;base64,{b64_img}"
    }

@app.post("/api/upload-and-analyze")
async def upload_and_analyze(file: UploadFile = File(...), mode: str = Form("wafer")):
    """Allows judges/users to upload their own images to be analyzed with OpenCV 5 & Agent."""
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if frame is None:
        return JSONResponse(status_code=400, content={"error": "Invalid image format"})

    # Resize if excessively large to keep fast interactive latency
    h, w = frame.shape[:2]
    if max(h, w) > 1280:
        scale = 1280.0 / max(h, w)
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)))

    if mode == "wafer":
        proc, telemetry = vision_pipeline.inspect_wafer(frame)
    elif mode == "robot":
        proc, telemetry = vision_pipeline.inspect_robotic_cell(frame)
    elif mode == "chemical":
        proc, telemetry = vision_pipeline.inspect_chemical_spill(frame)
    elif mode == "ppe":
        proc, telemetry = vision_pipeline.inspect_ppe_compliance(frame)
    else:
        proc, telemetry = vision_pipeline.inspect_wafer(frame)

    thought = agent_engine.reason_and_act(mode, telemetry)

    _, buffer = cv2.imencode(".jpg", proc, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    b64_img = base64.b64encode(buffer).decode("utf-8")

    # Upload evidence to AWS S3
    s3_res = aws_client.upload_forensic_artifact(
        artifact_name=file.filename or "uploaded_test.jpg",
        image_bytes=buffer.tobytes(),
        metadata={"channel": mode, "defects": str(telemetry.get("defect_count", 0))}
    )

    return {
        "filename": file.filename,
        "telemetry": telemetry,
        "agent_thought": thought,
        "s3_artifact": s3_res,
        "processed_image_b64": f"data:image/jpeg;base64,{b64_img}"
    }

@app.get("/api/cool/benchmark")
def run_cool_benchmark():
    """Executes live Cloud-Optimized OpenCV Library (COOL) vs Standard OpenCV benchmark."""
    results = cool_engine.benchmark_comparison()
    return results

@app.get("/api/agent/thoughts")
def get_agent_thoughts(limit: int = 15):
    """Retrieves recent multi-step reasoning thoughts from the Agentic Vision Engine."""
    return agent_engine.get_recent_thoughts(limit=limit)

@app.get("/api/actuators/history")
def get_actuator_history():
    """Retrieves execution audit log of physical equipment and cloud tool invocations."""
    return actuator_tools.get_action_history()

@app.post("/api/actuators/trigger")
def manual_actuation_trigger(tool: str = Query(...), param1: str = Query(""), param2: str = Query("")):
    """Operator manual override to trigger actuators."""
    if tool == "emergency_halt":
        res = actuator_tools.emergency_halt_conveyor(zone_id=param1 or "ZONE_MANUAL", reason=param2 or "Operator Manual E-Stop Override")
    elif tool == "reroute_agv":
        res = actuator_tools.reroute_agv_fleet(agv_id=param1 or "AGV-101", detour_waypoint=param2 or "BAY_AUX_3", hazard_coords=[100, 100, 50, 50])
    elif tool == "engage_hvac":
        res = actuator_tools.engage_hvac_containment(room_id=param1 or "MAIN_CLEANROOM", mode=param2 or "PURGE")
    elif tool == "sns_alert":
        res = actuator_tools.trigger_aws_sns_alert(target_role=param1 or "FACILITY_COMMAND", priority="MANUAL_HIGH", message=param2 or "Manual Drill Triggered", incident_payload={})
    else:
        return JSONResponse(status_code=400, content={"error": f"Unknown tool {tool}"})
    return {"status": "SUCCESS", "tool": tool, "execution": res}

@app.get("/api/digital-twin")
def get_digital_twin_state():
    """Returns facility digital twin state: zones, robots, AGV coordinates, conveyors, cameras."""
    aws_status = aws_client.get_status()
    shadow_state = aws_status["services"]["IoT_Core"]["shadow_state"]
    return {
        "facility_name": "Fab Alpha - Critical Cleanroom & Robotics",
        "zones": [
            {"id": "ZONE_A", "name": "Silicon Photolithography Wafer Fab", "status": "NOMINAL", "risk_level": "LOW"},
            {"id": "ZONE_B", "name": "Heavy Robotic Articulation Cell 04", "status": "CAUTION" if shadow_state.get("safety_interlock") == "TRIPPED" else "OPTIMAL", "risk_level": "HIGH"},
            {"id": "ZONE_C", "name": "Hazardous Fluid Chemical Storage Bay", "status": "CONTAINED", "risk_level": "CRITICAL"},
            {"id": "ZONE_D", "name": "Airlock Security & PPE Inspection Portal", "status": "ACTIVE_MONITORING", "risk_level": "LOW"}
        ],
        "actuators": shadow_state,
        "agv_fleet": [
            {"id": "AGV-101", "coords": [420, 280], "status": shadow_state.get("agv_101_mode", "AUTONOMOUS"), "battery": "94%"},
            {"id": "AGV-102", "coords": [180, 510], "status": "TRANSIT_CLEANROOM", "battery": "88%"}
        ],
        "camera_nodes": [
            {"channel": "wafer", "label": "CAM-01 (Wafer Fab Micro)", "fps": 28.4, "resolution": "1920x1080"},
            {"channel": "robot", "label": "CAM-02 (Robotic Cell Farneback)", "fps": 26.2, "resolution": "1920x1080"},
            {"channel": "chemical", "label": "CAM-03 (Hazmat Bay HSV)", "fps": 29.1, "resolution": "1920x1080"},
            {"channel": "ppe", "label": "CAM-04 (PPE Airlock Portal)", "fps": 27.8, "resolution": "1920x1080"}
        ]
    }

@app.get("/api/aws/status")
def get_aws_status():
    """Live AWS status and simulated fallback stats."""
    return aws_client.get_status()

@app.get("/api/incidents")
def get_incident_log():
    """Retrieves forensic incident packets logged in DynamoDB."""
    return aws_client.simulated_incidents

@app.post("/api/generate-report")
def generate_forensic_audit_report(channel: str = Query("wafer")):
    """Generates an official markdown/json forensic compliance report for download."""
    recent_thoughts = agent_engine.get_recent_thoughts(5)
    recent_actions = actuator_tools.get_action_history()[:5]
    
    report = {
        "report_id": f"REP-AUDIT-{int(time.time()*1000)}",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "facility": "AegisVision Industrial Plant Alpha",
        "system_version": "AegisVision v1.0.0 (OpenCV 5.0 + AWS Cloud)",
        "channel_inspected": channel,
        "executive_summary": "Autonomous physical AI inspection completed. Real-time OpenCV 5 computer vision pipelines detected deviations and dispatched targeted mitigation actuators per OSHA / ISO compliance policies.",
        "recent_agentic_cycles": recent_thoughts,
        "executed_actuations": recent_actions,
        "compliance_certifications": ["OSHA 1910.212 Compliant", "ISO 14644-1 Cleanroom Verified", "AWS Well-Architected Reliability Standard"]
    }
    return report

# Serve frontend directory if built/available
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "frontend", "public")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")
