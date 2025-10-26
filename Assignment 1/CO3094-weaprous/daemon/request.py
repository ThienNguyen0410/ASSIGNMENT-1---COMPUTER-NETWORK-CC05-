#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.request
~~~~~~~~~~~~~~~~~

This module provides a Request object to manage and persist 
request settings (cookies, auth, proxies).
"""
from .dictionary import CaseInsensitiveDict
from urllib.parse import parse_qs, urlsplit, unquote, urlencode
import json as _json


class Request():
    """The fully mutable "class" `Request <Request>` object,
    containing the exact bytes that will be sent to the server.

    Instances are generated from a "class" `Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    Usage::

      >>> import deamon.request
      >>> req = request.Request()
      ## Incoming message obtain aka. incoming_msg
      >>> r = req.prepare(incoming_msg)
      >>> r
      <Request>
    """
    __attrs__ = [
        "method",
        "url",
        "headers",
        "body",
        "reason",
        "cookies",
        "body",
        "routes",
        "hook",
    ]

    def __init__(self):
        #: HTTP verb to send to the server.
        self.method = None
        #: HTTP URL to send the request to.
        self.url = None
        #: dictionary of HTTP headers.
        self.headers = None
        #: HTTP path
        self.path = None        
        # The cookies set used to create Cookie header
        self.cookies = None
        #: request body to send to the server.
        self.body = None
        #: Routes
        self.routes = {}
        #: Hook point for routed mapped-path
        self.hook = None
        #: HTTP version (from request-line)
        self.version = None

    # ---------- helpers ----------
    def _parse_cookies_header(self, cookie_header: str):
        """
        Parse a Cookie header string into a dict.
        Example: "a=1; b=hello" -> {"a":"1","b":"hello"}
        """
        jar = {}
        if not cookie_header:
            return jar
        parts = cookie_header.split(";")
        for part in parts:
            if "=" in part:
                k, v = part.split("=", 1)
                jar[k.strip()] = v.strip()
        return jar

    # ---------- parsing incoming request ----------
    def extract_request_line(self, request):
        try:
            # request could include body; only look at header part
            head = request.split("\r\n\r\n", 1)[0]
            lines = head.splitlines()
            first_line = lines[0]
            method, target, version = first_line.split()

            # Map "/" to "/index.html" as course skeleton expects
            if target == '/':
                path = '/index.html'
            else:
                # keep only path+query from absolute-form if any
                # and decode %xx in path part
                url = urlsplit(target)
                path = unquote(url.path) if url.path else target
        except Exception:
            return None, None, None

        return method, path, version
             
    def prepare_headers(self, request):
        """Prepares the given HTTP headers (case-insensitive)."""
        head = request.split("\r\n\r\n", 1)[0]
        lines = head.split('\r\n')
        headers = CaseInsensitiveDict()
        for line in lines[1:]:
            if not line:
                break
            if ': ' in line:
                key, val = line.split(': ', 1)
                headers[key] = val
        return headers

    def prepare(self, request, routes=None):
        """Prepares the entire request with the given parameters.
        `request` is the raw HTTP request string (headers + optional body).
        """

        # Separate header and body (if any)
        if "\r\n\r\n" in request:
            head, body_part = request.split("\r\n\r\n", 1)
        else:
            head, body_part = request, ""

        # Prepare the request line from the request header
        self.method, self.path, self.version = self.extract_request_line(head)
        self.url = self.path  # keep url for backward-compat
        print("[Request] {} path {} version {}".format(self.method, self.path, self.version))

        #
        # @bksysnet Preapring the webapp hook with WeApRous instance
        #
        if routes:
            self.routes = routes
            self.hook = routes.get((self.method, self.path))
            # self.hook manipulation (if any) goes here

        # Headers (case-insensitive)
        self.headers = self.prepare_headers(head)

        # Cookies from header -> dict
        cookie_header = self.headers.get('Cookie', '')
        self.cookies = self._parse_cookies_header(cookie_header)

        # Respect Content-Length if present when extracting body
        try:
            clen = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            clen = 0
        if clen > 0:
            self.body = body_part[:clen]
        else:
            # No content length -> treat as empty for this assignment
            self.body = ""

        return

    # ---------- building outgoing request (not strictly needed server-side) ----------
    def prepare_body(self, data, files, json=None):
        """
        Prepare self.body & related headers for an outgoing request.
        Kept for completeness with course skeleton; minimal implementation.
        """
        body_bytes = b""
        if json is not None:
            body_str = _json.dumps(json, ensure_ascii=False)
            self.headers = self.headers or CaseInsensitiveDict()
            self.headers["Content-Type"] = "application/json; charset=utf-8"
            body_bytes = body_str.encode("utf-8")
        elif isinstance(data, (bytes, bytearray)):
            body_bytes = bytes(data)
        elif isinstance(data, str):
            body_bytes = data.encode("utf-8")
        elif isinstance(data, dict) and data:
            # application/x-www-form-urlencoded
            body_str = urlencode(data, doseq=True)
            self.headers = self.headers or CaseInsensitiveDict()
            self.headers["Content-Type"] = "application/x-www-form-urlencoded"
            body_bytes = body_str.encode("utf-8")

        self.body = body_bytes.decode("utf-8") if isinstance(body_bytes, (bytes, bytearray)) else (self.body or "")
        self.prepare_content_length(self.body)
        return

    def prepare_content_length(self, body):
        if self.headers is None:
            self.headers = CaseInsensitiveDict()
        if body is None:
            self.headers["Content-Length"] = "0"
        else:
            if isinstance(body, str):
                length = len(body.encode("utf-8"))
            else:
                # best-effort
                length = len(body)
            self.headers["Content-Length"] = str(length)
        return

    def prepare_auth(self, auth, url=""):
        """
        Placeholder for auth preparation (not required in this assignment).
        """
        # self.auth = ...
        return

    def prepare_cookies(self, cookies):
        """
        Accept either a ready-made Cookie string or a dict of key->value.
        """
        if self.headers is None:
            self.headers = CaseInsensitiveDict()

        if isinstance(cookies, dict):
            pairs = [f"{k}={v}" for k, v in cookies.items()]
            self.headers["Cookie"] = "; ".join(pairs)
        else:
            # assume string already formatted
            self.headers["Cookie"] = cookies
