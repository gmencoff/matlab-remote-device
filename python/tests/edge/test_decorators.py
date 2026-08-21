import inspect
import pytest
from src.edge.events import Event
from src.edge.decorators import remote_property, remote_method


class SimpleDevice:
    """Minimal device for testing decorators."""

    def __init__(self):
        self.property_changed = Event()
        self._gain = 0.0
        self._label = "default"

    @remote_property
    def gain(self) -> float:
        return self._gain

    @gain.setter
    def gain(self, value: float):
        self._gain = value

    @remote_property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, value: str):
        self._label = value

    @remote_property
    def read_only_value(self) -> int:
        return 42


class VisibleIfDevice:
    """Device with conditional visibility."""

    def __init__(self):
        self.property_changed = Event()
        self._mode = "idle"
        self._rx_gain = 10.0

    @remote_property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, value: str):
        self._mode = value

    @remote_property(visible_if=lambda self: self._mode == "rx")
    def rx_gain(self) -> float:
        return self._rx_gain

    @rx_gain.setter
    def rx_gain(self, value: float):
        self._rx_gain = value

    @remote_method(visible_if=lambda self: self._mode == "rx")
    def capture(self) -> list[float]:
        return [1.0, 2.0, 3.0]


class MethodDevice:
    """Device with remote methods."""

    def __init__(self):
        self.property_changed = Event()

    @remote_method
    def calibrate(self, channel: int = 0) -> bool:
        return True

    @remote_method
    def reset(self) -> None:
        pass

    @remote_method
    def compute(self, a: int, b: int, scale: float = 1.0) -> float:
        return (a + b) * scale


class TestRemoteProperty:
    def test_getter_works(self):
        d = SimpleDevice()
        assert d.gain == 0.0

    def test_setter_works(self):
        d = SimpleDevice()
        d.gain = 5.0
        assert d.gain == 5.0

    def test_setter_emits_property_changed(self):
        d = SimpleDevice()
        events = []
        d.property_changed.subscribe(lambda name: events.append(name))
        d.gain = 7.0
        assert events == ["gain"]

    def test_no_event_on_failed_setter(self):
        class FailDevice:
            def __init__(self):
                self.property_changed = Event()
                self._val = 0

            @remote_property
            def val(self) -> int:
                return self._val

            @val.setter
            def val(self, value: int):
                if value < 0:
                    raise ValueError("negative not allowed")
                self._val = value

        d = FailDevice()
        events = []
        d.property_changed.subscribe(lambda name: events.append(name))

        with pytest.raises(ValueError):
            d.val = -1

        assert events == []
        assert d.val == 0

    def test_read_only_property_raises_on_set(self):
        d = SimpleDevice()
        with pytest.raises(AttributeError, match="no setter"):
            d.read_only_value = 99

    def test_is_remote_property_marker(self):
        prop = SimpleDevice.__dict__["gain"]
        assert hasattr(prop, "_is_remote_property")
        assert prop._is_remote_property is True

    def test_ordinary_property_not_marked(self):
        class NormalDevice:
            @property
            def normal(self) -> int:
                return 1

        prop = NormalDevice.__dict__["normal"]
        assert not hasattr(prop, "_is_remote_property")

    def test_setter_preserves_visible_if(self):
        prop = VisibleIfDevice.__dict__["rx_gain"]
        assert prop.visible_if is not None

    def test_visible_if_evaluation(self):
        d = VisibleIfDevice()
        prop = type(d).__dict__["rx_gain"]
        assert prop.visible_if(d) is False
        d._mode = "rx"
        assert prop.visible_if(d) is True

    def test_class_level_access_returns_descriptor(self):
        prop = SimpleDevice.gain
        assert isinstance(prop, remote_property)


class TestRemoteMethod:
    def test_method_callable(self):
        d = MethodDevice()
        assert d.calibrate() is True

    def test_method_with_args(self):
        d = MethodDevice()
        result = d.compute(2, 3, scale=2.0)
        assert result == 10.0

    def test_method_default_args(self):
        d = MethodDevice()
        assert d.calibrate(channel=5) is True

    def test_is_remote_method_marker(self):
        m = MethodDevice.__dict__["calibrate"]
        assert hasattr(m, "_is_remote_method")
        assert m._is_remote_method is True

    def test_preserves_signature(self):
        m = MethodDevice.__dict__["calibrate"]
        sig = inspect.signature(m)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "channel" in params

    def test_visible_if_method(self):
        d = VisibleIfDevice()
        m = type(d).__dict__["capture"]
        assert m._visible_if(d) is False
        d._mode = "rx"
        assert m._visible_if(d) is True

    def test_method_invocation_through_instance(self):
        d = VisibleIfDevice()
        d._mode = "rx"
        result = d.capture()
        assert result == [1.0, 2.0, 3.0]

    def test_return_type_annotation_accessible(self):
        m = MethodDevice.__dict__["reset"]
        sig = inspect.signature(m)
        assert sig.return_annotation is None
