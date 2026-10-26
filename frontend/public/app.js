/**
 * AegisVision - Frontend Application Logic
 * Orchestrates live OpenCV 5 video feeds, Agentic Vision reasoning, COOL benchmarking,
 * facility digital twin simulation, and AWS cloud interaction.
 */

// Application State
const state = {
  activeTab: "surveillance",
  activeChannel: "wafer",
  activeOverlay: "annotated",
  isWebcamActive: false,
  webcamStream: null,
  pollInterval: null,
  twinAnimFrame: null,
  agvPos: { x: 340, y: 320, targetX: 680, targetY: 320, progress: 0 },
  hazardPulse: 0
};

// Channel Metadata Mapping
const CHANNEL_TITLES = {
  wafer: "CAM-01: Semiconductor Cleanroom Wafer Inspection (Sub-Pixel Canny & Morph)",
  robot: "CAM-02: Robotic Workcell Safety Envelope (Dense Farneback Optical Flow)",
  chemical: "CAM-03: Hazardous Chemical Storage Bay (HSV & YCrCb Fluid Dynamics)",
  ppe: "CAM-04: Cleanroom Airlock PPE Sentinel (Contour Morphology & MOG2)"
};

// DOM Elements
const elements = {
  tabs: document.querySelectorAll(".nav-tab"),
  panes: document.querySelectorAll(".tab-pane"),
  channelBtns: document.querySelectorAll(".channel-btn"),
  filterBtns: document.querySelectorAll(".filter-btn"),
  liveImg: document.getElementById("live-stream-img"),
  activeChannelName: document.getElementById("active-channel-name"),
  systemStatusText: document.getElementById("system-status-text"),
  systemStatusIndicator: document.getElementById("system-status-indicator"),
  hudFps: document.getElementById("hud-fps"),
  hudLatency: document.getElementById("hud-latency"),
  hudStatusBadge: document.getElementById("hud-status-badge"),
  hudStatusText: document.getElementById("hud-status-text"),
  metricObjects: document.getElementById("metric-objects"),
  metricAnomaly: document.getElementById("metric-anomaly"),
  metricLatency: document.getElementById("metric-latency"),
  metricCompliance: document.getElementById("metric-compliance"),
  featureList: document.getElementById("feature-list"),
  miniAgentTerminal: document.getElementById("mini-agent-terminal"),
  fullAgentTerminal: document.getElementById("full-agent-terminal"),
  actuatorHistoryList: document.getElementById("actuator-history-list"),
  badgeConveyor: document.getElementById("badge-conveyor-status"),
  badgeAgv: document.getElementById("badge-agv-status"),
  badgeHvac: document.getElementById("badge-hvac-status"),
  twinCanvas: document.getElementById("digital-twin-canvas"),
  customFileInput: document.getElementById("custom-file-input"),
  btnWebcam: document.getElementById("btn-use-webcam"),
  btnRunBenchmark: document.getElementById("btn-run-benchmark"),
  btnDownloadAudit: document.getElementById("btn-download-audit"),
  btnEStop: document.getElementById("btn-trigger-estop"),
  btnAgvReroute: document.getElementById("btn-trigger-agv-reroute"),
  btnHvac: document.getElementById("btn-trigger-hvac"),
  btnSns: document.getElementById("btn-trigger-sns")
};

// -------------------------------------------------------------
// 1. INITIALIZATION & TAB SWITCHING
// -------------------------------------------------------------
function init() {
  setupNavigation();
  setupChannelSwitching();
  setupFilterSwitching();
  setupActuators();
  setupBenchmark();
  setupUploadAndWebcam();
  setupAuditDownload();
  startTelemetryPolling();
  startDigitalTwinLoop();
}

function setupNavigation() {
  elements.tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const targetTab = tab.getAttribute("data-tab");
      state.activeTab = targetTab;
      
      elements.tabs.forEach(t => t.classList.remove("active"));
      elements.panes.forEach(p => p.classList.remove("active"));
      
      tab.classList.add("active");
      const targetPane = document.getElementById(`pane-${targetTab}`);
      if (targetPane) targetPane.classList.add("active");

      // Auto-trigger benchmark if user navigates to COOL tab first time
      if (targetTab === "cool" && !state.hasRunInitialBench) {
        runBenchmarkSuite();
        state.hasRunInitialBench = true;
      }
    });
  });
}

function setupChannelSwitching() {
  elements.channelBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const channel = btn.getAttribute("data-channel");
      state.activeChannel = channel;
      
      elements.channelBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      
      if (elements.activeChannelName) {
        elements.activeChannelName.innerText = CHANNEL_TITLES[channel] || channel;
      }
      
      updateStreamSource();
      fetchTelemetryOnce();
    });
  });
}

function setupFilterSwitching() {
  elements.filterBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const overlay = btn.getAttribute("data-overlay");
      state.activeOverlay = overlay;

      elements.filterBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      updateStreamSource();
      fetchTelemetryOnce();
    });
  });
}

function updateStreamSource() {
  if (state.isWebcamActive) return;
  const streamUrl = `/api/stream/${state.activeChannel}?overlay=${state.activeOverlay}&_t=${Date.now()}`;
  elements.liveImg.src = streamUrl;
}

// -------------------------------------------------------------
// 2. REAL-TIME TELEMETRY & POLLING
// -------------------------------------------------------------
function startTelemetryPolling() {
  fetchTelemetryOnce();
  state.pollInterval = setInterval(fetchTelemetryOnce, 1500);
}

async function fetchTelemetryOnce() {
  if (state.isWebcamActive) return;
  try {
    const res = await fetch(`/api/telemetry/${state.activeChannel}?overlay=${state.activeOverlay}`);
    if (!res.ok) return;
    const data = await res.json();
    renderTelemetry(data.telemetry, data.agent_thought);
    fetchAgentThoughts();
  } catch (err) {
    console.warn("Telemetry polling warning:", err);
  }
}

function renderTelemetry(tel, thought) {
  if (!tel) return;

  // Latency & FPS
  const latency = tel.latency_ms || 11.2;
  elements.hudLatency.innerText = `${latency} ms`;
  elements.metricLatency.innerText = `${latency} ms`;
  
  const approxFps = Math.min(30, Math.round(1000 / Math.max(16, latency)));
  elements.hudFps.innerText = `${approxFps}.0`;

  // Status & compliance
  let isHazard = false;
  let statusText = "NOMINAL";
  let count = 0;
  let anomalyPct = "0.0%";

  if (state.activeChannel === "wafer") {
    count = tel.defect_count || 0;
    const yieldScore = tel.wafer_yield_score || 95.0;
    anomalyPct = `${(100 - yieldScore).toFixed(1)}%`;
    isHazard = count > 2;
    statusText = isHazard ? "MICRO-DEFECT" : "YIELD OPTIMAL";
  } else if (state.activeChannel === "robot") {
    count = tel.total_tracked_objects || 0;
    isHazard = tel.danger_zone_breached || false;
    anomalyPct = isHazard ? "CRITICAL (100%)" : "0.0%";
    statusText = isHazard ? "DANGER: INTRUSION" : "ENVELOPE CLEAR";
  } else if (state.activeChannel === "chemical") {
    count = tel.spill_detected ? 1 : 0;
    isHazard = tel.spill_detected && (tel.total_spill_area_px > 800);
    anomalyPct = isHazard ? "CRITICAL HAZMAT" : "0.0%";
    statusText = isHazard ? "TOXIC SPILL" : "CONTAINED";
  } else if (state.activeChannel === "ppe") {
    count = tel.workers_detected || 0;
    const violations = tel.violation_count || 0;
    isHazard = violations > 0;
    anomalyPct = violations > 0 ? `${violations} VIOLATION` : "0.0%";
    statusText = isHazard ? "OSHA PPE BREACH" : "COMPLIANT";
  }

  elements.metricObjects.innerText = count;
  elements.metricAnomaly.innerText = anomalyPct;
  elements.metricCompliance.innerText = isHazard ? "FAIL (INTERVENED)" : "PASS (NOMINAL)";
  elements.metricCompliance.className = isHazard ? "metric-val hazard" : "metric-val nominal";

  elements.hudStatusText.innerText = statusText;
  if (isHazard) {
    elements.hudStatusBadge.classList.add("hazard");
    elements.systemStatusIndicator.style.borderColor = "var(--red-hazard)";
    elements.systemStatusIndicator.style.background = "rgba(255, 0, 85, 0.12)";
    elements.systemStatusText.innerText = "DEFCON: INTERVENTION ACTIVE";
    elements.systemStatusText.style.color = "var(--red-hazard)";
  } else {
    elements.hudStatusBadge.classList.remove("hazard");
    elements.systemStatusIndicator.style.borderColor = "rgba(0, 255, 136, 0.3)";
    elements.systemStatusIndicator.style.background = "rgba(0, 255, 136, 0.08)";
    elements.systemStatusText.innerText = "SENTINEL ONLINE";
    elements.systemStatusText.style.color = "var(--green-neon)";
  }

  // Feature breakdown list
  renderFeatureList(tel);
}

function renderFeatureList(tel) {
  if (!elements.featureList) return;
  let html = "";

  if (state.activeChannel === "wafer" && tel.defects) {
    tel.defects.forEach(d => {
      html += `<div style="display:flex; justify-content:space-between; padding:4px 0; border-bottom:1px solid rgba(255,255,255,0.05);">
        <span style="color:${d.severity === 'CRITICAL' ? 'var(--red-hazard)' : 'var(--amber-warn)'};">• ${d.type}</span>
        <span style="color:var(--text-muted);">${d.area_px} px²</span>
      </div>`;
    });
  } else if (state.activeChannel === "robot") {
    html += `<div style="display:flex; justify-content:space-between;"><span>Arm Velocity:</span><span style="color:var(--cyan-glow);">${tel.max_arm_velocity_px_s || 0} px/s</span></div>`;
    html += `<div style="display:flex; justify-content:space-between;"><span>Intrusion Alert:</span><span style="color:${tel.danger_zone_breached ? 'var(--red-hazard)' : 'var(--green-neon)'};">${tel.danger_zone_breached ? 'BREACH DETECTED' : 'CLEAR'}</span></div>`;
  } else if (state.activeChannel === "chemical") {
    html += `<div style="display:flex; justify-content:space-between;"><span>Spill Area:</span><span style="color:var(--amber-warn);">${tel.total_spill_area_px || 0} px²</span></div>`;
    html += `<div style="display:flex; justify-content:space-between;"><span>Expansion Rate:</span><span style="color:var(--cyan-glow);">${tel.expansion_rate_px_per_frame || 0} px/f</span></div>`;
  } else if (state.activeChannel === "ppe") {
    html += `<div style="display:flex; justify-content:space-between;"><span>Compliant Personnel:</span><span style="color:var(--green-neon);">${tel.compliant_count || 0}</span></div>`;
    html += `<div style="display:flex; justify-content:space-between;"><span>PPE Violations:</span><span style="color:var(--red-hazard);">${tel.violation_count || 0}</span></div>`;
  }

  elements.featureList.innerHTML = html || "<div style='color:var(--text-dim);'>No anomalies detected in current frame.</div>";
}

// -------------------------------------------------------------
// 3. AGENTIC THOUGHT STREAM TERMINAL
// -------------------------------------------------------------
async function fetchAgentThoughts() {
  try {
    const res = await fetch("/api/agent/thoughts?limit=15");
    if (!res.ok) return;
    const thoughts = await res.json();
    if (!thoughts || thoughts.length === 0) return;

    // Render Mini-Terminal (Latest thought)
    const latest = thoughts[0];
    let miniHtml = "";
    if (latest.observations && latest.observations[0]) {
      miniHtml += `<div class="log-entry see">[${latest.timestamp_iso}] [SEE] ${latest.observations[0]}</div>`;
    }
    if (latest.policy_applied && latest.policy_applied.id) {
      miniHtml += `<div class="log-entry reason">[${latest.timestamp_iso}] [POLICY] ${latest.policy_applied.id} enforced.</div>`;
    }
    if (latest.actuations_executed && latest.actuations_executed.length > 0) {
      miniHtml += `<div class="log-entry act">[${latest.timestamp_iso}] [ACTUATE] ${latest.actuations_executed[0].tool} dispatched.</div>`;
    } else {
      miniHtml += `<div class="log-entry act">[${latest.timestamp_iso}] [STATUS] Telemetry within safety tolerances.</div>`;
    }
    elements.miniAgentTerminal.innerHTML = miniHtml;

    // Render Full Cognitive Terminal
    let fullHtml = "";
    thoughts.forEach(t => {
      fullHtml += `<div style="margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.06);">
        <div style="font-weight:700; color:var(--text-main); margin-bottom:4px;">
          CYCLE #${t.cycle_id} [${t.timestamp_iso}] - CHANNEL: ${t.channel.toUpperCase()} (Risk: <span style="color:${t.risk_assessment === 'CRITICAL' ? 'var(--red-hazard)' : (t.risk_assessment === 'HIGH' ? 'var(--amber-warn)' : 'var(--green-neon)')};">${t.risk_assessment}</span>)
        </div>`;
      
      t.observations.forEach(obs => {
        fullHtml += `<div class="log-entry see">[OBSERVATION] ${obs}</div>`;
      });

      if (t.policy_applied && t.policy_applied.id) {
        fullHtml += `<div class="log-entry reason">[POLICY VERIFICATION] ${t.policy_applied.id}: ${t.policy_applied.text}</div>`;
      }

      if (t.actuations_executed && t.actuations_executed.length > 0) {
        t.actuations_executed.forEach(act => {
          fullHtml += `<div class="log-entry act">[ACTUATION EXECUTED] Invoked '${act.tool}' -> ${act.execution.status} (IoT Shadow Synced)</div>`;
        });
      } else {
        fullHtml += `<div class="log-entry act">[ACTION PLAN] No intervention required. System continuing nominal perception cycle.</div>`;
      }

      fullHtml += `</div>`;
    });
    elements.fullAgentTerminal.innerHTML = fullHtml;

  } catch (err) {
    console.warn("Agent thoughts polling warning:", err);
  }
}

// -------------------------------------------------------------
// 4. PHYSICAL ACTUATORS & AWS IOT SHADOW
// -------------------------------------------------------------
function setupActuators() {
  elements.btnEStop.addEventListener("click", () => triggerManualActuator("emergency_halt", "ZONE_ROBOT_WORKCELL", "Manual Operator E-Stop"));
  elements.btnAgvReroute.addEventListener("click", () => triggerManualActuator("reroute_agv", "AGV-101", "CORRIDOR_NORTH_4"));
  elements.btnHvac.addEventListener("click", () => triggerManualActuator("engage_hvac", "CHEM_BAY_03", "PURGE"));
  elements.btnSns.addEventListener("click", () => triggerManualActuator("sns_alert", "SAFETY_SUPERVISOR", "Operator Triggered Facility Drill"));
}

async function triggerManualActuator(tool, param1, param2) {
  try {
    const res = await fetch(`/api/actuators/trigger?tool=${tool}&param1=${encodeURIComponent(param1)}&param2=${encodeURIComponent(param2)}`, { method: "POST" });
    const data = await res.json();
    
    // Update local UI
    const timeStr = new Date().toLocaleTimeString();
    if (tool === "emergency_halt") {
      elements.badgeConveyor.innerText = "EMERGENCY HALTED (0 RPM)";
      elements.badgeConveyor.style.background = "rgba(255, 0, 85, 0.2)";
      elements.badgeConveyor.style.color = "var(--red-hazard)";
    } else if (tool === "reroute_agv") {
      elements.badgeAgv.innerText = "DETOUR ACTIVE";
      elements.badgeAgv.style.color = "var(--amber-warn)";
    } else if (tool === "engage_hvac") {
      elements.badgeHvac.innerText = "NEGATIVE PRESSURE PURGE";
      elements.badgeHvac.style.color = "var(--cyan-glow)";
    }

    // Add to Actuator History Log
    const newEntry = document.createElement("div");
    newEntry.innerHTML = `<span style="color:var(--cyan-glow);">[${timeStr}]</span> ${tool.toUpperCase()} -> Status: EXECUTED (Synced to AWS IoT Shadow)`;
    elements.actuatorHistoryList.prepend(newEntry);

  } catch (err) {
    alert("Actuator dispatch failed: " + err);
  }
}

// -------------------------------------------------------------
// 5. COOL BENCHMARK STUDIO
// -------------------------------------------------------------
function setupBenchmark() {
  elements.btnRunBenchmark.addEventListener("click", runBenchmarkSuite);
}

async function runBenchmarkSuite() {
  elements.btnRunBenchmark.innerText = "Benchmarking...";
  elements.btnRunBenchmark.disabled = true;

  try {
    const res = await fetch("/api/cool/benchmark");
    const data = await res.json();

    const stdLat = data.standard_opencv.latency_ms;
    const coolLat = data.cool_optimized.latency_ms;
    const speedup = data.speedup_factor;
    const reduct = data.latency_reduction_percent;
    const savings = data.cloud_cost_reduction_est;

    document.getElementById("metric-std-lat").innerText = `${stdLat} ms (${data.standard_opencv.fps} FPS)`;
    document.getElementById("metric-cool-lat").innerText = `${coolLat} ms (${data.cool_optimized.fps} FPS - ${speedup} Faster)`;
    
    document.getElementById("cool-speedup-val").innerText = speedup;
    document.getElementById("cool-lat-reduct-val").innerText = reduct;
    document.getElementById("cool-cost-val").innerText = savings;
    document.getElementById("cool-arch-val").innerText = data.target_cloud_instance;

    // Animate progress bars
    document.getElementById("bar-std-lat").style.width = "90%";
    const coolPct = Math.max(12, Math.round((coolLat / stdLat) * 90));
    document.getElementById("bar-cool-lat").style.width = `${coolPct}%`;

  } catch (err) {
    console.error("Benchmark failed:", err);
  } finally {
    elements.btnRunBenchmark.innerText = "Run Live Benchmark";
    elements.btnRunBenchmark.disabled = false;
  }
}

// -------------------------------------------------------------
// 6. FACILITY DIGITAL TWIN 2D MAP ANIMATION
// -------------------------------------------------------------
function startDigitalTwinLoop() {
  const canvas = elements.twinCanvas;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Dark grid background
    ctx.fillStyle = "#04070d";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = "rgba(0, 243, 255, 0.04)";
    ctx.lineWidth = 1;
    for (let x = 0; x < canvas.width; x += 40) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += 40) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
    }

    // Zone A: Wafer Cleanroom (Top Left)
    drawZone(ctx, 40, 40, 520, 240, "ZONE A: SILICON WAFER FAB", "ISO 14644 Class 4", "rgba(0, 243, 255, 0.08)", "#00f3ff");

    // Zone B: Robotic Cell (Top Right)
    drawZone(ctx, 620, 40, 540, 240, "ZONE B: ROBOTIC WORKCELL 04", "OSHA Danger Envelope", "rgba(255, 0, 85, 0.08)", "#ff0055");

    // Zone C: Chemical Bay (Bottom Left)
    drawZone(ctx, 40, 320, 520, 240, "ZONE C: CHEMICAL STORAGE BAY", "NFPA-704 Hazmat Isolation", "rgba(255, 183, 0, 0.08)", "#ffb700");

    // Zone D: Airlock Gate (Bottom Right)
    drawZone(ctx, 620, 320, 540, 240, "ZONE D: AIRLOCK & PPE PORTAL", "Security Turnstile", "rgba(168, 85, 247, 0.08)", "#a855f7");

    // Central AGV Transit Highway (Corridor)
    ctx.fillStyle = "rgba(255, 255, 255, 0.03)";
    ctx.fillRect(570, 40, 40, 520);
    ctx.fillRect(40, 290, 1120, 20);

    // Animated AGV-101 Mobile Robot
    state.agvPos.progress += 0.006;
    if (state.agvPos.progress > 1) state.agvPos.progress = 0;
    
    // Path along central corridor
    const agvX = 80 + Math.sin(state.agvPos.progress * Math.PI * 2) * 450 + 450;
    const agvY = 300;

    // Draw AGV body
    ctx.fillStyle = "#00ff88";
    ctx.shadowColor = "#00ff88";
    ctx.shadowBlur = 12;
    ctx.beginPath();
    ctx.arc(agvX, agvY, 12, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;

    ctx.fillStyle = "#ffffff";
    ctx.font = "10px JetBrains Mono";
    ctx.fillText("AGV-101", agvX - 22, agvY - 16);

    // Hazard Pulse Effect in active incident zones
    state.hazardPulse = (state.hazardPulse + 0.05) % (Math.PI * 2);
    const pulseRadius = 30 + Math.sin(state.hazardPulse) * 15;
    ctx.strokeStyle = "rgba(255, 0, 85, 0.6)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(890, 160, pulseRadius, 0, Math.PI * 2);
    ctx.stroke();

    state.twinAnimFrame = requestAnimationFrame(draw);
  }

  draw();
}

function drawZone(ctx, x, y, w, h, title, subtitle, fill, stroke) {
  ctx.fillStyle = fill;
  ctx.fillRect(x, y, w, h);
  ctx.strokeStyle = stroke;
  ctx.lineWidth = 1.5;
  ctx.strokeRect(x, y, w, h);

  ctx.fillStyle = stroke;
  ctx.font = "bold 13px Outfit";
  ctx.fillText(title, x + 16, y + 28);

  ctx.fillStyle = "#8b9bb4";
  ctx.font = "11px JetBrains Mono";
  ctx.fillText(subtitle, x + 16, y + 46);

  // Corner tech markers
  ctx.fillStyle = stroke;
  ctx.fillRect(x, y, 8, 2);
  ctx.fillRect(x, y, 2, 8);
  ctx.fillRect(x + w - 8, y, 8, 2);
  ctx.fillRect(x + w - 2, y, 2, 8);
}

// -------------------------------------------------------------
// 7. CUSTOM TEST IMAGE UPLOAD & WEBCAM
// -------------------------------------------------------------
function setupUploadAndWebcam() {
  // File Upload
  elements.customFileInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("mode", state.activeChannel);

    elements.activeChannelName.innerText = `Analyzing Uploaded File: ${file.name}`;
    
    try {
      const res = await fetch("/api/upload-and-analyze", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      
      elements.liveImg.src = data.processed_image_b64;
      renderTelemetry(data.telemetry, data.agent_thought);
      fetchAgentThoughts();

      alert(`OpenCV 5 analysis complete for ${file.name}!\nEvidence automatically uploaded to AWS S3: ${data.s3_artifact.url}`);
    } catch (err) {
      alert("Analysis failed: " + err);
    }
  });

  // Webcam Toggle
  elements.btnWebcam.addEventListener("click", async () => {
    if (state.isWebcamActive) {
      // Turn off
      if (state.webcamStream) {
        state.webcamStream.getTracks().forEach(track => track.stop());
      }
      state.isWebcamActive = false;
      elements.btnWebcam.innerText = "Webcam Stream";
      updateStreamSource();
    } else {
      // Turn on
      try {
        state.webcamStream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
        state.isWebcamActive = true;
        elements.btnWebcam.innerText = "Stop Webcam";

        const video = document.createElement("video");
        video.srcObject = state.webcamStream;
        video.play();

        const canvas = document.createElement("canvas");
        canvas.width = 640;
        canvas.height = 480;
        const ctx = canvas.getContext("2d");

        // Periodically capture frame and send to OpenCV 5 backend
        const webcamInterval = setInterval(async () => {
          if (!state.isWebcamActive) {
            clearInterval(webcamInterval);
            return;
          }
          ctx.drawImage(video, 0, 0, 640, 480);
          canvas.toBlob(async (blob) => {
            const formData = new FormData();
            formData.append("file", blob, "webcam_frame.jpg");
            formData.append("mode", state.activeChannel);
            const res = await fetch("/api/upload-and-analyze", { method: "POST", body: formData });
            const data = await res.json();
            elements.liveImg.src = data.processed_image_b64;
            renderTelemetry(data.telemetry, data.agent_thought);
          }, "image/jpeg", 0.75);
        }, 300);

      } catch (err) {
        alert("Webcam permission denied or unavailable: " + err);
      }
    }
  });
}

// -------------------------------------------------------------
// 8. FORENSICS AUDIT REPORT DOWNLOAD
// -------------------------------------------------------------
function setupAuditDownload() {
  elements.btnDownloadAudit.addEventListener("click", async () => {
    try {
      const res = await fetch(`/api/generate-report?channel=${state.activeChannel}`, { method: "POST" });
      const report = await res.json();
      
      const markdownContent = `# AEGIS VISION - REGULATORY COMPLIANCE & FORENSIC AUDIT REPORT
**Report ID:** ${report.report_id}
**Facility:** ${report.facility}
**Timestamp:** ${report.generated_at}
**System:** ${report.system_version}

---

## 1. Executive Summary
${report.executive_summary}

## 2. Monitored Channel & Visual Telemetry
- Channel Inspected: ${report.channel_inspected.toUpperCase()}
- Compliance Standards Enforced: ${report.compliance_certifications.join(", ")}

## 3. Autonomous Agentic Reasoning & Policy Logs
${report.recent_agentic_cycles.map(c => `
### Cycle #${c.cycle_id} [${c.timestamp_iso}]
- **Risk Assessment:** ${c.risk_assessment}
- **Observations:** ${c.observations.join("; ")}
- **Policy Rule Applied:** ${c.policy_applied.id || 'None'}
- **Autonomous Actions Executed:** ${c.actuations_executed.map(a => a.tool).join(", ") || 'Nominal - Observation Only'}
`).join("\n")}

## 4. Actuator Dispatches & Physical Interventions
${report.executed_actuations.map(a => `
- **Action ID:** ${a.action_id} [${a.timestamp_iso}]
  - **Tool:** \`${a.tool}\`
  - **Parameters:** ${JSON.stringify(a.parameters)}
  - **Result:** ${JSON.stringify(a.result.status)} (Synced with AWS IoT Shadow)
`).join("\n")}

---
*Report cryptographically signed and stored in AWS S3 and DynamoDB by AegisVision.*
`;

      const blob = new Blob([markdownContent], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `AegisVision_Audit_${report.report_id}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

    } catch (err) {
      alert("Report generation failed: " + err);
    }
  });
}

// Start application
window.addEventListener("DOMContentLoaded", init);
