# -*- coding: utf-8 -*-
"""
i18n bootstrap for HomematicCCU.

Falls back to a German dictionary when no compiled .mo file is found.
For a Kodi port, replace this file; all other modules call _() without
importing from Enigma2 themselves.
"""
from __future__ import absolute_import

import gettext

from Components.Language import language
from Tools.Directories import SCOPE_PLUGINS, resolveFilename

PLUGIN_DOMAIN = "HomematicCCU"
PLUGIN_PATH = "Extensions/HomematicCCU/locale"

_DE_FALLBACK = {
    # General
    "Back": "Zurück",
    "Exit": "Beenden",
    "Save": "Speichern",
    "Cancel": "Abbrechen",
    "Refresh": "Aktualisieren",
    "Information": "Informationen",
    "Settings": "Einstellungen",
    "Loading...": "Wird geladen...",
    "No items available": "Keine Einträge verfügbar",
    # Main menu
    "Homematic CCU3": "Homematic CCU3",
    "Devices": "Geräte",
    "System Variables": "Systemvariablen",
    # Device list
    "OK = details  |  GREEN = refresh": "OK = Details  |  GRÜN = Aktualisieren",
    "%d devices loaded  •  refresh every %ds": "%d Geräte geladen  •  Aktualisierung alle %ds",
    "Using cached data. Error: %s": "Gecachte Daten. Fehler: %s",
    "Error – check settings (BLUE)": "Fehler – Einstellungen prüfen (BLAU)",
    # Device detail
    "OK = set value  |  only ✎ entries are writable": "OK = Wert setzen  |  nur ✎-Einträge sind schreibbar",
    # Set value
    "Set Value": "Wert setzen",
    "Set System Variable": "Systemvariable setzen",
    "Toggle": "Umschalten",
    "YELLOW = toggle  |  GREEN = save  |  RED = cancel": "GELB = Umschalten  |  GRÜN = Speichern  |  ROT = Abbrechen",
    "LEFT/RIGHT = change  |  GREEN = save  |  RED = cancel": "LINKS/RECHTS = Ändern  |  GRÜN = Speichern  |  ROT = Abbrechen",
    "AN / AUS": "AN / AUS",
    "Min: %s": "Min: %s",
    "Max: %s": "Max: %s",
    "Error setting value: %s": "Fehler beim Setzen des Werts: %s",
    # System variables
    "%d system variables": "%d Systemvariablen",
    "OK = set value  |  GREEN = refresh": "OK = Wert setzen  |  GRÜN = Aktualisieren",
    # Settings
    "Left/Right changes value": "Links/Rechts ändert den Wert",
    "CCU3 Host": "CCU3 Host/IP",
    "Username": "Benutzername",
    "Password": "Passwort",
    "Refresh interval": "Aktualisierungsintervall",
    "Settings saved": "Einstellungen gespeichert",
    "Test connection": "Verbindung testen",
    "Connection test successful": "Verbindungstest erfolgreich",
    "Connection test failed: check host and credentials": "Verbindungstest fehlgeschlagen: Host und Zugangsdaten prüfen",
    # Info
    "OK = open  |  RED/Exit = quit": "OK = öffnen  |  ROT/Exit = beenden",
}


def localeInit():
    gettext.bindtextdomain(
        PLUGIN_DOMAIN, resolveFilename(SCOPE_PLUGINS, PLUGIN_PATH)
    )


def _(txt):
    translated = gettext.dgettext(PLUGIN_DOMAIN, txt)
    if translated != txt:
        return translated
    try:
        lang = language.getLanguage()[:2]
    except Exception:
        lang = "en"
    if lang == "de":
        return _DE_FALLBACK.get(txt, txt)
    return txt


localeInit()
try:
    language.addCallback(localeInit)
except Exception:
    pass
