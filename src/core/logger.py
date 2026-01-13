import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class TraceEvent:
    type: str  # "tool_call", "tool_result", "model_think", "user_input"
    name: str  # tool name or event name
    data: Any
    timestamp: float
    duration_ms: Optional[float] = None

class TraceLogger:
    def __init__(self):
        self.events: List[TraceEvent] = []

    def log(self, type: str, name: str, data: Any, duration_ms: float = 0):
        event = TraceEvent(
            type=type,
            name=name,
            data=data,
            timestamp=time.time(),
            duration_ms=duration_ms
        )
        self.events.append(event)

    def export(self) -> List[Dict]:
        return [asdict(e) for e in self.events]
