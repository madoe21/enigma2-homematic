# -*- coding: utf-8 -*-
"""
All Enigma2 screens for the HomematicCCU plugin.

Screen hierarchy
----------------
HomematicMainScreen
├── DeviceListScreen
│   └── DeviceDetailScreen
│       └── SetValueScreen          (change a device datapoint)
├── SysVarListScreen
│   └── SetValueScreen              (change a system variable)
├── SettingsScreen
└── InfoScreen

Portability note
----------------
Only this file and plugin.py / services.py import Enigma2 symbols.
All business logic lives in core.py and is Enigma2-free.
"""
from __future__ import absolute_import

import os

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import SCOPE_PLUGINS, resolveFilename

from . import _
from .core import (
    coerce_value,
    extract_device_summary,
    format_sysvar,
    format_value,
    step_for_type,
)
from .services import RefreshTimerService

BUYMEACOFFEE_URL = "https://buymeacoffee.com/madoe21"
_SUPPORT_TEXT    = "Support this plugin: " + BUYMEACOFFEE_URL


# ===========================================================================
# BaseListScreen  –  shared layout with colour-button bar
# ===========================================================================

class BaseListScreen(Screen):
    skin = """
        <screen name="BaseListScreen" position="center,120" size="1000,560"
                title="Homematic CCU3">
            <widget source="title" render="Label"
                    position="20,10" size="960,35" font="Regular;30" />
            <widget name="list" position="20,55" size="960,420"
                    scrollbarMode="showOnDemand" />
            <widget name="hint" position="20,480" size="960,28"
                    font="Regular;20" />
            <widget source="support" render="Label"
                    position="20,506" size="960,24" font="Regular;18"
                    foregroundColor="#666666" />
            <ePixmap pixmap="skin_default/buttons/red.png"
                     position="20,530"  size="220,30" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/green.png"
                     position="250,530" size="220,30" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/yellow.png"
                     position="480,530" size="220,30" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/blue.png"
                     position="710,530" size="270,30" alphatest="on" />
            <widget source="key_red" render="Label"
                    position="20,530"  size="220,30" font="Regular;22"
                    halign="center" valign="center" transparent="1" />
            <widget source="key_green" render="Label"
                    position="250,530" size="220,30" font="Regular;22"
                    halign="center" valign="center" transparent="1" />
            <widget source="key_yellow" render="Label"
                    position="480,530" size="220,30" font="Regular;22"
                    halign="center" valign="center" transparent="1" />
            <widget source="key_blue" render="Label"
                    position="710,530" size="270,30" font="Regular;22"
                    halign="center" valign="center" transparent="1" />
        </screen>"""

    def __init__(self, session, title, hint=""):
        Screen.__init__(self, session)
        self["title"]   = StaticText(title)
        self["list"]    = MenuList([])
        self["hint"]    = Label(hint)
        self["support"] = StaticText(_SUPPORT_TEXT)
        self["key_red"]    = StaticText(_("Close"))
        self["key_green"]  = StaticText("")
        self["key_yellow"] = StaticText("")
        self["key_blue"]   = StaticText("")
        self._rows = []

        self["actions"] = ActionMap(
            ["ColorActions", "OkCancelActions", "DirectionActions"],
            {
                "ok":     self.key_ok,
                "cancel": self.close,
                "red":    self.key_red_cb,
                "green":  self.key_green_cb,
                "yellow": self.key_yellow_cb,
                "blue":   self.key_blue_cb,
                "left":   self.key_left,
                "right":  self.key_right,
            },
            -1,
        )

    # ------------------------------------------------------------------

    def set_rows(self, rows):
        """Feed (label, data) pairs into the list widget."""
        self._rows = rows or []
        labels = [row[0] for row in self._rows] or [_("No items available")]
        self["list"].setList(labels)

    def current_data(self):
        idx = self["list"].getSelectionIndex()
        if idx is None or idx < 0 or idx >= len(self._rows):
            return None
        return self._rows[idx][1]

    # ------------------------------------------------------------------
    # Stubs – override in subclasses

    def key_ok(self):     pass
    def key_red_cb(self): self.close()
    def key_green_cb(self):  pass
    def key_yellow_cb(self): pass
    def key_blue_cb(self):   pass
    def key_left(self):      pass
    def key_right(self):     pass


# ===========================================================================
# HomematicMainScreen  –  top-level menu
# ===========================================================================

class HomematicMainScreen(BaseListScreen):

    def __init__(self, session, app):
        BaseListScreen.__init__(
            self, session,
            _("Homematic CCU3"),
            _("OK = open"),
        )
        self.app = app
        self["key_red"]    = StaticText(_("Close"))
        self["key_green"]  = StaticText(_("Refresh"))
        self["key_yellow"] = StaticText(_("Settings"))
        self["key_blue"]   = StaticText(_("Information"))
        self.set_rows([
            (_("Devices"),          "devices"),
            (_("System Variables"), "sysvars"),
        ])

    def key_ok(self):
        action = self.current_data()
        if action == "devices":
            self.session.open(DeviceListScreen, self.app)
        elif action == "sysvars":
            self.session.open(SysVarListScreen, self.app)

    def _settings_closed(self, _saved):
        pass  # settings already applied inside SettingsScreen

    def key_red_cb(self):    self.close()
    def key_green_cb(self):  self.session.open(DeviceListScreen, self.app)
    def key_yellow_cb(self): self.session.openWithCallback(self._settings_closed, SettingsScreen, self.app)
    def key_blue_cb(self):   self.session.open(InfoScreen)


# ===========================================================================
# DeviceListScreen  –  all CCU3 devices
# ===========================================================================

class DeviceListScreen(BaseListScreen):

    def __init__(self, session, app):
        BaseListScreen.__init__(
            self, session,
            _("Devices"),
            _("OK = details  |  GREEN = refresh"),
        )
        self.app = app
        self._device_summaries = []
        self["key_red"]   = StaticText(_("Close"))
        self["key_green"] = StaticText(_("Refresh"))

        self._refresh_svc = RefreshTimerService()
        self.onShow.append(self._load)
        self.onHide.append(self._refresh_svc.stop)

    # ------------------------------------------------------------------

    def _load(self):
        self["hint"].setText(_("Loading..."))
        self.set_rows([(_("Loading..."), None)])
        self._refresh_svc.stop()

        settings = self.app.store.get_settings()
        self.app.api.host     = settings.get("host", "")
        self.app.api.username = settings.get("username", "")
        self.app.api.password = settings.get("password", "")

        try:
            raw_devices = self.app.api.with_session(lambda api: api.get_devices())
            self._device_summaries = [extract_device_summary(d) for d in raw_devices]
            self.app.store.save_device_cache(raw_devices)
            self._render()
            refresh_sec = settings.get("refresh_sec", 30)
            self["hint"].setText(
                _("%d devices loaded  •  refresh every %ds") % (
                    len(self._device_summaries), refresh_sec
                )
            )
            self._refresh_svc.start(refresh_sec, self._load)

        except Exception as exc:
            cached = self.app.store.get_device_cache()
            if cached:
                self._device_summaries = [extract_device_summary(d) for d in cached]
                self._render()
                self["hint"].setText(_("Using cached data. Error: %s") % str(exc))
            else:
                self.set_rows([(u"⚠ " + str(exc), None)])
                self["hint"].setText(_("Error – check settings (BLUE)"))

    def _render(self):
        rows = []
        for dev in self._device_summaries:
            # Grab the first available datapoint value as inline status
            short = u""
            for ch in dev["channels"]:
                for dp in ch["datapoints"]:
                    short = u" → %s" % dp["value"]
                    break
                if short:
                    break
            label = u"%s  %s%s" % (dev["icon"], dev["name"], short)
            rows.append((label, dev))
        self.set_rows(rows)

    # ------------------------------------------------------------------

    def key_ok(self):
        dev = self.current_data()
        if dev:
            self.session.openWithCallback(
                self._on_detail_closed,
                DeviceDetailScreen,
                self.app,
                dev,
            )

    def _on_detail_closed(self, _changed):
        # After returning from detail/set-value we reload to show fresh data
        self._load()

    def key_green_cb(self):
        self._load()


# ===========================================================================
# DeviceDetailScreen  –  channels and datapoints of one device
# ===========================================================================

class DeviceDetailScreen(BaseListScreen):
    """
    Lists all channels and datapoints.
    Writable datapoints are marked with ✎.
    Pressing OK or GREEN on a writable datapoint opens SetValueScreen.
    """

    def __init__(self, session, app, device):
        BaseListScreen.__init__(
            self, session,
            u"%s  %s" % (device["icon"], device["name"]),
            _("OK = set value  |  only ✎ entries are writable"),
        )
        self.app    = app
        self.device = device
        self["key_red"]   = StaticText(_("Close"))
        self["key_green"] = StaticText(_("Set Value"))
        self._build_rows()

    # ------------------------------------------------------------------

    def _build_rows(self):
        rows = []
        for ch in self.device["channels"]:
            ch_label = (u"— %s —" % ch["name"]) if ch["name"] else u"——————"
            rows.append((ch_label, None))           # channel header – not selectable
            for dp in ch["datapoints"]:
                marker = u" ✎" if dp["writable"] else u""
                label  = u"  %-30s  %s%s" % (dp["name"], dp["value"], marker)
                rows.append((label, dp))
        self.set_rows(rows)

    # ------------------------------------------------------------------

    def key_ok(self):
        dp = self.current_data()
        if dp and dp.get("writable"):
            self._open_set_value(dp)

    def key_green_cb(self):
        self.key_ok()

    def _open_set_value(self, dp):
        def save_fn(new_value):
            settings = self.app.store.get_settings()
            self.app.api.host     = settings.get("host", "")
            self.app.api.username = settings.get("username", "")
            self.app.api.password = settings.get("password", "")
            self.app.api.with_session(
                lambda api: api.set_value(
                    dp["interface"], dp["address"],
                    dp["name"], dp["type"], new_value,
                )
            )

        self.session.openWithCallback(
            lambda changed: self.close(changed),
            SetValueScreen,

            dp.get("min"),
            dp.get("max"),
            dp.get("value_list") or [],
            save_fn,
        )


# ===========================================================================
# SetValueScreen  –  universal value editor
# ===========================================================================

class SetValueScreen(Screen):
    """
    Generic value-editing screen.

    Supports:
    - BOOL / ACTION : YELLOW toggles between True/False
    - FLOAT         : LEFT/RIGHT steps by 0.5 (clamped to min/max)
    - INTEGER       : LEFT/RIGHT steps by 1   (clamped to min/max)
    - ENUM          : LEFT/RIGHT cycles through value_list

    *save_fn* is a callable that receives the coerced new value.
    It should raise on error; the screen will catch it and show a dialog.
    """

    skin = """
        <screen name="SetValueScreen" position="center,185" size="800,390"
                title="Wert setzen">
            <widget source="title"    render="Label"
                    position="20,10"  size="760,35" font="Regular;26" />
            <widget name="dp_name"    position="20,55"  size="760,30"
                    font="Regular;22" foregroundColor="#aaaaaa" />
            <widget name="dp_value"   position="20,100" size="760,70"
                    font="Regular;54" halign="center" foregroundColor="#00c800" />
            <widget name="dp_range"   position="20,180" size="760,28"
                    font="Regular;20" halign="center" foregroundColor="#888888" />
            <widget name="hint"       position="20,218" size="760,28"
                    font="Regular;20" halign="center" />
            <ePixmap pixmap="skin_default/buttons/red.png"
                     position="20,330"  size="220,30" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/green.png"
                     position="250,330" size="220,30" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/yellow.png"
                     position="480,330" size="220,30" alphatest="on" />
            <widget source="key_red" render="Label"
                    position="20,330"  size="220,30" font="Regular;22"
                    halign="center" valign="center" transparent="1" />
            <widget source="key_green" render="Label"
                    position="250,330" size="220,30" font="Regular;22"
                    halign="center" valign="center" transparent="1" />
            <widget source="key_yellow" render="Label"
                    position="480,330" size="220,30" font="Regular;22"
                    halign="center" valign="center" transparent="1" />
        </screen>"""

    def __init__(self, session,
                 name, dp_type, raw_value, min_val, max_val, value_list,
                 save_fn):
        Screen.__init__(self, session)

        self._name        = name
        self._type        = dp_type
        self._value       = raw_value
        self._min         = min_val
        self._max         = max_val
        self._value_list  = value_list or []
        self._save_fn     = save_fn
        self._step        = step_for_type(dp_type)

        self["title"]    = StaticText(_("Set Value"))
        self["dp_name"]  = Label(name)
        self["dp_value"] = Label(self._display())
        self["dp_range"] = Label(self._range_text())
        self["hint"]     = Label(self._hint_text())
        self["key_red"]    = StaticText(_("Cancel"))
        self["key_green"]  = StaticText(_("Save"))
        if dp_type in ("BOOL", "ACTION"):
            self["key_yellow"] = StaticText(_("Toggle"))
        else:
            self["key_yellow"] = StaticText("")

        self["actions"] = ActionMap(
            ["ColorActions", "OkCancelActions", "DirectionActions"],
            {
                "cancel": lambda: self.close(False),
                "red":    lambda: self.close(False),
                "green":  self._save,
                "yellow": self._toggle,
                "ok":     self._save,
                "left":   lambda: self._adjust(-1),
                "right":  lambda: self._adjust(1),
            },
            -1,
        )

    # ------------------------------------------------------------------

    def _display(self):
        return format_value(self._type, self._value)

    def _range_text(self):
        if self._type in ("BOOL", "ACTION"):
            return _("AN / AUS")
        if self._value_list:
            return u" | ".join(str(v) for v in self._value_list)
        parts = []
        if self._min is not None:
            parts.append(_("Min: %s") % self._min)
        if self._max is not None:
            parts.append(_("Max: %s") % self._max)
        return u"  ".join(parts) if parts else u""

    def _hint_text(self):
        if self._type in ("BOOL", "ACTION"):
            return _("YELLOW = toggle  |  GREEN = save  |  RED = cancel")
        return _("LEFT/RIGHT = change  |  GREEN = save  |  RED = cancel")

    # ------------------------------------------------------------------

    def _toggle(self):
        if self._type in ("BOOL", "ACTION"):
            self._value = not (str(self._value).lower() in ("true", "1"))
            self["dp_value"].setText(self._display())
        elif self._value_list:
            self._adjust(1)

    def _adjust(self, direction):
        if self._type in ("BOOL", "ACTION"):
            self._toggle()
            return

        if self._value_list:
            try:
                idx = self._value_list.index(self._value)
            except ValueError:
                idx = 0
            self._value = self._value_list[(idx + direction) % len(self._value_list)]

        elif self._type == "FLOAT":
            try:
                val = float(self._value) + direction * float(self._step)
                if self._min is not None:
                    val = max(float(self._min), val)
                if self._max is not None:
                    val = min(float(self._max), val)
                self._value = round(val, 1)
            except (TypeError, ValueError):
                pass

        elif self._type == "INTEGER":
            try:
                val = int(float(self._value)) + direction * int(self._step)
                if self._min is not None:
                    val = max(int(float(self._min)), val)
                if self._max is not None:
                    val = min(int(float(self._max)), val)
                self._value = val
            except (TypeError, ValueError):
                pass

        self["dp_value"].setText(self._display())

    # ------------------------------------------------------------------

    def _save(self):
        try:
            new_value = coerce_value(self._type, self._value)
            self._save_fn(new_value)
            self.close(True)
        except Exception as exc:
            self.session.open(
                MessageBox,
                _("Error setting value: %s") % str(exc),
                MessageBox.TYPE_ERROR,
                timeout=6,
            )


# ===========================================================================
# SysVarListScreen  –  CCU3 system variables
# ===========================================================================

class SysVarListScreen(BaseListScreen):

    def __init__(self, session, app):
        BaseListScreen.__init__(
            self, session,
            _("System Variables"),
            _("OK = set value  |  GREEN = refresh"),
        )
        self.app = app
        self._sysvar_data = []
        self["key_red"]   = StaticText(_("Close"))
        self["key_green"] = StaticText(_("Refresh"))
        self.onShow.append(self._load)

    # ------------------------------------------------------------------

    def _load(self):
        self["hint"].setText(_("Loading..."))
        self.set_rows([(_("Loading..."), None)])

        settings = self.app.store.get_settings()
        self.app.api.host     = settings.get("host", "")
        self.app.api.username = settings.get("username", "")
        self.app.api.password = settings.get("password", "")

        try:
            raw = self.app.api.with_session(lambda api: api.get_system_variables())
            self._sysvar_data = [format_sysvar(sv) for sv in raw]
            rows = [
                (u"%-30s  %s" % (sv["name"], sv["value"]), sv)
                for sv in self._sysvar_data
            ]
            self.set_rows(rows)
            self["hint"].setText(_("%d system variables") % len(self._sysvar_data))

        except Exception as exc:
            self.set_rows([(u"⚠ " + str(exc), None)])
            self["hint"].setText(_("Error – check settings (BLUE)"))

    # ------------------------------------------------------------------

    def key_ok(self):
        sv = self.current_data()
        if sv:
            def save_fn(new_value):
                settings = self.app.store.get_settings()
                self.app.api.host     = settings.get("host", "")
                self.app.api.username = settings.get("username", "")
                self.app.api.password = settings.get("password", "")
                self.app.api.with_session(
                    lambda api: api.set_system_variable(sv["id"], new_value)
                )

            self.session.openWithCallback(
                lambda changed: changed and self._load(),
                SetValueScreen,
                sv["name"],
                sv["type"],
                sv["raw_value"],
                sv.get("min"),
                sv.get("max"),
                sv.get("value_list") or [],
                save_fn,
            )

    def key_green_cb(self):
        self._load()


# ===========================================================================
# SettingsScreen  –  host / credentials / refresh interval
# ===========================================================================

class SettingsScreen(BaseListScreen):

    _REFRESH_OPTIONS = [10, 15, 30, 60, 120, 300]

    def __init__(self, session, app):
        BaseListScreen.__init__(
            self, session,
            _("Settings"),
            _("Left/Right changes value"),
        )
        self.app = app
        self.settings = self.app.store.get_settings()
        self["key_green"] = StaticText(_("Save"))
        self["key_blue"]  = StaticText(_("Test connection"))
        self._render()

    # ------------------------------------------------------------------

    def _render(self):
        pw_mask = u"*" * len(self.settings.get("password", ""))
        self.set_rows([
            (u"%s: %s" % (_("CCU3 Host"),        self.settings.get("host", "")),        "host"),
            (u"%s: %s" % (_("Username"),          self.settings.get("username", "")),    "username"),
            (u"%s: %s" % (_("Password"),          pw_mask),                              "password"),
            (u"%s: %ds" % (_("Refresh interval"), self.settings.get("refresh_sec", 30)), "refresh_sec"),
        ])

    # ------------------------------------------------------------------

    def key_ok(self):
        key = self.current_data()
        if key in ("host", "username", "password"):
            current = self.settings.get(key, "")
            self.session.openWithCallback(
                lambda txt, k=key: self._on_text(k, txt),
                VirtualKeyBoard,
                title=_(key.replace("_", " ").title()),
                text=current,
            )

    def _on_text(self, key, text):
        if text is not None:
            self.settings[key] = text
            self._render()

    def key_left(self):  self._rotate(self.current_data(), -1)
    def key_right(self): self._rotate(self.current_data(), 1)

    def _rotate(self, key, direction):
        if key != "refresh_sec":
            return
        values  = self._REFRESH_OPTIONS
        current = self.settings.get("refresh_sec", 30)
        if current not in values:
            current = 30
        idx = (values.index(current) + direction) % len(values)
        self.settings["refresh_sec"] = values[idx]
        self._render()

    def key_green_cb(self):
        self.app.store.save_settings(self.settings)
        self.app.apply_settings(self.settings)
        self.session.open(
            MessageBox, _("Settings saved"), MessageBox.TYPE_INFO, timeout=3
        )
        self.close(True)

    def key_blue_cb(self):
        # Apply current (unsaved) host/credentials before testing
        self.app.api.host     = self.settings.get("host", "")
        self.app.api.username = self.settings.get("username", "")
        self.app.api.password = self.settings.get("password", "")
        ok  = self.app.api.test_connection()
        msg = (
            _("Connection test successful")
            if ok else
            _("Connection test failed: check host and credentials")
        )
        self.session.open(MessageBox, msg, MessageBox.TYPE_INFO, timeout=5)


# ===========================================================================
# InfoScreen  –  plugin info + BuyMeACoffee QR
# ===========================================================================

class InfoScreen(Screen):

    skin = """
        <screen name="InfoScreen" position="center,90" size="1000,620"
                title="Homematic CCU3 Info">
            <widget source="title" render="Label"
                    position="20,10" size="960,35" font="Regular;30" />
            <widget name="body"    position="20,55"  size="690,510"
                    scrollbarMode="showOnDemand" />
            <widget name="qr"      position="740,100" size="240,240"
                    alphatest="blend" />
            <widget source="support" render="Label"
                    position="20,555" size="960,24" font="Regular;18"
                    foregroundColor="#666666" />
            <ePixmap pixmap="skin_default/buttons/red.png"
                     position="20,580" size="220,30" alphatest="on" />
            <widget source="key_red" render="Label"
                    position="20,580" size="220,30" font="Regular;22"
                    halign="center" valign="center" transparent="1" />
        </screen>"""

    def __init__(self, session):
        Screen.__init__(self, session)
        self["title"]   = StaticText(_("Information"))
        self["key_red"] = StaticText(_("Close"))
        self["support"] = StaticText(_SUPPORT_TEXT)
        self["body"]    = ScrollLabel(self._info_text())
        self["qr"]      = Pixmap()
        self.onLayoutFinish.append(self._load_qr)

        self["actions"] = ActionMap(
            ["OkCancelActions", "DirectionActions", "ColorActions"],
            {
                "cancel": self.close,
                "ok":     self.close,
                "red":    self.close,
                "up":     self["body"].pageUp,
                "down":   self["body"].pageDown,
                "left":   self["body"].pageUp,
                "right":  self["body"].pageDown,
            },
            -1,
        )

    @staticmethod
    def _info_text():
        return u"\n".join([
            u"Homematic CCU3 Plugin  v1.0.0",
            u"",
            u"Zeigt alle Homematic-Geräte und Systemvariablen der CCU3",
            u"auf dem TV-Bildschirm an.  Werte lassen sich direkt auf dem",
            u"TV ändern – Thermostattemperatur, Schalter an/aus, Dimmer,",
            u"Rolladen-Position, Systemvariablen u.v.m.",
            u"",
            u"Voraussetzungen:",
            u"  · Homematic CCU3 im lokalen Netzwerk erreichbar",
            u"  · JSON-RPC API aktiv (CCU3-Standard)",
            u"  · Benutzerkonto mit Lese- und Schreibrechten",
            u"",
            u"Steuerung:",
            u"  Hauptmenü   ROT  = Schliessen",
            u"              GRÜN = Aktualisieren",
            u"              GELB = Einstellungen",
            u"              BLAU = Informationen",
            u"  Geräte      OK   = Details/Wert setzen",
            u"              GRÜN = Aktualisieren",
            u"  Details     OK   = Wert setzen (nur ✎-Einträge)",
            u"  Wert setzen LINKS/RECHTS = Wert ändern",
            u"              GELB = Umschalten (Bool/Schalter)",
            u"              GRÜN = Speichern",
            u"              ROT  = Abbrechen",
            u"  Systemvariablen  wie Wert setzen",
            u"  Einstellungen    OK = Text eingeben",
            u"              LINKS/RECHTS = Intervall wählen",
            u"              GRÜN = Speichern",
            u"              BLAU = Verbindungstest",
            u"",
            u"Fehlersuche:",
            u"  · Einstellungen öffnen und Verbindungstest (BLAU) starten",
            u"  · Sicherstellen, dass Port 80 der CCU3 erreichbar ist",
            u"  · Benutzername/Passwort in der CCU3 Benutzerverwaltung",
            u"    prüfen (Lese- und Schreibrechte erforderlich)",
            u"",
            u"GitHub : https://github.com/madoe21/enigma2-homematic",
            u"Support: " + BUYMEACOFFEE_URL,
        ])

    def _load_qr(self):
        candidates = [
            resolveFilename(SCOPE_PLUGINS, "Extensions/HomematicCCU/res/qr_buymeacoffee.png"),
            os.path.join(os.path.dirname(__file__), "res", "qr_buymeacoffee.png"),
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    self["qr"].instance.setPixmapFromFile(path)
                    return
                except Exception:
                    pass
