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
daemon.proxy
~~~~~~~~~~~~~~~~~

This module implements a simple proxy server using Python's socket and threading libraries.
It routes incoming HTTP requests to backend services based on hostname mappings and returns
the corresponding responses to clients.

Requirement:
-----------------
- socket: provides socket networking interface.
- threading: enables concurrent client handling via threads.
- response: customized :class: `Response <Response>` utilities.
- httpadapter: :class: `HttpAdapter <HttpAdapter >` adapter for HTTP request processing.
- dictionary: :class: `CaseInsensitiveDict <CaseInsensitiveDict>` for managing headers and cookies.

"""
import socket
import threading
from .response import *
from .httpadapter import HttpAdapter
from .dictionary import CaseInsensitiveDict

#: A dictionary mapping hostnames to backend IP and port tuples.
#: Used to determine routing targets for incoming requests.
PROXY_PASS = {
    "192.168.56.103:8080": ('192.168.56.103', 9000),
    "app1.local": ('192.168.56.103', 9001),
    "app2.local": ('192.168.56.103', 9002),
}


def forward_request(host: str, port: int, request: str) -> bytes:
    """
    Forwards an HTTP request to a backend server and retrieves the response.

    :params host (str): IP address of the backend server.
    :params port (int): port number of the backend server.
    :params request (str): incoming HTTP request.

    :returns: Raw HTTP response from the backend server. If the connection
    fails, returns a 404 Not Found response.
    :rtype: bytes
    """

    backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        backend.connect((host, port))
        backend.sendall(request.encode())
        response = b""
        while True:
            chunk = backend.recv(4096)
            if not chunk: break
            response += chunk
        return response
    except socket.error as e:
      print(f"Socket error: {e}")
      return (
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 13\r\n"
            "Connection: close\r\n"
            "\r\n"
            "404 Not Found"
        ).encode()


def resolve_routing_policy(hostname: str, routes: dict) -> tuple:
    """
    Handles an routing policy to return the matching proxy_pass.
    It determines the target backend to forward the request to.

    :params host (str): IP address of the request target server.
    :params port (int): port number of the request target server. (**LHTrieu**: idk what this does)
    :params routes (dict): dictionary mapping hostnames and location.

    :returns: `(proxy_host, proxy_port)` to forward the request.
    :rtype: tuple
    """

    print(hostname)
    proxy_map, policy = routes.get(hostname, ([], None))
    if isinstance(proxy_map, list):
        if len(proxy_map) == 0:
            print(f"[Proxy] Hostname {hostname} resolved to no route")
            # TODO: implement the error handling for non mapped host
            #       the policy is design by team, but it can be 
            #       basic default host in your self-defined system
            # Currently using a dummy host to raise an invalid connection
            proxy_host, proxy_port = '127.0.0.1', '9000'
        elif len(proxy_map) == 1:
            print(f"[Proxy] Hostname {hostname} resolved to a single route")
            proxy_host, proxy_port = proxy_map[0].split(":", 2)
        else:
            print(f"[Proxy] Hostname {hostname} resolved to multiple routes with policy {policy}")
            if policy == "round-robin":
                selected = proxy_map.pop(0)
                proxy_map.append(selected)
                proxy_host, proxy_port = selected.split(":", 2)
            else:
                print(f"[Proxy] Unknown routing policy {policy} for hostname {hostname}")
                proxy_host, proxy_port = proxy_map[0].split(":", 2)
    else:
        print(f"[Proxy] Hostname {hostname} resolved to a single route")
        proxy_host, proxy_port = proxy_map.split(":", 2)

    print(f"[Proxy] Hostname {hostname} resolved to backend {proxy_host}:{proxy_port}")
    return proxy_host, proxy_port


def handle_client(ip: str, port: int, conn: socket.socket, addr: tuple, routes: dict):
    """
    Handles an individual client connection by parsing the request,
    determining the target backend, and forwarding the request.

    The handler extracts the Host header from the request to
    matches the hostname against known routes. In the matching
    condition, it forwards the request to the appropriate backend.

    The handler sends the backend response back to the client or
    returns 404 if the hostname is unreachable or is not recognized.

    :params ip (str): IP address of the proxy server.
    :params port (int): port number of the proxy server.
    :params conn (socket.socket): client connection socket.
    :params addr (tuple): client address (IP, port).
    :params routes (dict): dictionary mapping hostnames and location.
    """

    request = conn.recv(1024).decode()

    # Extract hostname
    for line in request.splitlines():
        if line.lower().startswith('host:'):
            hostname = line.split(':', 1)[1].strip()

    print(f"[Proxy] {addr} at Host: {hostname}")

    # Resolve the matching destination in routes and need conver port
    # to integer value
    resolved_host, resolved_port = resolve_routing_policy(hostname, routes)
    try: resolved_port = int(resolved_port)
    except ValueError: print("Not a valid integer")

    if resolved_host:
        print(f"[Proxy] Host name {hostname} is forwarded to {resolved_host}:{resolved_port}")
        response = forward_request(resolved_host, resolved_port, request)        
    else:
        response = (
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Type: text/plain\r\n"
            "Content-Length: 13\r\n"
            "Connection: close\r\n"
            "\r\n"
            "404 Not Found"
        ).encode()
    conn.sendall(response)
    conn.close()

def run_proxy(ip: str, port: int, routes: dict):
    """
    Starts the proxy server and listens for incoming connections. 

    The process finds the proxy server to the specified IP and port.
    In each incoming connection, it accepts the connection and
    spawns a new thread for each client using `handle_client`.
 

    :params ip (str): IP address to bind the proxy server.
    :params port (int): port number to listen on.
    :params routes (dict): dictionary mapping hostnames and location.
    """

    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        proxy.bind((ip, port))
        proxy.listen(50)
        print(f"[Proxy] Listening on IP {ip} port {port}")
        while True:
            conn, addr = proxy.accept()
            # TODO: implement the step of the client incoming connection
            #       using multi-thread programming with the
            #       provided handle_client routine
            # (DONE)
            threading.Thread(target=handle_client, args=(ip, port, conn, addr, routes)).start()
    except socket.error as e:
      print(f"Socket error: {e}")

def create_proxy(ip, port, routes):
    """
    Entry point for launching the proxy server.

    :params ip (str): IP address to bind the proxy server.
    :params port (int): port number to listen on.
    :params routes (dict): dictionary mapping hostnames and location.
    """

    run_proxy(ip, port, routes)
