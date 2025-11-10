# #
# # Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# # All rights reserved.
# # This file is part of the CO3093/CO3094 course,
# # and is released under the "MIT License Agreement". Please see the LICENSE
# # file that should have been included as part of this package.
# #
# # WeApRous release
# #
# # The authors hereby grant to Licensee personal permission to use
# # and modify the Licensed Source Code for the sole purpose of studying
# # while attending the course
# #

# """THIS MODEL DEFINE ALL APIs WHICH ARE NECCESSARY FOR WEAPROUS"""
# """
# start_sampleapp
# ~~~~~~~~~~~~~~~~~

# This module provides a sample RESTful web application using the WeApRous framework.

# It defines basic route handlers and launches a TCP-based backend server to serve
# HTTP requests. The application includes a login endpoint and a greeting endpoint,
# and can be configured via command-line arguments.
# """

# import json
# import socket
# import argparse
# import threading
# from daemon.weaprous import WeApRous

# PORT = 8001  # Default port

# app = WeApRous()
# peers = {}
# account_list = {"admin":"password"}  #List save all account
# channels = {
#     "Channel 1": [],
#     "Channel 2": [],
#     "Channel 3": []
# }

# #=====================API /login==================================
# @app.route('/login', methods=['POST'])
# def login(headers="guest", body="anonymous"):
#     """
#     Handle user login via POST request.

#     This route simulates a login process and prints the provided headers and body
#     to the console.

#     :param headers (str): The request headers or user identifier.
#     :param body (str): The request body or login payload.
#     """
#     print("[Chatapp login:]")
#     try:
#         data = json.loads(body) if body and body!="anonymous" else {}
        
#         username = data.get("username", "")
#         password = data.get("password", "")

#         if username in account_list:
#             if account_list[username] == password:
#                 response = {
#                     "status":"success",
#                     "message":"login successfully",
#                     "user":username + "\n",
                    
#                 }
#                 print (f"{username} login successfully")
#                 return json.dumps(response)
#             else:
#                 return json.dumps({"status":"failed", "message":"login unsuccessfully"}) + "\n"
#     except Exception as e:
#         return json.dumps({"Status":"error" ,"msghahaha": str(e)})
    
# @app.route('/hello', methods=['PUT'])
# def hello(headers, body):
#     """
#     Handle greeting via PUT request.

#     This route prints a greeting message to the console using the provided headers
#     and body.

#     :param headers (str): The request headers or user identifier.
#     :param body (str): The request body or message payload.
#     """
#     print ("[SampleApp] ['PUT'] Hello in {} to {}".format(headers, body))


# #======================================API "/submit-info"==================================
# @app.route('/submit-info/', methods=['POST'])
# def submit_info(headers="", body=""):
#     """
#     Peer gửi thêm thông tin (nickname, status, ...)
#     """
#     try:
#         data = json.loads(body) if body and body!="anonymous" else {}
#         name = data.get("name")
#         info = data.get("info", {})
#         if name not in peers:
#             return {"status": "error", "msg": f"Peer {name} not found"}
#         peers[name]["info"] = info
#         print(f"[Server] Updated info for {name}: {info}")
#         return {"status": "ok", "msg": f"Info updated for {name}"}
#     except Exception as e:
#         return {"status": "error", "msg": str(e)}

# # ========== /add-list/ ==========
# @app.route('/add-list/', methods=['POST'])
# def add_list(headers="", body=""):
#     """
#     Server thêm peer mới vào danh sách tracker
#     """
#     try:
#         data = json.loads(body)
#         name = data.get("name")
#         ip = data.get("ip")
#         port = data.get("port")

#         peers[name] = {"ip": ip, "port": port, "info": {}}
#         print(f"[Server] Added peer {name} at {ip}:{port}")
#         return {"status": "ok", "msg": f"Added peer {name}"}
#     except Exception as e:
#         return {"status": "error", "msg": str(e)}

# # ========== /get-list/ ==========
# @app.route('/get-list/', methods=['GET'])
# def get_list(headers="", body=""):
#     """
#     Peer lấy danh sách các peer hiện có
#     """
#     return {"status": "ok", "peers": peers}

# # ========== /connect-peer/ ==========
# @app.route('/connect-peer/', methods=['POST'])
# def connect_peer(headers="", body=""):
#     """
#     Tạo kết nối TCP trực tiếp giữa các peer
#     """
#     try:
#         data = json.loads(body)
#         target = data.get("target")
#         msg = data.get("msg", "Hello")

#         if target not in peers:
#             return {"status": "error", "msg": f"Peer {target} not found"}

#         ip = peers[target]["ip"]
#         port = int(peers[target]["port"])

#         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         s.connect((ip, port))
#         s.sendall(msg.encode("utf-8"))
#         s.close()

#         print(f"[Server] Connected and sent message to {target}")
#         return {"status": "ok", "msg": f"Sent to {target}"}
#     except Exception as e:
#         return {"status": "error", "msg": str(e)}

# # ========== /broadcast-peer/ ==========
# @app.route('/broadcast-peer/', methods=['POST'])
# def broadcast_peer(headers="", body=""):
#     """
#     Gửi tin nhắn đến tất cả các peer khác (an toàn, có thống kê lỗi/thành công).
#     """
#     try:
#         # ======== PHÂN TÍCH INPUT =========
#         try:
#             data = json.loads(body) if body else {}
#         except Exception:
#             data = {}

#         msg = data.get("msg", "")
#         if not msg:
#             return {"status": "error", "msg": "Empty message"}

#         # ======== CHUẨN BỊ DANH SÁCH PEER =========
#         if not peers:
#             return {"status": "error", "msg": "No peers available"}

#         total = len(peers)
#         success = 0
#         failed = 0

#         print(f"[Server] Starting broadcast to {total} peers...")

#         # ======== GỬI TỪNG PEER TRONG THREAD RIÊNG =========
#         def send_to_peer(name, ip, port, message):
#             """Gửi tin nhắn đến 1 peer (có chống treo và log)."""
#             nonlocal success, failed
#             try:
#                 s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#                 s.settimeout(2.0)  # chống treo khi peer không phản hồi
#                 s.connect((ip, port))
#                 s.sendall(message.encode("utf-8"))
#                 s.close()
#                 print(f"  ✓ Sent to {name} ({ip}:{port})")
#                 success += 1
#             except Exception as e:
#                 print(f"  ✗ Failed to send to {name} ({ip}:{port}): {e}")
#                 failed += 1

#         threads = []

#         # ======== TẠO THREAD CHO TỪNG PEER =========
#         for name, info in peers.items():
#             ip = info.get("ip")
#             port = int(info.get("port", 0))
#             if not ip or not port:
#                 continue

#             t = threading.Thread(target=send_to_peer, args=(name, ip, port, msg))
#             t.daemon = True
#             threads.append(t)
#             t.start()

#         # ======== CHỜ CÁC THREAD HOÀN THÀNH =========
#         for t in threads:
#             t.join(timeout=3.0)

#         print(f"[Server] Broadcast completed. Success: {success}, Failed: {failed}")

#         return {
#             "status": "ok",
#             "msg": f"Broadcast done. Success: {success}, Failed: {failed}",
#             "total_peers": total
#         }

#     except Exception as e:
#         print(f"[Server] Broadcast failed: {e}")
#         return {"status": "error", "msg": str(e)}

# # ========== /send-peer/ ==========
# @app.route('/send-peer/', methods=['POST'])
# def send_peer(headers="", body=""):
#     """
#     Gửi tin nhắn đến một peer cụ thể
#     """
#     try:
#         data = json.loads(body)
#         target = data.get("target")
#         msg = data.get("msg", "")

#         if target not in peers:
#             return {"status": "error", "msg": f"Peer {target} not found"}

#         ip = peers[target]["ip"]
#         port = int(peers[target]["port"])

#         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         s.connect((ip, port))
#         s.sendall(msg.encode("utf-8"))
#         s.close()

#         print(f"[Server] Sent direct message to {target}")
#         return {"status": "ok", "msg": f"Sent message to {target}"}
#     except Exception as e:
#         return {"status": "error", "msg": str(e)}

# if __name__ == "__main__":
#     # Parse command-line arguments to configure server IP and port
#     parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
#     parser.add_argument('--server-ip', default='0.0.0.0')
#     parser.add_argument('--server-port', type=int, default=PORT)
 
#     args = parser.parse_args()
#     ip = args.server_ip
#     port = args.server_port

#     print("*"*60)
#     print("[CHATAPP BEGINS] :")
#     print("Open new terminal and enter your api:")
#     print("*"*60)

#     # Prepare and launch the RESTful application
#     app.prepare_address(ip, port)
#     app.run()








    #9/11/2025 7:12PM
    #
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""THIS MODEL DEFINE ALL APIs WHICH ARE NECCESSARY FOR WEAPROUS"""
"""
start_sampleapp
~~~~~~~~~~~~~~~~~

This module provides a sample RESTful web application using the WeApRous framework.

It defines basic route handlers and launches a TCP-based backend server to serve
HTTP requests. The application includes a login endpoint and a greeting endpoint,
and can be configured via command-line arguments.
"""

import json
import socket
import argparse
import threading
from daemon.weaprous import WeApRous

PORT = 8001  # Default port

app = WeApRous()
peers = {}
account_list = {"admin":"password"}  #List save all account

channels = {
    "Channel 1": [],
    "Channel 2": [],
    "Channel 3": []
}

#=====================API /login==================================
@app.route('/login', methods=['POST'])
def login(headers="guest", body="anonymous"):
    """
    Handle user login via POST request.

    This route simulates a login process and prints the provided headers and body
    to the console.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or login payload.
    """
    print("[Chatapp login:]")
    try:
        data = json.loads(body) if body and body!="anonymous" else {}
        
        username = data.get("username", "")
        password = data.get("password", "")

        if username in account_list:
            if account_list[username] == password:
                response = {
                    "status":"success",
                    "message":"login successfully",
                    "user":username + "\n",
                    
                }
                print (f"{username} login successfully")
                return json.dumps(response)
            else:
                return json.dumps({"status":"failed", "message":"login unsuccessfully"}) + "\n"
    except Exception as e:
        return json.dumps({"Status":"error" ,"msghahaha": str(e)})
    
@app.route('/hello', methods=['PUT'])
def hello(headers, body):
    """
    Handle greeting via PUT request.

    This route prints a greeting message to the console using the provided headers
    and body.

    :param headers (str): The request headers or user identifier.
    :param body (str): The request body or message payload.
    """
    print ("[SampleApp] ['PUT'] Hello in {} to {}".format(headers, body))


#======================================API "/submit-info"==================================
@app.route('/submit-info/', methods=['POST'])
def submit_info(headers="", body=""):
    """
    Peer gửi thêm thông tin (nickname, status, ...)
    """
    try:
        data = json.loads(body) if body and body!="anonymous" else {}
        name = data.get("name")
        info = data.get("info", {})
        if name not in peers:
            return {"status": "error", "msg": f"Peer {name} not found"}
        peers[name]["info"] = info
        print(f"[Server] Updated info for {name}: {info}")
        return {"status": "ok", "msg": f"Info updated for {name}"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

# ========== /add-list/ ==========
@app.route('/add-list/', methods=['POST'])
def add_list(headers="", body=""):
    """
    Server thêm peer mới vào danh sách tracker
    """
    try:
        data = json.loads(body)
        name = data.get("name")
        ip = data.get("ip")
        port = data.get("port")

        peers[name] = {"ip": ip, "port": port, "info": {}}
        print(f"[Server] Added peer {name} at {ip}:{port}")
        return {"status": "ok", "msg": f"Added peer {name}"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

# ========== /get-list/ ==========
@app.route('/get-list/', methods=['GET'])
def get_list(headers="", body=""):
    """
    Peer lấy danh sách các peer hiện có
    """
    return {"status": "ok", "peers": peers}

# ========== /connect-peer/ ==========
@app.route('/connect-peer/', methods=['POST'])
def connect_peer(headers="", body=""):
    """
    Tạo kết nối TCP trực tiếp giữa các peer
    """
    try:
        data = json.loads(body)
        target = data.get("target")
        msg = data.get("msg", "Hello")

        if target not in peers:
            return {"status": "error", "msg": f"Peer {target} not found"}

        ip = peers[target]["ip"]
        port = int(peers[target]["port"])

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        s.sendall(msg.encode("utf-8"))
        s.close()

        print(f"[Server] Connected and sent message to {target}")
        return {"status": "ok", "msg": f"Sent to {target}"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}
# ========== /send-peer/ ==========
@app.route('/send-peer/', methods=['POST'])
def send_peer(headers="", body=""):
    """
    Gửi tin nhắn đến một peer cụ thể — chỉ gửi nếu 2 peer cùng channel.
    body = {"sender": "peer1", "target": "peer2", "msg": "hello"}
    """
    try:
        data = json.loads(body) if body and body != "anonymous" else { }
        sender = data.get("sender")
        target = data.get("target")
        msg = data.get("msg", "")

        if not sender or not target:
            return {"status": "error", "msg": "Missing sender or target"}

        # ===== Kiểm tra xem 2 peer có cùng channel không =====
        sender_channels = [ch for ch, members in channels.items() if sender in members]
        target_channels = [ch for ch, members in channels.items() if target in members]

        # Tìm giao giữa 2 danh sách
        common = set(sender_channels) & set(target_channels)
        if not common:
            print(f"[Server] ❌ {sender} và {target} không cùng channel — không gửi.")
            return {"status": "error", "msg": f"{sender} và {target} không cùng channel"}

        # ===== Nếu cùng channel → gửi =====
        if target not in peers:
            return {"status": "error", "msg": f"Peer {target} not found"}

        ip = peers[target]["ip"]
        port = int(peers[target]["port"])

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        s.sendall(f"[From {sender}] {msg}".encode("utf-8"))
        s.close()

        print(f"[Server] ✅ {sender} gửi tới {target} (channel chung: {', '.join(common)})")
        return {"status": "ok", "msg": f"Sent message to {target}"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}


# ========== /broadcast-peer/ ==========
@app.route('/broadcast-peer/', methods=['POST'])
def broadcast_peer(headers="", body=""):
    try:
        data = json.loads(body) if body else {}
        sender = data.get("sender")
        msg = data.get("msg", "")
        channel = data.get("channel", "")

        if sender not in channels[channel]:
            return {"status": "error", "msg": "Peer not in this channel"}
        if not msg:
            return {"status": "error", "msg": "Empty message"}
        if not channel:
            return {"status": "error", "msg": "No channel specified"}

        # Chỉ gửi đến peer trong cùng channel
        peers_in_channel = channels.get(channel, [])
        if not peers_in_channel:
            return {"status": "error", "msg": f"No peers in {channel}"}

        success = 0
        failed = 0

        def send_to_peer(name):
            nonlocal success, failed
            try:
                info = peers[name]
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2.0)
                s.connect((info["ip"], int(info["port"])))
                s.sendall(msg.encode("utf-8"))
                s.close()
                success += 1
            except:
                failed += 1

        for peer in peers_in_channel:
            if peer == sender:  # không gửi lại cho sender
                continue
            send_to_peer(peer)

        return {"status":"ok", "msg":f"Broadcast done. Success:{success}, Failed:{failed}"}

    except Exception as e:
        return {"status":"error", "msg": str(e)}


# ========== /join-channel/ ==========
@app.route('/join-channel/', methods=['POST'])
def join_channel(headers="", body=""):
    """
    Peer tham gia channel.
    body = {"peer": "peer1", "channel": "Channel 1"}
    """
    try:
        data = json.loads(body) if body else {}
        peer = data.get("peer")
        channel = data.get("channel")

        if not peer or not channel:
            return {"status": "error", "msg": "Missing peer or channel"}

        if channel not in channels:
            return {"status": "error", "msg": f"Channel {channel} does not exist"}

        if peer not in channels[channel]:
            channels[channel].append(peer)

        return {"status": "ok", "msg": f"{peer} joined {channel}", "channels": channels}

    except Exception as e:
        return {"status": "error", "msg": str(e)}

@app.route('/view-channels/', methods=['GET'])
def view_channels(headers="", body=""):
    try:
        data = json.loads(body) if body and body!="anonymous" else {}
        peer = data.get("peer")
        chanels_of_peer = []

        for chan in channels:
            if peer in channels[chan]:
                chanels_of_peer.append(chan)
        return {"Peer" : peer, "all_channels": chanels_of_peer, "all_channels_w_member":channels}
    except Exception as e:
        return {"Status" :"error" , "msg": str(e)}


if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser(prog='Backend', description='', epilog='Beckend daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    print("*"*60)
    print("[CHATAPP BEGINS] :")
    print("Open new terminal and enter your api:")
    print("*"*60)

    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()