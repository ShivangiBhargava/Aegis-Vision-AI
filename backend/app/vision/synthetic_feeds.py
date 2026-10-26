"""
AegisVision - High-Fidelity Synthetic Industrial Video Feeds
Generates real-time, mathematically animated industrial vision scenarios using pure OpenCV 5 drawing,
noise generators, and procedural kinematics.
"""

import cv2
import numpy as np
import math
import time

class SyntheticFeedGenerator:
    def __init__(self):
        self.frame_counters = {"wafer": 0, "robot": 0, "chemical": 0, "ppe": 0}

    def generate_wafer_feed(self, width: int = 640, height: int = 480) -> np.ndarray:
        """Generates dynamic semiconductor cleanroom inspection feed with micro-defects."""
        f_idx = self.frame_counters["wafer"]
        self.frame_counters["wafer"] += 1
        
        # Dark cleanroom background
        frame = np.full((height, width, 3), 22, dtype=np.uint8)
        
        # Draw 300mm Silicon Wafer Disc
        center = (width // 2, height // 2)
        radius = int(min(width, height) * 0.42)
        
        # Wafer mirror silicon surface with subtle gradient
        cv2.circle(frame, center, radius, (95, 80, 75), -1)
        cv2.circle(frame, center, radius, (160, 150, 140), 2)
        
        # Wafer flat notch
        notch_angle = math.radians(270)
        nx = int(center[0] + radius * math.cos(notch_angle))
        ny = int(center[1] + radius * math.sin(notch_angle))
        cv2.circle(frame, (nx, ny), 12, (22, 22, 22), -1)

        # Silicon Die Grid
        grid_step = 28
        start_x = center[0] - radius + 15
        end_x = center[0] + radius - 15
        start_y = center[1] - radius + 15
        end_y = center[1] + radius - 15

        for gx in range(start_x, end_x, grid_step):
            for gy in range(start_y, end_y, grid_step):
                if np.hypot(gx + grid_step/2 - center[0], gy + grid_step/2 - center[1]) < radius - 15:
                    cv2.rectangle(frame, (gx, gy), (gx + grid_step - 2, gy + grid_step - 2), (120, 105, 100), 1)

        # Dynamic Defect 1: Micro-crack propagating across dies
        crack_phase = (f_idx % 120) / 120.0
        crack_len = int(crack_phase * 65)
        cx1, cy1 = center[0] - 80, center[1] - 40
        cx2, cy2 = cx1 + crack_len, cy1 + int(crack_len * 0.6)
        cv2.line(frame, (cx1, cy1), (cx2, cy2), (240, 240, 255), 2)
        cv2.line(frame, (cx1 + 20, cy1 + 12), (cx1 + 35, cy1 + 30), (220, 220, 255), 1)

        # Dynamic Defect 2: Particle Contamination void
        px = int(center[0] + 60 + 15 * math.sin(f_idx * 0.05))
        py = int(center[1] + 50)
        cv2.circle(frame, (px, py), 9, (30, 30, 35), -1)
        cv2.circle(frame, (px, py), 11, (210, 180, 140), 1)

        # Laser inspection crosshair scanner line
        scan_y = int((height * 0.15) + ((f_idx * 4) % int(height * 0.70)))
        cv2.line(frame, (center[0] - radius, scan_y), (center[0] + radius, scan_y), (255, 120, 50), 1)

        # Overlay Cleanroom Telemetry Header
        cv2.putText(frame, f"CAM-01: CLEANROOM WAFER FAB [DIE YIELD: 94.2%]", (16, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 200), 1, cv2.LINE_AA)
        return frame

    def generate_robotic_cell_feed(self, width: int = 640, height: int = 480) -> np.ndarray:
        """Generates dynamic robotic workcell with moving arm and worker intrusion."""
        f_idx = self.frame_counters["robot"]
        self.frame_counters["robot"] += 1
        
        # Industrial factory floor
        frame = np.full((height, width, 3), 40, dtype=np.uint8)
        
        # Floor grid texture
        for gy in range(0, height, 40):
            cv2.line(frame, (0, gy), (width, gy), (50, 50, 50), 1)
        for gx in range(0, width, 40):
            cv2.line(frame, (gx, 0), (gx, height), (50, 50, 50), 1)

        # Safety Zone yellow/black hazard stripes along borders
        cv2.rectangle(frame, (int(width * 0.20), int(height * 0.25)), (int(width * 0.80), int(height * 0.85)), (20, 60, 60), -1)

        # Robotic Arm Base
        base_x, base_y = int(width * 0.50), int(height * 0.65)
        cv2.circle(frame, (base_x, base_y), 35, (80, 80, 80), -1)
        cv2.circle(frame, (base_x, base_y), 20, (140, 140, 140), -1)

        # Articulated Arm Joint Kinematics
        theta1 = math.sin(f_idx * 0.04) * 0.8 - 0.2
        arm1_len = 110
        j1_x = int(base_x + arm1_len * math.sin(theta1))
        j1_y = int(base_y - arm1_len * math.cos(theta1))

        theta2 = theta1 + math.cos(f_idx * 0.05) * 1.1
        arm2_len = 95
        j2_x = int(j1_x + arm2_len * math.sin(theta2))
        j2_y = int(j1_y - arm2_len * math.cos(theta2))

        # Draw arm segments (Heavy industrial orange/yellow)
        cv2.line(frame, (base_x, base_y), (j1_x, j1_y), (0, 140, 255), 16)
        cv2.circle(frame, (j1_x, j1_y), 14, (50, 50, 50), -1)
        cv2.line(frame, (j1_x, j1_y), (j2_x, j2_y), (0, 180, 255), 10)
        cv2.circle(frame, (j2_x, j2_y), 10, (220, 220, 220), -1)

        # Welding / Tool end-effector sparks
        spark_phase = f_idx % 20
        if spark_phase < 8:
            cv2.circle(frame, (j2_x, j2_y), 8, (255, 255, 255), -1)
            for _ in range(5):
                sx = j2_x + np.random.randint(-18, 18)
                sy = j2_y + np.random.randint(-18, 18)
                cv2.line(frame, (j2_x, j2_y), (sx, sy), (0, 255, 255), 1)

        # Moving Human Worker approaching or entering danger zone
        worker_cycle = (f_idx % 240)
        # Worker walks from left margin into or near danger perimeter
        wx = int(60 + (worker_cycle * 1.8 if worker_cycle < 120 else (240 - worker_cycle) * 1.8))
        wy = int(height * 0.60)
        
        # Worker representation (Upper torso + hardhat + vest)
        cv2.rectangle(frame, (wx - 18, wy - 45), (wx + 18, wy + 20), (0, 160, 220), -1) # High-vis orange
        cv2.circle(frame, (wx, wy - 55), 12, (240, 240, 240), -1) # Hardhat white

        cv2.putText(frame, "CAM-02: ROBOTIC WORKCELL 04 [DYNAMIC KINEMATICS]", (16, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 200), 1, cv2.LINE_AA)
        return frame

    def generate_chemical_bay_feed(self, width: int = 640, height: int = 480) -> np.ndarray:
        """Generates dynamic chemical storage bay with expanding toxic leak and vapor plume."""
        f_idx = self.frame_counters["chemical"]
        self.frame_counters["chemical"] += 1
        
        frame = np.full((height, width, 3), 35, dtype=np.uint8)
        
        # Storage racks and chemical drum barrels
        barrel1_x, barrel1_y = int(width * 0.35), int(height * 0.45)
        barrel2_x, barrel2_y = int(width * 0.65), int(height * 0.45)

        # Barrel 1 (Yellow Hazmat Drum)
        cv2.rectangle(frame, (barrel1_x - 35, barrel1_y - 60), (barrel1_x + 35, barrel1_y + 40), (0, 210, 240), -1)
        cv2.ellipse(frame, (barrel1_x, barrel1_y - 60), (35, 12), 0, 0, 360, (0, 180, 210), -1)
        cv2.putText(frame, "TOXIC-8", (barrel1_x - 28, barrel1_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1)

        # Barrel 2 (Blue Solvent Drum)
        cv2.rectangle(frame, (barrel2_x - 35, barrel2_y - 60), (barrel2_x + 35, barrel2_y + 40), (180, 90, 30), -1)
        cv2.ellipse(frame, (barrel2_x, barrel2_y - 60), (35, 12), 0, 0, 360, (150, 70, 20), -1)

        # Expanding Hazardous Fluid Puddle from Drum 1
        spill_growth = min(90, int((f_idx % 200) * 0.65))
        px, py = barrel1_x + 10, barrel1_y + 55
        
        # Procedural organic fluid puddle shape
        puddle_pts = []
        for angle_deg in range(0, 360, 20):
            rad = math.radians(angle_deg)
            var_r = (spill_growth + 15) * (1.0 + 0.25 * math.sin(angle_deg * 3 + f_idx * 0.1))
            pt_x = int(px + var_r * 1.5 * math.cos(rad))
            pt_y = int(py + var_r * 0.75 * math.sin(rad))
            puddle_pts.append([pt_x, pt_y])

        pts_arr = np.array(puddle_pts, np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(frame, [pts_arr], (0, 230, 80)) # Toxic luminous green
        cv2.polylines(frame, [pts_arr], True, (0, 255, 120), 2)

        # Vapor Plume overlay
        vapor_y = py - 40 - int((f_idx % 60) * 1.2)
        cv2.ellipse(frame, (px + 10, vapor_y), (40, 20), 0, 0, 360, (50, 160, 100), -1)

        cv2.putText(frame, "CAM-03: CHEMICAL STORAGE ISOLATION BAY [HAZMAT]", (16, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 200), 1, cv2.LINE_AA)
        return frame

    def generate_ppe_gate_feed(self, width: int = 640, height: int = 480) -> np.ndarray:
        """Generates dynamic cleanroom personnel gate with compliant and non-compliant workers."""
        f_idx = self.frame_counters["ppe"]
        self.frame_counters["ppe"] += 1
        
        frame = np.full((height, width, 3), 48, dtype=np.uint8)
        
        # Turnstile security gate layout
        cv2.rectangle(frame, (int(width * 0.35), int(height * 0.40)), (int(width * 0.65), int(height * 0.95)), (75, 75, 75), -1)
        cv2.line(frame, (int(width * 0.35), int(height * 0.55)), (int(width * 0.65), int(height * 0.55)), (0, 0, 255), 4)

        # Worker 1 (Compliant - Wearing white hardhat and high-vis vest)
        w1_x = int(width * 0.22)
        w1_y = int(height * 0.55)
        # Body / Vest
        cv2.rectangle(frame, (w1_x - 22, w1_y - 50), (w1_x + 22, w1_y + 40), (20, 220, 220), -1) # Yellow high-vis
        # Head / Hardhat
        cv2.circle(frame, (w1_x, w1_y - 65), 16, (245, 245, 245), -1) # White hardhat
        cv2.putText(frame, "W-101", (w1_x - 18, w1_y + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200, 200, 200), 1)

        # Worker 2 (Non-Compliant - Missing helmet and vest)
        # Animates towards the security gate
        walk_offset = (f_idx % 180) * 0.8
        w2_x = int(width * 0.80 - walk_offset)
        w2_y = int(height * 0.55)
        # Body (Ordinary dark clothing - No high-vis vest)
        cv2.rectangle(frame, (w2_x - 22, w2_y - 50), (w2_x + 22, w2_y + 40), (120, 50, 40), -1) # Dark red shirt
        # Head (No Hardhat - Brown hair)
        cv2.circle(frame, (w2_x, w2_y - 65), 15, (40, 60, 110), -1) # Dark head/no helmet
        cv2.putText(frame, "W-102", (w2_x - 18, w2_y + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200, 200, 200), 1)

        cv2.putText(frame, "CAM-04: AIRLOCK AIR-SHOWER ACCESS GATE [ISO 5]", (16, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 200), 1, cv2.LINE_AA)
        return frame

    def get_feed(self, feed_name: str, width: int = 640, height: int = 480) -> np.ndarray:
        if feed_name == "wafer":
            return self.generate_wafer_feed(width, height)
        elif feed_name == "robot":
            return self.generate_robotic_cell_feed(width, height)
        elif feed_name == "chemical":
            return self.generate_chemical_bay_feed(width, height)
        elif feed_name == "ppe":
            return self.generate_ppe_gate_feed(width, height)
        else:
            return self.generate_wafer_feed(width, height)

# Global synthetic generator
synthetic_generator = SyntheticFeedGenerator()
