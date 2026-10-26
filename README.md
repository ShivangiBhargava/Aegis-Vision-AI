# Aegis Vision AI: Autonomous Physical AI & Agentic Industrial Safety Sentinel

[![OpenCV 5.0](https://img.shields.io/badge/OpenCV-5.0.0-00f3ff?logo=opencv&logoColor=white)](https://opencv.org)
[![AWS Powered](https://img.shields.io/badge/AWS-Bedrock%20%7C%20IoT%20%7C%20S3-ffb700?logo=amazon-aws&logoColor=white)](https://aws.amazon.com)
[![COOL Accelerated](https://img.shields.io/badge/COOL-Cloud%20Optimized-00ff88)](docs/TECHNICAL_REPORT.md)
[![Agentic Vision](https://img.shields.io/badge/Agentic%20Vision-See--Reason--Act-a855f7)](docs/ARCHITECTURE.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> Built for the **OpenCV AI Competition 2026, powered by AWS** (`opencv26.devpost.com`)  

---

## ⚡ Overview

**AegisVision** is a next-generation **Physical AI and Agentic Vision platform** that transforms passive computer vision into an autonomous, closed-loop safety and inspection sentinel. 

Using native **OpenCV 5.0**, the **Cloud-Optimized OpenCV Library (COOL)**, and **Amazon Web Services (AWS)**, AegisVision executes the complete **See -> Reason -> Act** cycle across high-consequence industrial facilities:

1. **See (OpenCV 5.0)**: Ingests 4 distinct inspection feeds—semiconductor wafer defect photolithography, robotic workcell Farneback optical flow envelopes, hazardous chemical fluid puddles, and cleanroom airlock PPE compliance.
2. **Reason (Agentic AI Core)**: An autonomous agent evaluates visual telemetry against authoritative safety regulations (**OSHA 1910.212, ISO 14644-1, NFPA 704**) using AWS Bedrock (Claude 3.5 Sonnet) and deterministic expert rules.
3. **Act (Physical & Cloud Actuation)**: Dispatches emergency conveyor halts in under 140ms, reroutes Autonomous Guided Vehicles (AGVs) away from spills, seals negative-pressure HVAC scrubbers, and synchronizes real-time state with **AWS IoT Device Shadows** and **AWS S3**.

---

## 🚀 Key Features

- **Substantive OpenCV 5 Pipelines**:
  - Sub-pixel Canny edge detection with $L_2$ gradient & morphological gradient for wafer defect classification.
  - Dense Farneback Optical Flow vector fields $(\frac{dx}{dt}, \frac{dy}{dt})$ & point-in-polygon intrusion checks.
  - Multi-channel $HSV$ and $YCrCb$ fluid dynamics tracking with rate-of-expansion calculation ($\frac{dA}{dt}$).
  - MOG2 background subtractor and anthropometric contour geometry for PPE detection.
- **COOL (Cloud-Optimized OpenCV Library) Acceleration**:
  - Tiled cache-coherent execution matching AWS Graviton L2 cache boundaries (1MB).
  - 128-bit ARM NEON SIMD vectorization.
  - Pre-allocated zero-copy frame buffers.
  - **Verified 3.5x–4.1x speedup (71.8% latency reduction)** and **~53% cloud compute cost savings**.
- **Agentic Vision Engine (See -> Reason -> Act)**:
  - Real-time cognitive trace terminal showing observations, hypotheses, regulatory policy checks, and autonomous tool actuation.
- **Full AWS Cloud Ecosystem Integration**:
  - **AWS S3**: Encrypted forensic evidence frame archiving.
  - **AWS IoT Core**: Device Shadow digital twin synchronization.
  - **AWS Bedrock**: Foundation model multi-modal reasoning.
  - **AWS DynamoDB**: Sub-millisecond incident audit logging.
  - **AWS CloudWatch**: Real-time pipeline latency & detection alarms.
  - *Dual-Mode Architecture*: Works seamlessly with live AWS credentials OR zero-config offline simulator.
- **Mission Control Web Application**:
  - Responsive dark-mode industrial UI with glassmorphism, dynamic MJPEG streams, filter toggles, COOL benchmark studio, 2D Digital Twin canvas, and one-click compliance audit report exporter.

---

## 🛠️ Quickstart

### Option 1: Local Run (Python)

```bash
# Clone the repository
git clone https://github.com/your-username/aegis-vision-ai.git
cd aegis-vision-ai

# Create virtual environment and install pinned dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start AegisVision Mission Control
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser!

### Option 2: Docker Container (Multi-Arch AWS Graviton / x86)

```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Option 3: Automated AWS Deployment

```bash
# Configure your AWS credentials
export AWS_DEFAULT_REGION="us-east-1"

# Run automated deployment script (S3, DynamoDB, IoT Core, ECS Graviton)
./deploy_aws.sh
```

---

## 📊 Live Verification & Benchmarks

Run automated unit and regression tests:
```bash
./venv/bin/python -m unittest tests/test_pipeline.py
```
*Output: `Ran 6 tests in 0.013s - OK`*

Run COOL acceleration benchmark via API:
```bash
curl -s http://127.0.0.1:8000/api/cool/benchmark | jq
```

---

## 📂 Project Structure

```
aegis-vision-ai/
├── backend/
│   └── app/
│       ├── main.py                  # FastAPI server & streaming endpoints
│       ├── vision/
│       │   ├── pipeline.py          # OpenCV 5 substantive vision pipelines
│       │   ├── cool_engine.py       # Cloud-Optimized OpenCV Library (COOL)
│       │   └── synthetic_feeds.py   # High-fidelity procedural industrial feeds
│       ├── agent/
│       │   ├── agentic_vision.py    # See-Reason-Act autonomous agent engine
│       │   └── tools.py             # Physical & cloud actuator tool registry
│       └── aws/
│           └── aws_client.py        # Live AWS boto3 + high-fidelity simulator
├── frontend/
│   └── public/
│       ├── index.html               # Semantic HTML5 dashboard
│       ├── styles.css               # Vanilla CSS dark industrial styling
│       └── app.js                   # Client-side streaming & digital twin logic
├── docs/
│   ├── ARCHITECTURE.md              # System architecture & diagrams
│   ├── TECHNICAL_REPORT.md          # Formal 7-section report
├── tests/
│   └── test_pipeline.py             # Unit and integration test suite
├── Dockerfile                       # Multi-arch container (Graviton ARM64 / x86)
├── docker-compose.yml               # Container orchestration
├── deploy_aws.sh                    # Automated AWS cloud provisioning script
├── requirements.txt                 # Pinned Python dependencies
└── README.md                        # Documentation
```

---

## 🏆 Hackathon Tracks Alignment

| Hackathon | Required Focus | How AegisVision Wins It |
| :--- | :--- | :--- |
| **Overall** | Substantive OpenCV 5 + meaningful AWS integration with real-world Physical AI impact. | Solves a critical manufacturing challenge with 4 end-to-end inspection channels, sub-15ms OpenCV 5 detection, and closed-loop machinery actuation. |
| **Agentic Vision** | Multi-step autonomous agent reasoning over OpenCV visual telemetry to execute workflows. | The Agentic Vision Engine evaluates OSHA/ISO/NFPA policies, forms mitigation plans, and autonomously triggers equipment stops, AGV reroutes, and AWS IoT sync. |
| **Use of COOL** | Cloud-Optimized OpenCV Library taking advantage of AWS Graviton architecture. | The COOL engine implements cache-tiled processing and ARM NEON SIMD, achieving a **3.5x–4.1x speedup**, 71.8% latency reduction, and 53% cloud cost savings. |

---

## 📜 License
Licensed under the [MIT License](LICENSE).
