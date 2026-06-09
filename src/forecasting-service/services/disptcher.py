import os
import sys
import json
import time
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List

class AlertLevel(Enum):
    IMMEDIATE    = "IMMEDIATE"
    SCHEDULED    = "SCHEDULED"
    SENSOR_NOISE = "SENSOR_NOISE"
    MONITOR      = "MONITOR"
    HEALTHY      = "HEALTHY"

@dataclass
class ThresholdConfig:
    rul_critical: float
    rul_warning:  float
    conf_high:    float

    @classmethod
    def get_default(cls):
        return cls(rul_critical=45.0, rul_warning=75.0, conf_high=0.7)

@dataclass
class DispatchDecision:
    machine_id:   str
    alert_level:  AlertLevel
    mean_rul:     float       
    confidence:   float       
    failure_type: str         
    message:      str
    should_alert: bool
    channels:     List[str]

# Legacy procedural hook wrapper to satisfy original pipeline.py architecture contracts
def dispatch(verification: Any, config: Optional[ThresholdConfig] = None) -> DispatchDecision:
    if config is None:
        config = ThresholdConfig.get_default()

    if isinstance(verification, dict):
        rul  = verification.get("predicted_rul", 125.0)
        conf = verification.get("confidence", 1.0)
        mid  = verification.get("machine_id", "unknown")
        
        xai_block = verification.get("xai_root_cause_diagnosis")
        ft = xai_block.get("mapped_mechanical_subsystem", "unknown") if xai_block else "unknown"
    else:
        rul  = getattr(verification, "mean_rul", 125.0)
        conf = getattr(verification, "confidence", 1.0)
        mid  = getattr(verification, "machine_id", "unknown")
        ft   = getattr(verification, "failure_type", "unknown")

    is_high_conf = conf >= config.conf_high
    
    if rul <= config.rul_critical:
        return DispatchDecision(
            machine_id=mid, alert_level=AlertLevel.IMMEDIATE,
            mean_rul=rul, confidence=conf, failure_type=ft,
            message=f"CRITICAL ALERT: Machine {mid} - Component: {ft.upper()}. Immediate action required.",
            should_alert=True, channels=["sms", "push", "dashboard"],
        )
    elif rul <= config.rul_warning:
        return DispatchDecision(
            machine_id=mid, alert_level=AlertLevel.SCHEDULED,
            mean_rul=rul, confidence=conf, failure_type=ft,
            message=f"MAINTENANCE REQUIRED: Machine {mid}. Schedule inspection for {ft}.",
            should_alert=True, channels=["email", "dashboard"],
        )
    else:
        return DispatchDecision(
            machine_id=mid, alert_level=AlertLevel.HEALTHY,
            mean_rul=rul, confidence=conf, failure_type=ft,
            message=f"STATUS HEALTHY: Machine {mid} operating normally.",
            should_alert=False, channels=[],
        )

class AlertDispatcher:
    def __init__(self, config: Optional[ThresholdConfig] = None):
        self.config = config or ThresholdConfig.get_default()

    def evaluate_health_metrics(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        success = payload.get("success", False)
        if not success:
            return {"dispatch_status": "FAILED_PIPELINE_RECORD", "payload": payload}

        inner_payload = payload.get("payload", {})
        predicted_rul = inner_payload.get("predicted_rul", -1.0)
        machine_id = inner_payload.get("machine_id", "unknown_asset")
        
        if predicted_rul <= self.config.rul_critical:
            alert_level = "CRITICAL"
            routing_key = "telemetry.alert.critical"
        elif predicted_rul <= self.config.rul_warning:
            alert_level = "WARNING"
            routing_key = "telemetry.alert.warning"
        else:
            alert_level = "HEALTHY"
            routing_key = "telemetry.metrics.normal"

        inner_payload["alert_level"] = alert_level
        
        return {
            "dispatch_timestamp": time.time(),
            "asset_id": machine_id,
            "alert_level": alert_level,
            "routing_key": routing_key,
            "requires_immediate_action": alert_level == "CRITICAL",
            "data": inner_payload
        }

    def dispatch(self, processed_payload: Dict[str, Any]) -> bool:
        envelope = self.evaluate_health_metrics(processed_payload)
        print(f"\n>>> [DISPATCHER BROADCAST] Route: '{envelope.get('routing_key')}' | Severity: {envelope.get('alert_level')}")
        return True