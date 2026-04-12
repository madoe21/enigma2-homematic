# -*- coding: utf-8 -*-
"""
Platform-neutral settings and device-cache persistence.

All data is stored as JSON files under /etc/enigma2/ (default paths
can be overridden in the constructor for unit tests or alternative
platforms).

No Enigma2 or Kodi imports – safe to unit-test standalone.
"""
from __future__ import absolute_import

import json
import os

SETTINGS_FILE    = "/etc/enigma2/homematicccu_settings.json"
DEVICE_CACHE_FILE = "/etc/enigma2/homematicccu_devices.json"

DEFAULT_SETTINGS = {
    "host":        "192.168.1.100",
    "username":    "Admin",
    "password":    "",
    "refresh_sec": 30,
}


class HomematicStore(object):
    """Read/write settings and device cache."""

    def __init__(
        self,
        settings_file=SETTINGS_FILE,
        device_cache_file=DEVICE_CACHE_FILE,
    ):
        self.settings_file    = settings_file
        self.device_cache_file = device_cache_file

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _read_json(path, fallback):
        try:
            with open(path, "r") as fh:
                return json.load(fh)
        except Exception:
            return fallback

    @staticmethod
    def _write_json(path, data):
        folder = os.path.dirname(path)
        if folder and not os.path.isdir(folder):
            try:
                os.makedirs(folder)
            except Exception:
                pass
        try:
            with open(path, "w") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def get_settings(self):
        """Return merged settings dict (persisted values override defaults)."""
        saved  = self._read_json(self.settings_file, {})
        merged = DEFAULT_SETTINGS.copy()
        if isinstance(saved, dict):
            merged.update(saved)
        return merged

    def save_settings(self, settings):
        """Persist *settings* dict, filling missing keys from defaults."""
        merged = DEFAULT_SETTINGS.copy()
        if isinstance(settings, dict):
            merged.update(settings)
        self._write_json(self.settings_file, merged)

    # ------------------------------------------------------------------
    # Device cache  (raw CCU3 device list for offline fallback)
    # ------------------------------------------------------------------

    def get_device_cache(self):
        """Return cached raw device list, or empty list if not available."""
        data = self._read_json(self.device_cache_file, [])
        return data if isinstance(data, list) else []

    def save_device_cache(self, devices):
        """Persist raw device list returned by CCU3."""
        self._write_json(self.device_cache_file, devices or [])
