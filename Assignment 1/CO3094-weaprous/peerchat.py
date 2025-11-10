import socket
import threading
import json
import requests
import argparse
import time

#Store channels with their members
channels = {}
existing_channels = {"Channel 1":[], "Channel 2":[], "Channel 3":[]}
customer_channels = []

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
    """Lắng nghe tin nhắn TCP đến từ peer khác (ổn định hơn)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((local_ip, local_port))
    except OSError:
        print(f"[Peer warning] Cannot bind {local_ip}, fallback to 0.0.0.0")
        s.bind(("0.0.0.0", local_port))
    s.listen(5)
    print(f"[Peer] Listening at {local_ip}:{local_port}")

    while True:
        try:
            conn, addr = s.accept()
            # Nhận từng gói và xử lý an toàn
            data = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
            if data:
                text = data.decode("utf-8", errors="ignore").strip()
                print(f"\n📩 [Message from {addr}]: {text}\n> ", end="", flush=True)
            conn.close()
        except Exception as e:
            print(f"[Peer listener error] {e}")


def login(server_ip, server_port, username, password):
    url = f"http://{server_ip}:{server_port}/login"
    try:
        r = requests.post(url, json={"username": username, "password": password}, timeout=5)
        try:
            print("[Server]", r.json())
        except:
            print("[Server text]", r.text)
    except Exception as e:
        print("[Login error]", e)

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
        print("\n📋 Peer list:")
        for name, info in peers.items():
            print(f"  - {name}: {info}")
        return peers
    except Exception as e:
        print("[get_list error]", e)
        return {}

def send_peer(server_ip, server_port, target, msg, name):
    url = f"http://{server_ip}:{server_port}/send-peer/"
    print(url)
    try:
        # r = requests.post(url, json={"target": target, "msg": msg}, timeout=5)
        r = requests.post(url, json={"sender": name, "target": target, "msg": msg}, timeout=5)
        print("[Server]", r.json())
    except Exception as e:
        print("[send_peer error]", e)

def broadcast(server_ip, server_port, channel, msg, name):
    url = f"http://{server_ip}:{server_port}/broadcast-peer/"
    try:
        r = requests.post(url, json={"sender": name, "channel": channel, "msg": msg}, timeout=5)
        print("[Server]", r.json())
    except Exception as e:
        print("[broadcast error]", e)



def join_channel_client(server_ip, server_port, peer_name, channel_name):
    """Gọi server để join channel"""
    url = f"http://{server_ip}:{server_port}/join-channel/"
    try:
        r = requests.post(url, json={"peer": peer_name, "channel": channel_name}, timeout=5)
        data = r.json()
        print("[Server]", data)
    except Exception as e:
        print("[join_channel_client error]", e)


def view_channels_client(server_ip, server_port, peer_name):
    """Gọi server để xem channel peer đã tham gia"""
    url = f"http://{server_ip}:{server_port}/view-channels/"
    try:
        r = requests.get(url, json={"peer":peer_name}, timeout=5)
        data = r.json()
        print("[Server]", data.get("all_channels"))
    except Exception as e:
        print("[View_channels_client error]", e)

def main():
    parser = argparse.ArgumentParser(description="Simple Peer Chat client")
    parser.add_argument("--name", required=True, help="peer name (unique)")
    parser.add_argument("--local-ip", default=None, help="local IP to bind (default: auto-detect)")
    parser.add_argument("--port", type=int, default=9001, help="local listening port")
    parser.add_argument("--server-ip", default="127.0.0.1", help="tracker server IP")
    parser.add_argument("--server-port", type=int, default=8001, help="tracker server port")
    parser.add_argument("--auto-login", action="store_true", help="call /login with admin/account before registering (optional)")
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

    # Optionally login as admin (if server expects)
    if args.auto_login:
        login(server_ip, server_port, "admin", "password")

    # Register this peer in tracker
    add_list(server_ip, server_port, name, local_ip, local_port)

    # CLI loop
    try:
        while True:
            print("\n=== MENU ===")
            print("1. List all active peers")
            print("2. Broadcast peer to peer")
            print("3. Direct send (P2P open socket) - connect directly using info from /get-list")
            print("4. View channels users have joined")
            print("5.Join channels")
            print("6. View all channels with their members")
            print("7. Quit channels")


            choice = input("> ").strip()
            if choice == "1":
                get_list(server_ip, server_port)
            elif choice == "2":
                channel = input("Nhập channel để gửi: ").strip()
                msg = input("Nội dung broadcast: ").strip()
                broadcast(server_ip, server_port, channel, msg, name)
                #Send trực tiếp
            elif choice == "3":
                target = input("Enter your target peer:").strip()
                msg = input("Enter your message:").strip()
                send_peer(server_ip, server_port, target, msg, name)
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
                print("Thoát...")
                break
            else:
                print("Chọn 1,2,3,4 hoặc 0")
    except KeyboardInterrupt:
        print("\nInterrupted, exiting.")

if __name__ == "__main__":
    main()
