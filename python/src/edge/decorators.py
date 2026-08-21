import functools
import inspect
from typing import Any, Callable


class remote_property(property):
    """Property descriptor that exposes a device attribute for remote access.

    Inherits from built-in property for standard getter/setter/deleter
    behavior and adds remote metadata and automatic event emission.

    Usage:
        @remote_property
        def gain(self) -> float:
            return self._gain

        @gain.setter
        def gain(self, value: float):
            self._gain = value

        @remote_property(visible_if=lambda self: self.mode == "rx")
        def rx_gain(self) -> float:
            return self._rx_gain
    """

    _is_remote_property = True

    def __init__(self, fget=None, fset=None, fdel=None, doc=None, *, visible_if=None):
        super().__init__(fget, fset, fdel, doc)
        self._visible_if = visible_if
        self._name: str | None = None

    def __call__(self, fget):
        """Handle @remote_property(visible_if=...) as two-step decorator."""
        if self.fget is None and callable(fget):
            return type(self)(fget, visible_if=self._visible_if)
        raise TypeError("remote_property requires a getter function")

    def __set_name__(self, owner, name: str):
        self._name = name

    def __set__(self, obj, value):
        super().__set__(obj, value)
        obj.property_changed.emit(self._name)

    def setter(self, fset):
        new_prop = type(self)(self.fget, fset, self.fdel, self.__doc__,
                             visible_if=self._visible_if)
        new_prop._name = self._name
        return new_prop

    @property
    def visible_if(self) -> Callable | None:
        return self._visible_if


def remote_method(func=None, *, visible_if: Callable | None = None):
    """Decorator that marks a method for remote invocation.

    Usage:
        @remote_method
        def calibrate(self, channel: int = 0) -> bool:
            ...

        @remote_method(visible_if=lambda self: self.mode == "rx")
        def capture(self) -> list[float]:
            ...
    """
    def decorator(fn):
        fn._is_remote_method = True
        fn._visible_if = visible_if
        return fn

    if func is not None:
        return decorator(func)
    return decorator
