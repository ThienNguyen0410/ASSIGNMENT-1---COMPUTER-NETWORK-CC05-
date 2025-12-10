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
account_list = {"admin":{"username": "admin", "password": "password"}}  #List save all accounts
logged_in_peers = []  #List save all logged in peers
channels = {
    "Channel 1": [],
    "Channel 2": [],
    "Channel 3": []
}

# Message storage for peer-to-peer chat
# messages_store = {}
# cookies = {} 
# peer_authentication = {} #Store authentication status for each peer
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
        
        username = data.get("username")
        password = data.get("password")
        print(username)
        print(password)
        if username in account_list:
            if account_list[username]["password"] == password:
                response = {
                    "status":"success",
                    "message":"login successfully",
                    "user":username + "\n",
                }
                print (f"{username} login successfully")
                return json.dumps(response)
            else:
                return json.dumps({"status":"failed", "message":"login unsuccessfully"}) + "\n"
        else:
            return json.dumps({"status":"failed", "message":"login unsuccessfully"}) + "\n"
    except Exception as e:
        return json.dumps({"status":"error" ,"message": str(e)})
    
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
        peer_ip = data.get("ip")
        peer_name = data.get("name")
        peer_port = data.get("port")
        print(f"[Server] Received info from: {peer_name} at {peer_ip}:{peer_port}")
        if peer_name not in peers:
            peers[peer_name] = {"ip": peer_ip, "port": peer_port}
        peers[peer_name]["info"] = {"ip": peer_ip, "port": peer_port}
        print(f"[Server] Updated info for: {peer_name}")
        return {"status": "ok", "msg": f"Info updated for {peer_name}"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

# ========== /add-list/ ==========
@app.route('/add-list/', methods=['POST'])
def add_list(headers="", body=""):
    """
    Server thêm peer mới vào danh sách tracker
    """
    try:
        data = json.loads(body) if body and body!="anonymous" else {}
        name = data.get("name")
        ip = data.get("ip")
        port = data.get("port")

        peers[name] = {"ip": ip, "port": port}
        print(f"[Server] Added peer {name} at {ip}:{port}")
        return {"status": "ok", "msg": f"Added peer {name}"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}
    
# ========== /get-list/ ==========
@app.route('/get-list/', methods=['GET'])
def get_list(headers="", body=""):
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
        if target not in peers:
            return {"status": "error", "msg": f"Peer {target} not found"}

        ip = peers[target]["ip"]
        port = int(peers[target]["port"])

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        s.sendall(f"[From {sender}] {msg}".encode("utf-8"))
        s.close()

        print(f"[Server] ✅ {sender} gửi tới {target} )")
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

@app.route('/get-info/', methods=['GET'])
def get_info(headers="", body=""):
    try:
        data = json.loads(body) if body and body !="anonymous" else {}
        peer_name = data.get("peer_name")
        if peer_name not in peers:
            return {"Status": "no", f"{peer_name}" : "Not logged in yet"}
        else:
            return {"Status": "ok", f"{peer_name}" : "Logged in"}
    except Exception as e:
        return {"Status" :"error" , "msg": str(e)}

@app.route('/register/', methods = ['POST'])
def register(headers="", body=""):
    try:
        data = json.loads(body) if body and body !="anonymous" else {}
        username = data.get("username")
        password = data.get("password")
        if username in account_list:
            return {"status": "error", "msg": f"Username {username} already exists"}
        account_list[username] = {"username": username, "password": password}
        print(account_list)
        return {"status": "ok", "msg": f"Registered username {username}"}   
    except Exception as e:
        return {"Status" :"error" , "msg": str(e)}

@app.route('/create-channel/', methods = ['POST'])
def create_channel(headers="", body=""):
    try:
        data = json.loads(body) if body and body !="anonymous" else {}
        channel_name = data.get("channel_name")
        peer_create = data.get("peer_name")
        if channel_name in channels:
            return {"status": "error", "msg": f"Channel {channel_name} already exists"}
        channels[channel_name] = [peer_create]
        return {"status": "ok", "msg": f"Channel {channel_name} created"}
    except Exception as e:
        return {"Status" :"error" , "msg": str(e)}

@app.route('logout/', methods = ['POST'])
def logout(headers="", body=""):
    try:
        data = json.loads(body) if body and body !="anonymous" else {}
        peer_name = data.get("peer_name")
        if peer_name not in peers:
            return {"status": "error", "msg": f"Peer {peer_name} not found"}
        # Remove peer from all channels
        for chan in channels:
            if peer_name in channels[chan]:
                channels[chan].remove(peer_name)
        # Remove peer from peers list
        del peers[peer_name]
        return {"status": "ok", "msg": f"Peer {peer_name} logged out"}
    except Exception as e:
        return {"Status" :"error" , "msg": str(e)}


#Handle server warning
@app.route('/ping', methods=['GET'])
def ping(headers="", body=""):
    """
    Health check endpoint to verify server is running.
    """
    return {"status": "ok", "msg": "pong"}

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
    print(f"Server running at http://{ip}:{port}/")
    print("Open new terminal and enter your api:")
    print("*"*60)

    # Prepare and launch the RESTful application
    app.prepare_address(ip, port)
    app.run()