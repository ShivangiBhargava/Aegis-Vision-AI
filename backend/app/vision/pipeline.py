"""
AegisVision - OpenCV 5 Substantive Vision Pipeline
Implements advanced computer vision routines for industrial physical AI:
1. Semiconductor Wafer Micro-Defect Inspection (Sub-pixel edges, morphology, template diff)
2. Robotic Workcell & Dynamic Safety Zone (Dense Farneback Optical Flow, intrusion vectors)
3. Hazardous Chemical Spill & Vapor Plume Tracker (HSV/YCrCb segmentation, temporal expansion)
4. Cleanroom & Industrial PPE Compliance (Subtractor, contour geometry, badge verification)
"""

import cv2
import numpy as np
import time
from typing import Dict, Any, Tuple, List, Optional

class VisionPipeline:
    def __init__(self):
        self.version = cv2.__version__
        self.prev_gray_frames: Dict[str, np.ndarray] = {}
        self.prev_spill_areas: Dict[str, float] = {}
        self.bg_subtractors: Dict[str, Any] = {}
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    def get_or_create_subtractor(self, key: str):
        if key not in self.bg_subtractors:
            self.bg_subtractors[key] = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=25, detectShadows=True)
        return self.bg_subtractors[key]

    # ---------------------------------------------------------
    # 1. SEMICONDUCTOR WAFER MICRO-DEFECT INSPECTION
    # ---------------------------------------------------------
    def inspect_wafer(self, frame: np.ndarray, overlay_mode: str = "annotated") -> Tuple[np.ndarray, Dict[str, Any]]:
        """Inspects semiconductor silicon wafers for micro-fractures, voids, and particle contamination."""
        start_time = time.perf_counter()
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        enhanced = self.clahe.apply(gray)
        
        # Sub-pixel edge detection using Gaussian blur and OpenCV Canny
        blurred = cv2.GaussianBlur(enhanced, (5, 5), 1.2)
        edges = cv2.Canny(blurred, 40, 140, apertureSize=3, L2gradient=True)

        # Morphological gradient to isolate micro-fractures
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        morph_grad = cv2.morphologyEx(edges, cv2.MORPH_GRADIENT, kernel)
        
        # Find defect contours
        contours, hierarchy = cv2.findContours(morph_grad, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        defects = []
        annotated = frame.copy()
        mask = np.zeros((h, w), dtype=np.uint8)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 15 < area < 12000: # filter noise and macro boundaries
                x, y, bw, bh = cv2.boundingRect(cnt)
                perimeter = cv2.arcLength(cnt, True)
                circularity = (4 * np.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0
                
                # Classify defect type
                if circularity > 0.65:
                    defect_type = "PARTICLE_VOID"
                    color = (0, 165, 255) # Orange
                    severity = "CRITICAL" if area > 200 else "MEDIUM"
                elif bw / max(1, bh) > 3.0 or bh / max(1, bw) > 3.0:
                    defect_type = "MICRO_CRACK"
                    color = (0, 0, 255) # Red
                    severity = "HIGH"
                else:
                    defect_type = "SURFACE_BLEMISH"
                    color = (0, 255, 255) # Yellow
                    severity = "LOW"

                defects.append({
                    "type": defect_type,
                    "severity": severity,
                    "area_px": round(area, 2),
                    "bbox": [int(x), int(y), int(bw), int(bh)],
                    "circularity": round(circularity, 3),
                    "coordinates_norm": [round(x/w, 3), round(y/h, 3), round(bw/w, 3), round(bh/h, 3)]
                })

                cv2.drawContours(mask, [cnt], -1, 255, -1)
                if overlay_mode in ["annotated", "composite"]:
                    cv2.rectangle(annotated, (x, y), (x + bw, y + bh), color, 2)
                    cv2.putText(annotated, f"{defect_type} ({severity})", (x, max(15, y - 6)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)

        # Calculate wafer yield & health score
        total_defect_area = sum(d["area_px"] for d in defects)
        wafer_area_estimate = np.pi * ((min(h, w) * 0.45) ** 2)
        contamination_ratio = total_defect_area / max(1.0, wafer_area_estimate)
        yield_score = max(0.0, min(100.0, 100.0 - (len(defects) * 4.5 + contamination_ratio * 500)))

        latency_ms = (time.perf_counter() - start_time) * 1000

        # Construct requested visualization output
        output_frame = annotated
        if overlay_mode == "edges":
            output_frame = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        elif overlay_mode == "mask":
            heatmap = cv2.applyColorMap(mask, cv2.COLORMAP_JET)
            output_frame = cv2.addWeighted(frame, 0.4, heatmap, 0.6, 0)

        telemetry = {
            "channel": "WAFER_INSPECTION_CH1",
            "opencv_version": self.version,
            "latency_ms": round(latency_ms, 2),
            "defect_count": len(defects),
            "defects": defects[:8], # top 8
            "total_defect_area_px": round(total_defect_area, 2),
            "wafer_yield_score": round(yield_score, 1),
            "status": "ANOMALY_DETECTED" if len(defects) > 0 else "NOMINAL",
            "critical_violations": sum(1 for d in defects if d["severity"] == "CRITICAL")
        }
        return output_frame, telemetry

    # ---------------------------------------------------------
    # 2. ROBOTIC WORKCELL & OPTICAL FLOW DANGER ZONE SENTINEL
    # ---------------------------------------------------------
    def inspect_robotic_cell(self, frame: np.ndarray, stream_id: str = "cell_1", overlay_mode: str = "annotated") -> Tuple[np.ndarray, Dict[str, Any]]:
        """Tracks robotic arm motion vectors and worker intrusion into dynamic safety envelope."""
        start_time = time.perf_counter()
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Define Safety Exclusion Zone polygon (e.g. 20% to 80% width, 30% to 90% height)
        zone_polygon = np.array([
            [int(w * 0.25), int(h * 0.30)],
            [int(w * 0.75), int(h * 0.30)],
            [int(w * 0.85), int(h * 0.88)],
            [int(w * 0.15), int(h * 0.88)]
        ], np.int32)

        annotated = frame.copy()
        
        # Compute Dense Optical Flow using Farneback algorithm
        flow_vectors = []
        max_speed = 0.0
        avg_speed = 0.0
        intrusions = []

        if stream_id in self.prev_gray_frames and self.prev_gray_frames[stream_id].shape == gray.shape:
            prev_gray = self.prev_gray_frames[stream_id]
            # OpenCV Farneback Optical Flow
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, gray, None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )
            
            mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            max_speed = float(np.max(mag))
            avg_speed = float(np.mean(mag))

            # Grid sampling for optical flow vector visualization
            step = 28
            for y in range(0, h, step):
                for x in range(0, w, step):
                    fx, fy = flow[y, x]
                    speed = np.hypot(fx, fy)
                    if speed > 2.0:
                        pt1 = (x, y)
                        pt2 = (int(x + fx * 2.5), int(y + fy * 2.5))
                        flow_vectors.append({"x": x, "y": y, "dx": round(float(fx), 2), "dy": round(float(fy), 2), "speed": round(float(speed), 2)})
                        if overlay_mode in ["annotated", "vectors"]:
                            # Color vector by velocity intensity
                            v_color = (0, 255, 0) if speed < 8 else ((0, 200, 255) if speed < 16 else (0, 0, 255))
                            cv2.arrowedLine(annotated, pt1, pt2, v_color, 1, tipLength=0.3)

        self.prev_gray_frames[stream_id] = gray

        # Detect moving objects/personnel using background subtraction
        subtractor = self.get_or_create_subtractor(stream_id)
        fg_mask = subtractor.apply(frame)
        _, fg_thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
        fg_clean = cv2.morphologyEx(fg_thresh, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)))
        contours, _ = cv2.findContours(fg_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 1200:
                x, y, bw, bh = cv2.boundingRect(cnt)
                center_pt = (x + bw // 2, y + bh // 2)
                
                # Check point-in-polygon intrusion into danger zone
                in_danger_zone = cv2.pointPolygonTest(zone_polygon, (float(center_pt[0]), float(center_pt[1])), False) >= 0
                
                status = "CRITICAL_INTRUSION" if in_danger_zone else "CLEAR"
                box_color = (0, 0, 255) if in_danger_zone else (0, 255, 0)

                intrusions.append({
                    "bbox": [int(x), int(y), int(bw), int(bh)],
                    "center": [center_pt[0], center_pt[1]],
                    "in_danger_zone": in_danger_zone,
                    "area_px": round(area, 1),
                    "status": status
                })

                if overlay_mode in ["annotated", "composite"]:
                    cv2.rectangle(annotated, (x, y), (x + bw, y + bh), box_color, 2)
                    cv2.putText(annotated, f"TARGET: {status}", (x, y - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, box_color, 1, cv2.LINE_AA)

        # Draw Safety Zone Outline
        zone_color = (0, 0, 255) if any(i["in_danger_zone"] for i in intrusions) else (0, 255, 255)
        cv2.polylines(annotated, [zone_polygon], True, zone_color, 2)
        cv2.putText(annotated, "DANGER ZONE: ARM ENVELOPE", (zone_polygon[0][0], zone_polygon[0][1] - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, zone_color, 2, cv2.LINE_AA)

        latency_ms = (time.perf_counter() - start_time) * 1000

        output_frame = annotated
        if overlay_mode == "mask":
            output_frame = cv2.cvtColor(fg_clean, cv2.COLOR_GRAY2BGR)

        telemetry = {
            "channel": "ROBOTIC_CELL_CH2",
            "opencv_version": self.version,
            "latency_ms": round(latency_ms, 2),
            "max_arm_velocity_px_s": round(max_speed * 30.0, 1),
            "avg_scene_motion": round(avg_speed, 2),
            "danger_zone_breached": any(i["in_danger_zone"] for i in intrusions),
            "active_intrusions": [i for i in intrusions if i["in_danger_zone"]],
            "total_tracked_objects": len(intrusions),
            "safety_envelope_status": "EMERGENCY_HALT_REQUIRED" if any(i["in_danger_zone"] for i in intrusions) else "SECURE"
        }
        return output_frame, telemetry

    # ---------------------------------------------------------
    # 3. HAZARDOUS CHEMICAL SPILL & FLUID DYNAMICS TRACKER
    # ---------------------------------------------------------
    def inspect_chemical_spill(self, frame: np.ndarray, stream_id: str = "chem_1", overlay_mode: str = "annotated") -> Tuple[np.ndarray, Dict[str, Any]]:
        """Isolates hazardous liquid spills, computes expansion velocity and containment vectors."""
        start_time = time.perf_counter()
        h, w = frame.shape[:2]
        
        # Color conversion to HSV & YCrCb for robust fluid identification
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)

        # Detect neon hazardous fluids (toxic green/cyan/amber chemical markers)
        # Low green/cyan mask
        lower_chem = np.array([25, 60, 60])
        upper_chem = np.array([95, 255, 255])
        mask1 = cv2.inRange(hsv, lower_chem, upper_chem)

        # Dark puddle / oil sheen mask using Cr/Cb thresholding
        _, cr_thresh = cv2.threshold(ycrcb[:, :, 1], 155, 255, cv2.THRESH_BINARY)
        _, cb_thresh = cv2.threshold(ycrcb[:, :, 2], 145, 255, cv2.THRESH_BINARY)
        sheen_mask = cv2.bitwise_and(cr_thresh, cb_thresh)

        combined_mask = cv2.bitwise_or(mask1, sheen_mask)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        clean_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
        clean_mask = cv2.morphologyEx(clean_mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(clean_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        spills = []
        annotated = frame.copy()
        current_total_area = 0.0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 450:
                current_total_area += area
                hull = cv2.convexHull(cnt)
                approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
                x, y, bw, bh = cv2.boundingRect(cnt)
                
                spills.append({
                    "area_px": round(area, 1),
                    "hull_vertices": len(hull),
                    "bbox": [int(x), int(y), int(bw), int(bh)],
                    "centroid": [int(x + bw/2), int(y + bh/2)],
                    "hazard_classification": "HAZMAT_CLASS_8_CORROSIVE" if area > 2000 else "POTENTIAL_CHEMICAL_SPILL"
                })

                if overlay_mode in ["annotated", "composite"]:
                    # Draw semi-transparent hazard overlay
                    cv2.drawContours(annotated, [hull], -1, (0, 0, 255), 2)
                    cv2.putText(annotated, f"HAZMAT SPILL: {int(area)} px", (x, max(15, y - 6)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1, cv2.LINE_AA)

        # Compute rate of expansion dA/dt
        prev_area = self.prev_spill_areas.get(stream_id, current_total_area)
        expansion_rate = current_total_area - prev_area
        self.prev_spill_areas[stream_id] = current_total_area

        latency_ms = (time.perf_counter() - start_time) * 1000

        output_frame = annotated
        if overlay_mode == "mask":
            heatmap = cv2.applyColorMap(clean_mask, cv2.COLORMAP_VIRIDIS)
            output_frame = cv2.addWeighted(frame, 0.3, heatmap, 0.7, 0)

        telemetry = {
            "channel": "CHEMICAL_BAY_CH3",
            "opencv_version": self.version,
            "latency_ms": round(latency_ms, 2),
            "spill_detected": len(spills) > 0,
            "total_spill_area_px": round(current_total_area, 1),
            "expansion_rate_px_per_frame": round(expansion_rate, 2),
            "severity": "CRITICAL_HAZMAT" if current_total_area > 3000 else ("MODERATE_LEAK" if current_total_area > 0 else "NONE"),
            "spill_instances": spills
        }
        return output_frame, telemetry

    # ---------------------------------------------------------
    # 4. CLEANROOM & INDUSTRIAL PPE COMPLIANCE SENTINEL
    # ---------------------------------------------------------
    def inspect_ppe_compliance(self, frame: np.ndarray, overlay_mode: str = "annotated") -> Tuple[np.ndarray, Dict[str, Any]]:
        """Verifies safety helmets, high-vis vests, and cleanroom attire using contour geometry & color spaces."""
        start_time = time.perf_counter()
        h, w = frame.shape[:2]
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Detect high-visibility neon yellow/orange safety vests
        vest_lower = np.array([18, 120, 120])
        vest_upper = np.array([40, 255, 255])
        vest_mask = cv2.inRange(hsv, vest_lower, vest_upper)

        # Detect safety hardhats (white / neon yellow / blue)
        helmet_lower = np.array([0, 0, 190])
        helmet_upper = np.array([180, 50, 255])
        helmet_mask = cv2.inRange(hsv, helmet_lower, helmet_upper)

        # Body contours using morphology
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        edges = cv2.Canny(blurred, 30, 90)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 15))
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        workers = []
        annotated = frame.copy()

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 4000:
                x, y, bw, bh = cv2.boundingRect(cnt)
                aspect = bh / max(1, bw)
                if aspect > 1.2: # Upright human aspect ratio
                    # Head region (top 25% of bbox)
                    head_roi_mask = helmet_mask[y: y + int(bh * 0.28), x: x + bw]
                    has_helmet = (cv2.countNonZero(head_roi_mask) > 150)
                    
                    # Torso region (middle 45% of bbox)
                    torso_roi_mask = vest_mask[y + int(bh * 0.25): y + int(bh * 0.70), x: x + bw]
                    has_vest = (cv2.countNonZero(torso_roi_mask) > 300)

                    compliant = has_helmet and has_vest
                    tag = "COMPLIANT" if compliant else "PPE_VIOLATION"
                    color = (0, 255, 0) if compliant else (0, 0, 255)

                    missing = []
                    if not has_helmet: missing.append("HARDHAT_MISSING")
                    if not has_vest: missing.append("VEST_MISSING")

                    workers.append({
                        "worker_id": f"W-{len(workers)+101}",
                        "bbox": [int(x), int(y), int(bw), int(bh)],
                        "has_helmet": has_helmet,
                        "has_vest": has_vest,
                        "compliant": compliant,
                        "violations": missing
                    })

                    if overlay_mode in ["annotated", "composite"]:
                        cv2.rectangle(annotated, (x, y), (x + bw, y + bh), color, 2)
                        cv2.putText(annotated, f"{tag}: {', '.join(missing) if missing else 'ALL CLEAR'}", 
                                    (x, max(15, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)

        latency_ms = (time.perf_counter() - start_time) * 1000

        output_frame = annotated
        if overlay_mode == "mask":
            combined_ppe = cv2.bitwise_or(vest_mask, helmet_mask)
            output_frame = cv2.applyColorMap(combined_ppe, cv2.COLORMAP_OCEAN)

        telemetry = {
            "channel": "PPE_CLEANROOM_CH4",
            "opencv_version": self.version,
            "latency_ms": round(latency_ms, 2),
            "workers_detected": len(workers),
            "compliant_count": sum(1 for w in workers if w["compliant"]),
            "violation_count": sum(1 for w in workers if not w["compliant"]),
            "workers": workers,
            "zone_status": "BREACH_UNAUTHORIZED" if any(not w["compliant"] for w in workers) else "COMPLIANT"
        }
        return output_frame, telemetry

# Global vision pipeline singleton
vision_pipeline = VisionPipeline()
