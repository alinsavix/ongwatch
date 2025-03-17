import asyncio
import json
from collections import deque
from dataclasses import asdict, is_dataclass
from typing import Any, Deque, Dict

import paho.mqtt.client as mqtt


class MQTTPublisher:
    def __init__(self, broker: str = "localhost", port: int = 1883):
        self._broker = broker
        self._port = port
        self._queue: Deque[Any] = deque()
        self._client = mqtt.Client()
        self._running = False
        self._task = None

        # Connect to MQTT broker
        self._client.connect(broker, port)
        self._client.loop_start()

    async def _process_queue(self):
        self._running = True
        while self._running:
            try:
                if self._queue:
                    topic, payload = self._queue.popleft()
                    self._client.publish(topic, payload)
                await asyncio.sleep(0.01)  # Small delay to prevent CPU hogging
            except Exception as e:
                print(f"Error processing MQTT message: {e}")

    def start(self):
        """Start the background processing task"""
        if not self._task:
            self._task = asyncio.create_task(self._process_queue())

    def stop(self):
        """Stop the background processing task"""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        self._client.loop_stop()
        self._client.disconnect()

    def _serialize_object(self, obj: Any) -> str:
        """Convert object to JSON string"""
        if is_dataclass(obj):
            return json.dumps(asdict(obj))
        elif isinstance(obj, dict):
            return json.dumps(obj)
        else:
            return json.dumps(obj.__dict__)

    def _get_topic(self, obj: Any) -> str:
        """Generate MQTT topic based on object type"""
        return f"ongwatch/{obj.__class__.__name__.lower()}"

    def publish(self, obj: Any):
        """
        Publish an object to MQTT broker
        Args:
            obj: Any object that can be serialized to JSON
        """
        topic = self._get_topic(obj)
        payload = self._serialize_object(obj)
        self._queue.append((topic, payload))

# Global instance
_publisher = None

def init(broker: str = "localhost", port: int = 1883):
    """Initialize the global MQTT publisher"""
    global _publisher
    _publisher = MQTTPublisher(broker, port)
    _publisher.start()

def publish(obj: Any):
    """Publish an object using the global MQTT publisher"""
    if not _publisher:
        raise RuntimeError("MQTT publisher not initialized. Call init() first.")
    _publisher.publish(obj)

def stop():
    """Stop the global MQTT publisher"""
    if _publisher:
        _publisher.stop()
