# -*- coding: utf-8 -*-
"""
Platform-neutral Homematic CCU3 JSON-RPC client.

The CCU3 exposes its full API at  http://<host>/api/homematic.cgi
using JSON-RPC 1.1.  Session authentication is done with Session.login;
the returned session ID must be passed as "_session_id_" in every
subsequent call.

No Enigma2 or Kodi imports – safe to unit-test standalone.

Portability
-----------
For a Kodi port replace only services.py and plugin.py;
this file stays unchanged.
"""
from __future__ import absolute_import

import json

# Python 2 / Python 3 compatibility ----------------------------------------
try:
    from urllib2 import Request, URLError, urlopen  # Python 2
    _PY2 = True
except ImportError:
    from urllib.error import URLError               # Python 3
    from urllib.request import Request, urlopen
    _PY2 = False
# ---------------------------------------------------------------------------


class CCU3Client(object):
    """JSON-RPC client for the Homematic CCU3.

    Parameters
    ----------
    host : str
        IP address or hostname of the CCU3 (e.g. "192.168.1.100").
    username : str
        CCU3 user name (default: "Admin").
    password : str
        CCU3 password.
    timeout : int
        HTTP timeout in seconds.
    """

    _RPC_PATH = "/api/homematic.cgi"

    def __init__(self, host="192.168.1.100", username="Admin", password="",
                 timeout=10):
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout
        self._session = None
        self._req_id = 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @property
    def _url(self):
        return "http://%s%s" % (self.host, self._RPC_PATH)

    def _call(self, method, params=None):
        """Execute one JSON-RPC call and return the ``result`` field."""
        self._req_id += 1
        payload = json.dumps({
            "method":  method,
            "id":      self._req_id,
            "params":  params or {},
            "version": "1.1",
        })
        if _PY2:
            if isinstance(payload, unicode):  # noqa: F821 – exists in Py2
                payload = payload.encode("utf-8")
        else:
            payload = payload.encode("utf-8")

        req = Request(
            self._url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            resp = urlopen(req, timeout=self.timeout)
            body = resp.read()
            if not _PY2 and isinstance(body, bytes):
                body = body.decode("utf-8", errors="replace")
            data = json.loads(body)
            if data.get("error"):
                raise CCU3Error("CCU3 error: %s" % str(data["error"]))
            return data.get("result")
        except URLError as exc:
            raise CCU3ConnectionError("Connection error: %s" % str(exc))

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def login(self):
        """Authenticate and store the session ID.  Raises on failure."""
        sid = self._call("Session.login", {
            "username": self.username,
            "password": self.password,
        })
        if not sid:
            raise CCU3AuthError("Login failed – wrong credentials?")
        self._session = sid
        return sid

    def logout(self):
        """End the session.  Safe to call even when not logged in."""
        if self._session:
            try:
                self._call("Session.logout", {"_session_id_": self._session})
            except Exception:
                pass
            self._session = None

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_devices(self):
        """Return list of all devices with channels and datapoints."""
        return self._call(
            "Device.listAllDetail", {"_session_id_": self._session}
        ) or []

    def get_system_variables(self):
        """Return list of all CCU3 system variables."""
        return self._call(
            "SysVar.getAll", {"_session_id_": self._session}
        ) or []

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def set_value(self, interface, address, value_key, value_type, value):
        """Set a single datapoint on a device channel.

        Parameters
        ----------
        interface : str
            BidCos interface name stored in the datapoint
            (e.g. "BidCos-RF", "HmIP-RF", "VirtualDevices").
        address : str
            Channel address including channel index
            (e.g. "OEQ0123456:1").
        value_key : str
            Datapoint name (e.g. "SET_POINT_TEMPERATURE", "STATE").
        value_type : str
            CCU3 type string ("BOOL", "FLOAT", "INTEGER", "ACTION", "ENUM").
        value : bool | float | int
            New value, already coerced to the correct Python type.
        """
        return self._call("Interface.setValue", {
            "_session_id_": self._session,
            "interface":    interface,
            "address":      address,
            "valueKey":     value_key,
            "type":         value_type,
            "value":        value,
        })

    def set_system_variable(self, sysvar_id, value):
        """Set a CCU3 system variable by its numeric ID."""
        return self._call("SysVar.setValue", {
            "_session_id_": self._session,
            "id":           sysvar_id,
            "value":        value,
        })

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def test_connection(self):
        """Try to login and logout.  Returns True on success."""
        try:
            self.login()
            self.logout()
            return True
        except Exception:
            return False

    def with_session(self, fn):
        """Login, run ``fn(self)``, logout (even on error).

        This helper makes callers concise:

            client.with_session(lambda api: api.set_value(...))

        The caller's exception propagates after logout so the UI layer
        can display it.
        """
        self.login()
        try:
            return fn(self)
        finally:
            self.logout()


# ------------------------------------------------------------------
# Custom exceptions – allow callers to distinguish error categories
# ------------------------------------------------------------------

class CCU3Error(Exception):
    """Generic CCU3 API error (the CCU returned an error object)."""


class CCU3ConnectionError(CCU3Error):
    """Network / connection error reaching the CCU3."""


class CCU3AuthError(CCU3Error):
    """Authentication failure (wrong credentials / locked user)."""
