# Testing Instructions

## Prerequisites

- Python 3.11+
- pip
- Optional: Docker
- Internet access only if you want to install dependencies

## Quickstart

1. Clone the repository:

```bash
git clone https://github.com/ShivangiBhargava/Aegis-Vision-AI.git
cd Aegis-Vision-AI
```

2. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start the backend server:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

5. Open the application in a browser:

- http://localhost:8000

6. Optional Docker run:

```bash
docker-compose up --build
```

## Testing Checklist

### A. System health check

Open:

- http://127.0.0.1:8000/api/status

Expected result:

- System name is displayed
- OpenCV version is 5.x
- AWS mode is either `LIVE_AWS` or `SIMULATED_AWS_CLOUD`
- Active channels include `wafer`, `robot`, `chemical`, and `ppe`

Command:

```bash
curl -s http://127.0.0.1:8000/api/status
```

### B. Live telemetry validation

Test each vision channel:

- http://127.0.0.1:8000/api/telemetry/wafer
- http://127.0.0.1:8000/api/telemetry/robot
- http://127.0.0.1:8000/api/telemetry/chemical
- http://127.0.0.1:8000/api/telemetry/ppe

Expected result:

- Returns telemetry data for the selected channel
- Includes detection metrics such as `defect_count`, `violation_count`, `latency`, risk levels, or spill detection
- Includes an `agent_thought` object and preview image

Command:

```bash
curl -s http://127.0.0.1:8000/api/telemetry/wafer | python -m json.tool
```

### C. Video stream test

Open:

- http://127.0.0.1:8000/api/stream/wafer
- http://127.0.0.1:8000/api/stream/robot
- http://127.0.0.1:8000/api/stream/chemical
- http://127.0.0.1:8000/api/stream/ppe

Expected result:

- MJPEG stream loads successfully
- Video frames render with annotations and overlays
- Stream continues to refresh without crashing

### D. Image upload and analysis

Use the upload endpoint:

```http
POST http://127.0.0.1:8000/api/upload-and-analyze
```

Form fields:

- `file`: uploaded image
- `mode`: `wafer`, `robot`, `chemical`, or `ppe`

Expected result:

- Image is processed by the relevant pipeline
- Telemetry is returned with inspection metrics
- Agentic reasoning evaluates the image
- Processed image preview is returned
- Forensic artifact is uploaded to simulated AWS storage

Example using curl:

```bash
curl -X POST "http://127.0.0.1:8000/api/upload-and-analyze" -F "file=@sample.jpg" -F "mode=wafer"
```

### E. Agentic reasoning and actuation

Check recent agent thoughts:

- http://127.0.0.1:8000/api/agent/thoughts

Check actuator history:

- http://127.0.0.1:8000/api/actuators/history

Manual actuation trigger:

- http://127.0.0.1:8000/api/actuators/trigger?tool=emergency_halt&param1=ZONE_JUDGE&param2=Judge%20Manual%20Test

Expected result:

- Autonomous reasoning produces a risk assessment and recommended actions
- Actuators are triggered and logged
- Status indicates successful execution

### F. COOL benchmark validation

Open:

- http://127.0.0.1:8000/api/cool/benchmark

Expected result:

- Returns benchmark comparison between standard OpenCV and COOL-optimized OpenCV
- Speedup factor is greater than 1
- COOL path shows lower latency than standard OpenCV

Command:

```bash
curl -s http://127.0.0.1:8000/api/cool/benchmark
```

### G. AWS cloud simulation validation

Open:

- http://127.0.0.1:8000/api/aws/status
- http://127.0.0.1:8000/api/incidents

Expected result:

- AWS mode is reported as `SIMULATED_AWS_CLOUD` when no live credentials are configured
- Services such as S3, CloudWatch, IoT Core, and DynamoDB show `ONLINE`
- Incident logs are recorded in the simulator

### H. Audit report generation

Open:

- http://127.0.0.1:8000/api/generate-report?channel=wafer

Expected result:

- A structured compliance report is returned
- Includes `report_id`, generated timestamp, facility, executed actions, and recent thoughts

### I. Automated test suite

Run:

```bash
python -m unittest tests/test_pipeline.py
```

Expected result:

- All pipeline, agent, actuator, and AWS simulation tests pass
- Example output should show `OK`

## Success Criteria for Evaluation

- Application starts successfully with no missing dependency errors
- At least one channel produces valid telemetry and image output
- Agentic reasoning engine executes and logs actions
- COOL benchmark returns measurable acceleration
- AWS simulation or live integration is visible and functional
- Upload and analysis flow works without crash
- The interface loads and reflects the dashboard and digital twin state

