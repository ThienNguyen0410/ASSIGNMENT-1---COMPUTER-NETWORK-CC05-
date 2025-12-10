# ASSIGNMENT 1: COMPUTER NETWORK CC05 - 251
This program will include 2 main tasks
- Task 1: HTTP server with cookies sessions
- Task 2: Hybrid chat application (client server & p2p paradigm)

1. **Task 1: HTTP server with cookies session**
To run this task you will follow steps below:
Open 2 terminals:
- Find your computer ip by command

```bash
ipconfig (window)
ifconfig (linux)
```
**Terminal 1: Run Backend**
```bash
python start_backend.py --server-ip your computer ip  --server-port 9000
```

**Terminal 2: Run Proxy**
```bash
python start_proxy.py --server-ip 0.0.0.0 --server-port 8080
```

+ Open incognito site on Google Chrome
+ Visit URL: HTTP:// your computer ip:8080/
-> 404 Unauthorized (Not Cookies Yet)
+ Press "login" to enter username: admin and password: password
-> Login successfully
+ Visit index page
+ Open again URL HTTP://your computer ip:8080/
-> You don't need to login again because Set-Cookies = True has been set
2. **Task 2: Hybrid Chat Application**
This task will implement a chat application which combines two main paradigms: client - server and p2p paradigms.

This task will be implemented in 2 files:

`start_sampleapp.py`: Implement Resful API for chat app.
`peerchat.py`: Implement client site for chat app.

**Use cases for users**

+ Register: Users can register when they didn't have accounts
+ Login: Users can login when they already had accounts
+ View active peers: a peer can view all connected_peers
+ Send direct messages: peers can send messages to another peer
+ Broadcast message: peers can send messages to all memebers in a same channel (group chat)
+ View channels: peers can view all active channels
+ Join channels: a peer can join channels which they want to join
+ Create channels: a peer can create different channels
+ Server warning: peers will be anncounced when server is crashed but they still chat together

**Run program**
The program will be run in `WSL` with the local ip address.

**Terminal 1: Run server (tracker)**
```bash
python3 start_sampleapp.py --server-ip 0.0.0.0 --server-port 8001
```

**Terminal 2: Run clients**
Run 2 clients

```bash
python3 peerchat.py --name peer1 --local-ip 127.0.0.1 --port 9001 --server-ip 127.0.0.1 --server-port 8001
```

```bash
python3 peerchat.py --name peer2 --local-ip 127.0.0.1 --port 9002 --server-ip 127.0.0.1 --server-port 8001
```

After that see the terminals and begin your chat.
**Notes**: 
`requests` library has been used in task 2 so you need to install the library by the command:
```bash
pip3 install requests
```

You need to view channel before sending messages because after viewing channels you will 
know the ip address and port of peers.

