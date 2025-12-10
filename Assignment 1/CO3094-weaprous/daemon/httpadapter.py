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
daemon.httpadapter
~~~~~~~~~~~~~~~~~

This module provides a http adapter object to manage and persist 
http settings (headers, bodies). The adapter supports both
raw URL paths and RESTful route definitions, and integrates with
Request and Response objects to handle client-server communication.
"""

from .request import Request
from .response import Response
from .dictionary import CaseInsensitiveDict
import os

class HttpAdapter:
    """
    A mutable :class:`HTTP adapter <HTTP adapter>` for managing client connections
    and routing requests.

    The `HttpAdapter` class encapsulates the logic for receiving HTTP requests,
    dispatching them to appropriate route handlers, and constructing responses.
    It supports RESTful routing via hooks and integrates with :class:`Request <Request>` 
    and :class:`Response <Response>` objects for full request lifecycle management.

    Attributes:
        ip (str): IP address of the client.
        port (int): Port number of the client.
        conn (socket): Active socket connection.
        connaddr (tuple): Address of the connected client.
        routes (dict): Mapping of route paths to handler functions.
        request (Request): Request object for parsing incoming data.
        response (Response): Response object for building and sending replies.
    """

    __attrs__ = [
        "ip",
        "port",
        "conn",
        "connaddr",
        "routes",
        "request",
        "response",
    ]

    def __init__(self, ip, port, conn, connaddr, routes):
        """
        Initialize a new HttpAdapter instance.
        :param ip (str): IP address of the client.
        :param port (int): Port number of the client.
        :param conn (socket): Active socket connection.
        :param connaddr (tuple): Address of the connected client.
        :param routes (dict): Mapping of route paths to handler functions.
        """

        #: IP address.
        self.ip = ip
        #: Port.
        self.port = port
        #: Connection
        self.conn = conn
        #: Connection address
        self.connaddr = connaddr
        #: Routes
        self.routes = routes
        #: Request
        self.request = Request()
        #: Response
        self.response = Response()

    def http_login(self, body):
        #Body's form: username=admin&password=password
        creds = {}
        for pair in body.split("&"):
            if "=" in pair:
                key,value = pair.split("=", 1)
                creds[key] = value

        correct_username = creds.get("username", "")
        correct_password = creds.get("password", "")

        if correct_username == "admin" and correct_password == "password":
         
            body = (
                "<html><head><title>Welcome</title></head>"
                "<body><h1>Login successful!</h1>"
                "<p>Welcome, admin!</p>"
                "<a href='/index.html'>Go to index</a>"
                "</body></html>"
            )

            headers = {
            "Content-Type": "text/html; charset=utf-8",
            "Set-Cookie": "auth=true; Path=/",
            }
            
            return ("200 OK", headers, body)
        
        #Invalid authentication
        body = (
            "<html><head><title>Login Failed</title></head>"
            "<body><h1>401 Unauthorized</h1>"
            "<p>Invalid username or password</p>"
            "<p><a href='/login.html'>Try again</a></p>"
            "</body></html>"
        )
        headers = {"Content-Type" : "text/html; charset=utf-8"}
        return ("401 Unauthorized", headers, body)

  

    def handle_client(self, conn, addr, routes):
        """
        Handle an incoming client connection.

        This method reads the request from the socket, prepares the request object,
        invokes the appropriate route handler if available, builds the response,
        and sends it back to the client.

        :param conn (socket): The client socket connection.
        :param addr (tuple): The client's address.
        :param routes (dict): The route mapping for dispatching requests.
        """

        # Connection handler.
        self.conn = conn        
        # Connection address.
        self.connaddr = addr
        # Request handler
        req = self.request
        # Response handler
        resp = self.response

        try:
            raw_req = conn.recv(4096).decode("utf-8", errors = "ignore")
            if not raw_req:
                conn.close()
                return
            
            req.prepare(raw_req, routes)

            status = ""
            body = ""
            headers = {}

            #Task 1A: Handle login
            if req.method == "POST" and req.path == "/login":
                status, headers, body = self.http_login(req.body)
            #Task 1B: Hanle login
            elif req.method == "GET":
                if req.path == "/":
                    req.path = "/index.html"
            
                auth =  req.cookies.get("auth")

                if req.path in ("/", "/index.html") and auth != "true" or (req.path == "/peer" and auth != "true"):
                    status = "401 Unauthorized"
                    headers = {"Content-Type": "text/html; charset=utf-8"}
                    body = (
                            "<html><head><title>401</title></head>"
                            "<body><h1>401 Unauthorized</h1>"
                            "<p>Please <a href='/login.html'>login</a> first</p>"
                            "</body></html>"
                        )
                else:
                    base_dir = os.getcwd()
                    if req.path.startswith("/static/"):
                        filepath = os.path.join(base_dir, req.path.lstrip("/"))
                    else:
                        filepath = os.path.join(base_dir, "www", req.path.lstrip("/"))

                        # Nếu file tồn tại
                    if os.path.exists(filepath) and os.path.isfile(filepath):
                            with open(filepath, "rb") as f:
                                body = f.read()
                            status = "200 OK"

                            # Đoán content-type cơ bản
                            if filepath.endswith(".html"):
                                content_type = "text/html; charset=utf-8"
                            elif filepath.endswith(".css"):
                                content_type = "text/css"
                            elif filepath.endswith(".js"):
                                content_type = "application/javascript"
                            elif filepath.endswith((".jpg", ".jpeg")):
                                content_type = "image/jpeg"
                            elif filepath.endswith(".png"):
                                content_type = "image/png"
                            elif filepath.endswith(".ico"):
                                content_type = "image/x-icon"
                            else:
                                content_type = "application/octet-stream"

                            headers = {"Content-Type": content_type}

                    else:
                        # File không tồn tại
                        status = "404 Not Found"
                        headers = {"Content-Type": "text/html; charset=utf-8"}
                        body = (
                            "<html><head><title>404</title></head>"
                            "<body><h1>404 Not Found</h1>"
                            "<p>The requested page could not be found.</p>"
                            "</body></html>"
                        )
            if hasattr(req,"hook") and req.hook:
                status, headers, body_bytes = self.handle_weaprous(req, resp)
                body = body_bytes  # Replace body with hook result
        #Graph into a http response
            if isinstance(body, str):
                body_bytes = body.encode("utf-8")
            else:
                body_bytes = body

            response_data = (
                f"HTTP/1.1 {status}\r\n"
                + "".join(f"{k}: {v}\r\n" for k, v in headers.items())
                + "\r\n"
            ).encode("utf-8") + body_bytes

            conn.sendall(response_data)
        except Exception as e:
            err_body = f"<h1>500 Internal Server Error</h1><p>{e}</p>"
            conn.sendall(
                b"HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/html\r\n\r\n"
                + err_body.encode("utf-8")
            )
        finally:
            conn.close()


        #End of task 1: HTTP server with cookie session

    """-------------------------------------------------------------------------------------------"""
        #Start task 2: Implement hybrid chat application
    def handle_weaprous(self, req, resp):
        """
        Handle WeApRous-style route hooks.
        This allows returning JSON responses from hooks like login.
        """ 
        import json

        def to_bytes(payload, current_ct=None):
            """Convert payload to bytes and set content-type if needed."""
            if isinstance(payload, (bytes, bytearray)):
                return bytes(payload), current_ct
            if payload is None:
                return b'{"status":"success"}', "application/json; charset=utf-8"
            if isinstance(payload, (dict, list)):
                return json.dumps(payload).encode("utf-8"), "application/json; charset=utf-8"
            if isinstance(payload, str):
                return payload.encode("utf-8"), current_ct or "text/plain; charset=utf-8"
            return str(payload).encode("utf-8"), current_ct or "text/plain; charset=utf-8"

        try:
            body_text = req.body.decode("utf-8") if isinstance(req.body, (bytes, bytearray)) else (req.body or "")
            result = req.hook(headers=req.headers, body=body_text)

                # Nếu hook trả về tuple (status, headers, payload)
            if isinstance(result, tuple) and len(result) == 3:
                status, headers, payload = result
                headers = dict(headers or {})
                payload_bytes, ct = to_bytes(payload, headers.get("Content-Type"))
                headers.setdefault("Content-Type", ct)
                headers.setdefault("Access-Control-Allow-Origin", "*")
                return status, headers, payload_bytes

                # Nếu hook trả về dict/list/str/None
            payload_bytes, ct = to_bytes(result)
            headers = {
                    "Content-Type": ct,
                    "Access-Control-Allow-Origin": "*",
                }
            return "200 OK", headers, payload_bytes

        except Exception as ex:
            err = {"status": "error", "error": str(ex)}
            return (
                "500 Internal Server Error",
                {
                    "Content-Type": "application/json; charset=utf-8",
                    "Access-Control-Allow-Origin": "*",
                },
                json.dumps(err).encode("utf-8"),
            )





    @property
    def extract_cookies(self, req, resp):
        """
        Build cookies from the :class:`Request <Request>` headers.

        :param req:(Request) The :class:`Request <Request>` object.
        :param resp: (Response) The res:class:`Response <Response>` object.
        :rtype: cookies - A dictionary of cookie key-value pairs.
        """
        req = self.request
        cookies = {}
        for header in req.headers:
            if header.startswith("Cookie:"):
                cookie_str = header.split(":", 1)[1].strip()
                for pair in cookie_str.split(";"):
                    key, value = pair.strip().split("=")
                    cookies[key] = value
        return cookies

    def get_header_from_request(self, req):
        return
    def get_encoding_from_headers(self, header):
        """
        Extract character encoding from HTTP headers.
        If not specified, default to 'utf-8'.
        """
        content_type = header.get("Content-Type")
        if not content_type:
            return "utf-8"

        # Tìm phần charset trong header
        if "charset=" in content_type:
            return content_type.split("charset=")[-1].split(";")[0].strip()
        
        # Mặc định fallback
        return "utf-8"
    
    def extract_cookies(req):
        return

    def build_response(self, req, resp):
        """Builds a :class:`Response <Response>` object 

        :param req: The :class:`Request <Request>` used to generate the response.
        :param resp: The  response object.
        :rtype: Response
        """
        response = Response()

        # Set encoding.
        response.encoding = self.get_encoding_from_headers(response.headers)
        response.raw = resp
        response.reason = response.raw.reason

        if isinstance(req.url, bytes):
            response.url = req.url.decode("utf-8")
        else:
            response.url = req.url

        # Add new cookies from the server.
        response.cookies = self.extract_cookies(req)

        # Give the Response some context.
        response.request = req
        response.connection = self

        return response

    # def get_connection(self, url, proxies=None):
        # """Returns a url connection for the given URL. 

        # :param url: The URL to connect to.
        # :param proxies: (optional) A Requests-style dictionary of proxies used on this request.
        # :rtype: int
        # """

        # proxy = select_proxy(url, proxies)

        # if proxy:
            # proxy = prepend_scheme_if_needed(proxy, "http")
            # proxy_url = parse_url(proxy)
            # if not proxy_url.host:
                # raise InvalidProxyURL(
                    # "Please check proxy URL. It is malformed "
                    # "and could be missing the host."
                # )
            # proxy_manager = self.proxy_manager_for(proxy)
            # conn = proxy_manager.connection_from_url(url)
        # else:
            # # Only scheme should be lower case
            # parsed = urlparse(url)
            # url = parsed.geturl()
            # conn = self.poolmanager.connection_from_url(url)

        # return conn


    def add_headers(self, request):
        """
        Add headers to the request.

        This method is intended to be overridden by subclasses to inject
        custom headers. It does nothing by default.

        
        :param request: :class:`Request <Request>` to add headers to.
        """
        pass

    def build_proxy_headers(self, proxy):
        """Returns a dictionary of the headers to add to any request sent
        through a proxy. 

        :class:`HttpAdapter <HttpAdapter>`.

        :param proxy: The url of the proxy being used for this request.
        :rtype: dict
        """
        headers = {}
        #
        # TODO: build your authentication here
        #       username, password =...
        # we provide dummy auth here
        #
        proxy_login = ""
        if "://" in proxy and "@" in proxy:
            proxy_login = proxy.split("://")[1]
            proxy_login = proxy_login.split("@")[0]

        elif "://" in proxy:
            proxy_login = proxy.split("://")[1]

        elif "@" in proxy:
            proxy_login = proxy.split("@")[0]
        
        proxy_username = proxy_login.split(":")[0]
        proxy_password = proxy_login.split(":")[1]

        username, password = (proxy_username, proxy_password)
        
        if username:
            # headers["Proxy-Authorization"] = (username, password)
            headers["Proxy-Authorization"] = (proxy_username, proxy_password)

        return headers