from typing import Callable, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import asyncio
import uuid

@dataclass
class Event:
    event_type: str
    data: Any
    timestamp: datetime
    source_id: str
    priority: int

class EventManager:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_queue = asyncio.Queue()
        
    async def publish(self, event: Event) -> None:
        await self._event_queue.put(event)
        
    def subscribe(self, event_type: str, callback: Callable) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        
    async def process_events(self) -> None:
        while True:
            event = await self._event_queue.get()
            if event.event_type in self._subscribers:
                for callback in self._subscribers[event.event_type]:
                    await callback(event)