# -*- coding: utf-8 -*-
"""
Enigma2-specific runtime services.

This is the ONLY module that imports from the Enigma2 framework
(besides screens.py and plugin.py).

For a Kodi port replace this file with a Kodi-specific implementation
that exposes the same public interface (RefreshTimerService).
"""
from __future__ import absolute_import

from enigma import eTimer


def _timer_connect(timer, callback):
    """Connect a timer timeout signal – handles both Enigma2 API styles."""
    try:
        timer.timeout.connect(callback)
    except Exception:
        timer.callback.append(callback)


class RefreshTimerService(object):
    """Single-shot auto-refresh timer.

    Usage::

        svc = RefreshTimerService()
        svc.start(30, my_reload_function)   # fires once after 30 s
        # …  call stop() when screen hides
        svc.stop()
    """

    def __init__(self):
        self._timer    = eTimer()
        self._callback = None
        _timer_connect(self._timer, self._on_fire)

    # ------------------------------------------------------------------

    def _on_fire(self):
        if self._callback:
            self._callback()

    def start(self, interval_sec, callback):
        """Start (or restart) the timer for *interval_sec* seconds."""
        self._callback = callback
        self._timer.start(int(interval_sec) * 1000, True)

    def stop(self):
        """Cancel any pending timer callback."""
        self._timer.stop()
        self._callback = None

    def restart(self, interval_sec, callback):
        """Convenience: stop then start."""
        self.stop()
        self.start(interval_sec, callback)
