import threading
import pytest
from src.edge.events import Event


class TestEvent:
    def test_subscribe_and_emit(self):
        event = Event()
        received = []
        event.subscribe(lambda x: received.append(x))
        event.emit("hello")
        assert received == ["hello"]

    def test_multiple_subscribers(self):
        event = Event()
        results = []
        event.subscribe(lambda x: results.append(f"a:{x}"))
        event.subscribe(lambda x: results.append(f"b:{x}"))
        event.emit("val")
        assert results == ["a:val", "b:val"]

    def test_emit_with_multiple_args(self):
        event = Event()
        received = []
        event.subscribe(lambda a, b: received.append((a, b)))
        event.emit(1, 2)
        assert received == [(1, 2)]

    def test_emit_with_kwargs(self):
        event = Event()
        received = []
        event.subscribe(lambda name=None: received.append(name))
        event.emit(name="test")
        assert received == ["test"]

    def test_unsubscribe(self):
        event = Event()
        results = []
        cb = lambda x: results.append(x)
        event.subscribe(cb)
        event.emit("first")
        event.unsubscribe(cb)
        event.emit("second")
        assert results == ["first"]

    def test_unsubscribe_nonexistent_is_noop(self):
        event = Event()
        event.unsubscribe(lambda: None)  # should not raise

    def test_subscriber_exception_does_not_propagate(self):
        event = Event()
        results = []

        def bad_subscriber(x):
            raise ValueError("boom")

        event.subscribe(bad_subscriber)
        event.subscribe(lambda x: results.append(x))
        event.emit("val")
        assert results == ["val"]

    def test_subscriber_exception_does_not_prevent_others(self):
        event = Event()
        call_order = []

        event.subscribe(lambda: call_order.append(1))
        event.subscribe(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        event.subscribe(lambda: call_order.append(3))

        # The second subscriber raises but 1 and 3 should still run
        # We need subscribers that actually raise in the body
        call_order.clear()
        event = Event()

        event.subscribe(lambda: call_order.append(1))

        def raiser():
            raise RuntimeError("fail")

        event.subscribe(raiser)
        event.subscribe(lambda: call_order.append(3))

        event.emit()
        assert call_order == [1, 3]

    def test_emit_from_another_thread(self):
        event = Event()
        received = []
        event.subscribe(lambda x: received.append(x))

        thread = threading.Thread(target=lambda: event.emit("from_thread"))
        thread.start()
        thread.join()

        assert received == ["from_thread"]

    def test_emit_no_subscribers(self):
        event = Event()
        event.emit("nobody listening")  # should not raise

    def test_subscribe_during_emit_does_not_affect_current(self):
        event = Event()
        results = []

        def first_cb():
            results.append("first")
            event.subscribe(lambda: results.append("late"))

        event.subscribe(first_cb)
        event.emit()
        # The late subscriber was added during emit but shouldn't fire
        # in the same emit call (we iterate a snapshot)
        assert results == ["first"]
