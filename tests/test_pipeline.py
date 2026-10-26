"""
AegisVision - Automated Unit & Integration Tests
Tests OpenCV 5 pipelines, COOL acceleration engine, and Agentic reasoning.
"""

import unittest
import numpy as np
import cv2
from backend.app.vision.pipeline import vision_pipeline
from backend.app.vision.cool_engine import cool_engine
from backend.app.agent.agentic_vision import agent_engine
from backend.app.agent.tools import actuator_tools
from backend.app.aws.aws_client import aws_client

class TestAegisVision(unittest.TestCase):
    def setUp(self):
        # Create synthetic test frame
        self.test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.circle(self.test_frame, (320, 240), 100, (200, 200, 200), -1)

    def test_opencv5_version(self):
        """Verifies that OpenCV 5.x is active."""
        ver = cv2.__version__
        self.assertTrue(ver.startswith("5."), f"Expected OpenCV 5, got {ver}")

    def test_wafer_inspection(self):
        """Tests semiconductor wafer inspection pipeline."""
        out, telemetry = vision_pipeline.inspect_wafer(self.test_frame)
        self.assertEqual(out.shape, self.test_frame.shape)
        self.assertIn("defect_count", telemetry)
        self.assertIn("wafer_yield_score", telemetry)
        self.assertGreater(telemetry["latency_ms"], 0)

    def test_cool_acceleration_benchmark(self):
        """Tests Cloud-Optimized OpenCV Library (COOL) benchmarking."""
        bench = cool_engine.benchmark_comparison(self.test_frame)
        self.assertIn("speedup_factor", bench)
        self.assertIn("cool_optimized", bench)
        self.assertIn("standard_opencv", bench)
        self.assertLess(bench["cool_optimized"]["latency_ms"], bench["standard_opencv"]["latency_ms"])

    def test_agentic_reason_and_act(self):
        """Tests See -> Reason -> Act autonomous agent cycle."""
        # Simulated danger telemetry
        danger_tel = {
            "channel": "ROBOTIC_CELL_CH2",
            "danger_zone_breached": True,
            "max_arm_velocity_px_s": 85.0,
            "active_intrusions": [{"id": 1, "in_danger_zone": True}]
        }
        thought = agent_engine.reason_and_act("robot", danger_tel)
        self.assertEqual(thought["risk_assessment"], "CRITICAL")
        self.assertEqual(thought["policy_applied"]["id"], "OSHA_1910_212")
        self.assertGreater(len(thought["actuations_executed"]), 0)

    def test_actuator_tool_execution(self):
        """Tests physical actuator execution and AWS IoT shadow sync."""
        res = actuator_tools.emergency_halt_conveyor("ZONE_TEST", "Unit Test Trigger")
        self.assertEqual(res["status"], "EXECUTED")
        self.assertEqual(res["rpm"], 0)

    def test_aws_cloud_simulator(self):
        """Tests AWS client operations in offline simulation fallback."""
        status = aws_client.get_status()
        self.assertIn(status["mode"], ["LIVE_AWS", "SIMULATED_AWS_CLOUD"])
        self.assertEqual(status["services"]["S3"]["status"], "ONLINE")

if __name__ == "__main__":
    unittest.main()
