from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from services.verification import VerificationResult

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
        return cls(rul_critical=24.0, rul_warning=72.0, conf_high=0.7)

@dataclass
class DispatchDecision:
    machine_id:   str
    alert_level:  AlertLevel
    message:      str
    should_alert: bool  
    channels:     List[str]

def dispatch(verification: VerificationResult, config: Optional[ThresholdConfig] = None) -> DispatchDecision:
    if config is None:
        config = ThresholdConfig.get_default()

    rul = verification.mean_rul
    conf = verification.confidence
    mid = verification.machine_id
    ft = verification.failure_type
    
    is_high_conf = conf >= config.conf_high

 
    if rul < config.rul_critical:
        if is_high_conf:
            return DispatchDecision(
                machine_id=mid,
                alert_level=AlertLevel.IMMEDIATE,
                message=f"CRITICAL ALERT: Machine {mid} - {ft.upper()} detected. Estimated RUL: {rul:.1f}h. Immediate action required.",
                should_alert=True,
                channels=["sms", "push", "dashboard"]
            )
        else:
            return DispatchDecision(
                machine_id=mid,
                alert_level=AlertLevel.SENSOR_NOISE,
                message=f"INVESTIGATE: Machine {mid} reports critical RUL ({rul:.1f}h) but Confidence is LOW ({conf:.0%}). Check for sensor noise.",
                should_alert=True,
                channels=["dashboard"] 
            )


    elif rul < config.rul_warning:
        if is_high_conf:
            return DispatchDecision(
                machine_id=mid,
                alert_level=AlertLevel.SCHEDULED,
                message=f"MAINTENANCE REQUIRED: Machine {mid} - {ft}. RUL is {rul:.1f}h. Schedule inspection within {config.rul_warning}h window.",
                should_alert=True,
                channels=["email", "dashboard"]
            )
        else:
            return DispatchDecision(
                machine_id=mid,
                alert_level=AlertLevel.SENSOR_NOISE,
                message=f"CAUTION: Possible degradation on {mid}. RUL {rul:.1f}h with low confidence ({conf:.0%}). Flagged for review.",
                should_alert=False,
                channels=["dashboard"]
            )


    else:
        status_msg = "HEALTHY" if is_high_conf else "MONITORING"
        return DispatchDecision(
            machine_id=mid,
            alert_level=AlertLevel.HEALTHY if is_high_conf else AlertLevel.MONITOR,
            message=f"STATUS {status_msg}: Machine {mid} is operating normally. RUL: {rul:.1f}h.",
            should_alert=False,
            channels=[]
        )