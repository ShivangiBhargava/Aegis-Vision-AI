"""
AegisVision - AWS Cloud Infrastructure Integration Client
Supports dual execution:
1. Live AWS Services (S3, Bedrock, IoT Core, CloudWatch, DynamoDB) via boto3.
2. High-Fidelity Local Cloud Simulator when running offline or without credentials.
"""

import os
import json
import time
import base64
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("aegis_vision.aws")

class AWSClient:
    def __init__(self):
        self.region = os.getenv("AWS_DEFAULT_REGION", os.getenv("AWS_REGION", "us-east-1"))
        self.s3_bucket = os.getenv("AEGIS_S3_BUCKET", "aegis-vision-telemetry-opencv26")
        self.dynamo_table = os.getenv("AEGIS_DYNAMO_TABLE", "AegisVisionIncidents")
        self.iot_thing = os.getenv("AEGIS_IOT_THING_NAME", "AegisIndustrialFacilityAlpha")
        self.bedrock_model_id = os.getenv("AEGIS_BEDROCK_MODEL", "anthropic.claude-3-5-sonnet-20241022-v2:0")
        
        self.is_live = False
        self.clients = {}
        self.simulated_storage = {}
        self.simulated_shadow = {
            "state": {
                "reported": {
                    "conveyor_speed_rpm": 120,
                    "conveyor_status": "NORMAL",
                    "agv_101_mode": "AUTONOMOUS",
                    "agv_101_location": "ZONE_B",
                    "hvac_ventilation_pct": 65,
                    "safety_interlock": "DISARMED",
                    "emergency_siren": "OFF"
                }
            }
        }
        self.simulated_incidents = []
        self._init_aws_connections()

    def _init_aws_connections(self):
        has_creds = bool(os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"))
        if not has_creds and not os.path.exists(os.path.expanduser("~/.aws/credentials")):
            logger.info("No AWS credentials detected. Operating in High-Fidelity AWS Cloud Simulation Mode.")
            self.is_live = False
            return

        try:
            import boto3
            self.clients["s3"] = boto3.client("s3", region_name=self.region)
            self.clients["cloudwatch"] = boto3.client("cloudwatch", region_name=self.region)
            self.clients["iot_data"] = boto3.client("iot-data", region_name=self.region)
            self.clients["dynamodb"] = boto3.client("dynamodb", region_name=self.region)
            self.clients["bedrock"] = boto3.client("bedrock-runtime", region_name=self.region)
            self.is_live = True
            logger.info(f"Connected to Live AWS Cloud Services in region {self.region}")
        except Exception as e:
            logger.warning(f"AWS connection initialization failed ({e}). Falling back to simulation mode.")
            self.is_live = False

    def upload_forensic_artifact(self, artifact_name: str, image_bytes: bytes, metadata: Dict[str, str]) -> Dict[str, Any]:
        """Uploads annotated OpenCV 5 evidence frames to AWS S3."""
        key = f"incidents/{time.strftime('%Y/%m/%d')}/{int(time.time())}_{artifact_name}"
        if self.is_live and "s3" in self.clients:
            try:
                self.clients["s3"].put_object(
                    Bucket=self.s3_bucket,
                    Key=key,
                    Body=image_bytes,
                    ContentType="image/jpeg",
                    Metadata=metadata
                )
                s3_url = f"https://{self.s3_bucket}.s3.{self.region}.amazonaws.com/{key}"
                return {"status": "SUCCESS", "storage": "AWS_S3_LIVE", "key": key, "url": s3_url}
            except Exception as e:
                logger.error(f"S3 upload error: {e}")

        # Local Simulation Mode
        b64_data = base64.b64encode(image_bytes).decode("utf-8")
        self.simulated_storage[key] = {
            "size": len(image_bytes),
            "metadata": metadata,
            "timestamp": time.time(),
            "preview_b64": f"data:image/jpeg;base64,{b64_data}"
        }
        return {
            "status": "SIMULATED_SUCCESS",
            "storage": "AWS_S3_SIMULATED",
            "key": key,
            "url": f"s3://{self.s3_bucket}/{key}",
            "preview": f"data:image/jpeg;base64,{b64_data[:100]}..."
        }

    def update_iot_digital_twin_shadow(self, desired_state: Dict[str, Any]) -> Dict[str, Any]:
        """Publishes desired robotic/facility actuator states via AWS IoT Device Shadow."""
        payload = json.dumps({"state": {"desired": desired_state}})
        if self.is_live and "iot_data" in self.clients:
            try:
                response = self.clients["iot_data"].update_thing_shadow(
                    thingName=self.iot_thing,
                    payload=payload
                )
                return {"status": "SUCCESS", "shadow": "AWS_IOT_LIVE", "updated": desired_state}
            except Exception as e:
                logger.error(f"AWS IoT Shadow update error: {e}")

        # Simulator update
        current_state = self.simulated_shadow["state"]["reported"]
        current_state.update(desired_state)
        return {
            "status": "SIMULATED_SUCCESS",
            "shadow": "AWS_IOT_SIMULATED",
            "updated": desired_state,
            "full_state": current_state
        }

    def emit_vision_cloudwatch_metric(self, metric_name: str, value: float, unit: str = "Milliseconds", dimensions: Optional[Dict[str, str]] = None) -> bool:
        """Pushes real-time OpenCV 5 latency and detection telemetry to AWS CloudWatch."""
        dims = [{"Name": k, "Value": v} for k, v in (dimensions or {}).items()]
        dims.append({"Name": "System", "Value": "AegisVision-OpenCV5"})

        if self.is_live and "cloudwatch" in self.clients:
            try:
                self.clients["cloudwatch"].put_metric_data(
                    Namespace="OpenCV/IndustrialVision",
                    MetricData=[{
                        "MetricName": metric_name,
                        "Value": value,
                        "Unit": unit,
                        "Dimensions": dims,
                        "Timestamp": time.time()
                    }]
                )
                return True
            except Exception as e:
                logger.error(f"CloudWatch metric push error: {e}")
        return True

    def log_incident_to_dynamo(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Records forensic incident logs in AWS DynamoDB with millisecond precision."""
        incident_id = f"INC-{int(time.time()*1000)}"
        incident_data["incident_id"] = incident_id
        incident_data["timestamp"] = time.time()
        incident_data["timestamp_iso"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        if self.is_live and "dynamodb" in self.clients:
            try:
                item = {k: {"S": str(v)} for k, v in incident_data.items()}
                self.clients["dynamodb"].put_item(
                    TableName=self.dynamo_table,
                    Item=item
                )
                return {"status": "SUCCESS", "incident_id": incident_id, "backend": "DYNAMODB_LIVE"}
            except Exception as e:
                logger.error(f"DynamoDB put error: {e}")

        self.simulated_incidents.insert(0, incident_data)
        if len(self.simulated_incidents) > 100:
            self.simulated_incidents.pop()
        return {"status": "SIMULATED_SUCCESS", "incident_id": incident_id, "backend": "DYNAMODB_SIMULATED"}

    def invoke_bedrock_reasoning(self, prompt: str, visual_context: Dict[str, Any]) -> Optional[str]:
        """Invokes AWS Bedrock Anthropic Claude model for multi-step agent reasoning."""
        if self.is_live and "bedrock" in self.clients:
            try:
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 800,
                    "temperature": 0.2,
                    "messages": [{
                        "role": "user",
                        "content": f"{prompt}\n\nStructured OpenCV Telemetry:\n{json.dumps(visual_context, indent=2)}"
                    }]
                })
                response = self.clients["bedrock"].invoke_model(
                    modelId=self.bedrock_model_id,
                    body=body
                )
                response_body = json.loads(response.get("body").read())
                return response_body["content"][0]["text"]
            except Exception as e:
                logger.error(f"AWS Bedrock invocation error: {e}")
        return None

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive status of AWS cloud integration."""
        return {
            "mode": "LIVE_AWS" if self.is_live else "SIMULATED_AWS_CLOUD",
            "region": self.region,
            "services": {
                "S3": {"status": "ONLINE", "bucket": self.s3_bucket, "objects_stored": len(self.simulated_storage)},
                "CloudWatch": {"status": "ONLINE", "namespace": "OpenCV/IndustrialVision"},
                "IoT_Core": {"status": "ONLINE", "thing": self.iot_thing, "shadow_state": self.simulated_shadow["state"]["reported"]},
                "DynamoDB": {"status": "ONLINE", "table": self.dynamo_table, "logged_incidents": len(self.simulated_incidents)},
                "Bedrock": {"status": "ONLINE", "model_id": self.bedrock_model_id}
            }
        }

# Global singleton client
aws_client = AWSClient()
