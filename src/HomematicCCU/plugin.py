# -*- coding: utf-8 -*-
"""
Enigma2 plugin entry point for HomematicCCU.

AppContext wires together the platform-neutral modules (api, store)
with the Enigma2 plugin descriptor.

For a Kodi port, replace this file and services.py while keeping
api.py, core.py, config_store.py, and all business logic unchanged.
"""
from __future__ import absolute_import

from Plugins.Plugin import PluginDescriptor

from . import _
from .api import CCU3Client
from .config_store import HomematicStore
from .screens import HomematicMainScreen


# ---------------------------------------------------------------------------
# Application context  –  single instance per session
# ---------------------------------------------------------------------------

class AppContext(object):
    """Container wiring together store and API client."""

    def __init__(self, session):
        self.session = session
        self.store   = HomematicStore()
        settings     = self.store.get_settings()
        self.api     = CCU3Client(
            host=settings.get("host",     "192.168.1.100"),
            username=settings.get("username", "Admin"),
            password=settings.get("password", ""),
        )

    def apply_settings(self, settings):
        """Apply settings changed in the UI to the running API client."""
        self.api.host     = settings.get("host",     "192.168.1.100")
        self.api.username = settings.get("username", "Admin")
        self.api.password = settings.get("password", "")
        self.api._session = None    # force re-login on next request


# ---------------------------------------------------------------------------
# Plugin entry points
# ---------------------------------------------------------------------------

def main(session, **kwargs):
    app = AppContext(session)
    session.open(HomematicMainScreen, app)


def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name=        "Homematic CCU3",
            description= _(u"Homematic Geräte und Status am TV anzeigen"),
            where=       PluginDescriptor.WHERE_PLUGINMENU,
            fnc=         main,
            icon=        "plugin.png",
        )
    ]
