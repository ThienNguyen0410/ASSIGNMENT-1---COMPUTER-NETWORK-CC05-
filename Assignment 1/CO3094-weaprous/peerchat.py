#THE LATES VERSION OF PEERCHAT.PY
import socket
import threading
import json
import requests
import argparse
import time
import os

connected_peers = {}
def detect_local_ip():
    """Detect an outward-facing IP (works without internet if routed)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def listen_peer(local_ip, local_port):
    """Listen for incoming peer messages."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((local_ip, local_port))
    except OSError:
        print(f"[Peer warning] Cannot bind {local_ip}, fallback to 0.0.0.0")
        s.bind(("0.0.0.0", local_port))
    s.listen(10)
    print(f"[Peer] Listening at {local_ip}:{local_port}")

    while True:
        try:
            conn, addr = s.accept()
            # Receive data
            data = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
            if data:
                text = data.decode("utf-8", errors="ignore").strip()
                print(f"[Message from {addr}]: {text}\n> ", end="", flush=True)
            conn.close()
        except Exception as e:
            print(f"[Peer listener error] {e}")


def login(server_ip, server_port, username, password):
    url = f"http://{server_ip}:{server_port}/login"
    try:
        r = requests.post(url, json={"username": username, "password": password}, timeout=5)
        try:
            print("[Server]", r.json())
            return r.json()
        except:
            print("[Server text]", r.text)
            return {"status":"error", "msg":"Invalid server response"}
    except Exception as e:
        print("[Login error]", e)

def submit_info(server_ip, server_port, name, ip, port):
    url = f"http://{server_ip}:{server_port}/submit-info/"
    try:
        r = requests.post(url, json={"name": name, "ip": ip, "port": port}, timeout=5)
        print("[Server]", r.json())
    except Exception as e:
        print("[submit_info error]", e)

def add_list(server_ip, server_port, name, ip, port):
    url = f"http://{server_ip}:{server_port}/add-list/"
    try:
        r = requests.post(url, json={"name": name, "ip": ip, "port": port}, timeout=5)
        print("[Server]", r.json())
    except Exception as e:
        print("[add_list error]", e)

def get_list(server_ip, server_port):
    url = f"http://{server_ip}:{server_port}/get-list/"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        peers = data.get("peers", {})
        global connected_peers
        connected_peers = peers
        print("Peer list:")
        for name, info in peers.items():
            print(f"  - {name}: {info}")
        return peers
    except Exception as e:
        print("[get_list error]", e)
        return {}

def send_peer(target, msg, name):
    """Send a direct message to another peer via TCP socket"""
    target_info = connected_peers.get(target)
    if not target_info:
        print(f"[send_peer error] Target peer '{target}' not found in connected peers.")
        return
    target_ip = target_info.get("ip")
    target_port = target_info.get("port")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((target_ip, target_port))
        full_msg = f"[From {name}]: {msg}"
        s.sendall(full_msg.encode("utf-8"))
        s.close()
        print(f"[Info] Message sent to {target} at {target_ip}:{target_port}")
    except Exception as e:
        print(f"[send_peer error] Could not send message to {target}: {e}")

def broadcast(server_ip, server_port, channel, msg, name):
    url = f"http://{server_ip}:{server_port}/broadcast-peer/"
    try:
        r = requests.post(url, json={"sender": name, "channel": channel, "msg": msg}, timeout=5)
        print("[Server]", r.json())
    except Exception as e:
        print("[broadcast error]", e)



def join_channel_client(server_ip, server_port, peer_name, channel_name):
    """Call server to join channel"""
    url = f"http://{server_ip}:{server_port}/join-channel/"
    try:
        r = requests.post(url, json={"peer": peer_name, "channel": channel_name}, timeout=5)
        data = r.json()
        print("[Server]", data)
    except Exception as e:
        print("[join_channel_client error]", e)


def view_channels_client(server_ip, server_port, peer_name):
    """Call server to view channels the peer has joined"""
    url = f"http://{server_ip}:{server_port}/view-channels/"
    try:
        r = requests.get(url, json={"peer":peer_name}, timeout=5)
        data = r.json()
        print("[Server]", data.get("all_channels"))
    except Exception as e:
        print("[View_channels_client error]", e)
def get_info(server_ip, server_port, peer_name):
    url = f"http://{server_ip}:{server_port}/get-info/"
    try:
        r = requests.post(url, json={"peer": peer_name}, timeout=5)
        print("[Server]", r.json())
        return r.json()
    except Exception as e:
        print("[get_info error]", e)
        return {"Status":"error"}
def register(server_ip, server_port, username, password):
    url = f"http://{server_ip}:{server_port}/register/"
    try:
        r = requests.post(url, json={"username": username, "password": password}, timeout=5)
        print("[Server]", r.json())
        return r.json()
    except Exception as e:
        print("[register error]", e)
def create_channel(server_ip, server_port, channel_name, name):
    url = f"http://{server_ip}:{server_port}/create-channel/"
    try:
        r = requests.post(url, json={"peer_name": name, "channel_name": channel_name}, timeout=5)
        print("[Server]", r.json())
        return r.json()
    except Exception as e:
        print("[create_channel error]", e)


# Warning if server is crashed
def hearthbeat_check(server_ip, server_port):
    url = f"http://{server_ip}:{server_port}/ping"
    fail_count = 0
    while True:
        try:
            r = requests.get(url,timeout=5)
            fail_count = 0
        except:
            fail_count +=1
        if fail_count >=3:
            print("[Warning] Cannot reach server, it may be down!")
            
        time.sleep(0.5)
def main():
    parser = argparse.ArgumentParser(description="Simple Peer Chat client")
    parser.add_argument("--name", required=True, help="peer name (unique)")
    parser.add_argument("--local-ip", default=None, help="local IP to bind (default: auto-detect)")
    parser.add_argument("--port", type=int, default=9001, help="local listening port")
    parser.add_argument("--server-ip", default="127.0.0.1", help="tracker server IP")
    parser.add_argument("--server-port", type=int, default=8001, help="tracker server port")
    args = parser.parse_args()

    name = args.name
    local_ip = args.local_ip if args.local_ip else detect_local_ip()
    local_port = args.port
    server_ip = args.server_ip
    server_port = args.server_port

    # Start listener thread
    listener = threading.Thread(target=listen_peer, args=(local_ip, local_port), daemon=True)
    listener.start()
    time.sleep(0.2)

    hb = threading.Thread(target=hearthbeat_check, args=(server_ip, server_port), daemon=True)
    hb.start()

    # Login loop
    while True:
        username = input("Enter username for login: ").strip()
        password = input("Enter password for login: ").strip()
        account = login(server_ip, server_port, username, password)
        if account.get("status") == "success":
            submit_info(server_ip, server_port, username, local_ip, local_port)
            add_list(server_ip, server_port, username, local_ip, local_port)
            print("You loggin successfully.")
            name = username
            break
        else:
            print("Login failed. Do you want to register a new account? (y/n)")
            choice = input("> ").strip().lower()
            if choice == "y":
                while True:
                    reg_username = input("Enter username for register: ").strip()
                    req_password = input("Enter password for register: ").strip()
                    reg_response = register(server_ip, server_port, reg_username, req_password)
                    if reg_response.get("status") == "ok":
                        print("Registration successful. Please log in again.")
                        break
                    else:
                        print("Registration failed:", reg_response.get("msg"))
            else:
                print("Please try logging in again.")

    # CLI loop
    try:
        while True:
            print("=== MENU ===")
            print("1. List all active peers")
            print("2. Broadcast peer to peer")
            print("3. Direct send (P2P open socket) - connect directly using info from /get-list")
            print("4. View channels users have joined")
            print("5.Join channels")
            print("6. View all channels with their members")
            print("7. Create New Channel")
            print("8. Quit channels")


            choice = input("> ").strip()
            if choice == "1":
                get_list(server_ip, server_port)
                print(connected_peers)

            elif choice == "2":
                channel = input("Enter channel to broadcast: ").strip()
                while True:
                    print(f"Welcome to {channel} channel. Type 'exit' to leave.")
                    msg = input("Broadcast content: ").strip()
                    if msg == "exit":
                        break
                    else:
                        broadcast(server_ip, server_port, channel, msg, name)

                #Send direct message
            elif choice == "3":
                print(connected_peers)
                target = input("Enter your target peer:").strip()
                while True:
                    msg = input("Enter your message:").strip()
                    if msg == "exit":
                        break
                    else:
                        send_peer(target, msg, name)

            elif choice == "4":
                view_channels_client(server_ip, server_port, name)

            elif choice == "5":
                channel_name = input("Enter channel to join: ").strip()
                join_channel_client(server_ip, server_port, name, channel_name)

            elif choice == "6":
                # xem tất cả channels + members
                url = f"http://{server_ip}:{server_port}/view-channels/"
                try:
                    r = requests.get(url,json={"peer":name}, timeout=5)
                    print("[All channels]", r.json().get("all_channels_w_member", {}))
                except:
                    pass

            elif choice == "7":
                channel_name = input("Enter new channel name: ").strip()
                create_channel(server_ip, server_port, channel_name, name)

            elif choice == "8":
                print("exit...")
                break
            else:
                print("Choose a number from 1 to 8.")
    except KeyboardInterrupt:
        print("Interrupted, exiting.")

if __name__ == "__main__":
    main()
