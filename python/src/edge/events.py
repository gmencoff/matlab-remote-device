import logging
import threading
from typing import Any

logger = logging.getLogger(__name__)


class Event:
    """In-process observer pattern. Subscribers execute synchronously."""

    def __init__(self):
        self._subscribers: list = []
        self._lock = threading.Lock()

    def subscribe(self, callback) -> None:
        with self._lock:
            self._subscribers.append(callback)

    def unsubscribe(self, callback) -> None:
        with self._lock:
            try:
                self._subscribers.remove(callback)
            except ValueError:
                pass

    def emit(self, *args: Any, **kwargs: Any) -> None:
        with self._lock:
            subscribers = list(self._subscribers)
        for subscriber in subscribers:
            try:
                subscriber(*args, **kwargs)
            except Exception:
                logger.exception(
                    "Subscriber %r raised during emit", subscriber
                )
