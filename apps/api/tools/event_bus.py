import asyncio
import logging
from collections import defaultdict
from collections.abc import AsyncGenerator
from typing import Any

logger = logging.getLogger(__name__)


class EventBus:
    """Asynchronous in-memory event bus with pub/sub channel broadcasting."""

    _instance: "EventBus | None" = None

    def __init__(self) -> None:
        # Map event_name -> list of subscriber asyncio.Queue
        self._subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = EventBus()
        return cls._instance

    async def publish(self, event_name: str, payload: dict[str, Any]) -> None:
        """Publish an event payload to all active subscribers for the event topic."""
        async with self._lock:
            queues = list(self._subscribers.get(event_name, []))
            # Also send to wildcard '*' subscribers
            wildcard_queues = list(self._subscribers.get("*", []))

        all_queues = set(queues + wildcard_queues)
        logger.debug(f"[EventBus] Publishing '{event_name}' to {len(all_queues)} subscribers")

        for queue in all_queues:
            try:
                queue.put_nowait({"event": event_name, "payload": payload})
            except asyncio.QueueFull:
                logger.warning(f"[EventBus] Subscriber queue full for event '{event_name}'")

    async def subscribe(
        self, event_name: str
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Subscribe to an event topic and yield incoming messages."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers[event_name].append(queue)

        try:
            while True:
                message = await queue.get()
                yield message
        finally:
            async with self._lock:
                if queue in self._subscribers[event_name]:
                    self._subscribers[event_name].remove(queue)


# Singleton instance accessor
def get_event_bus() -> EventBus:
    return EventBus.get_instance()
