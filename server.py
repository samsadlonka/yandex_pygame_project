import socket
from _thread import *
import sys
import pickle

from const import SERVER_IP

server = SERVER_IP
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    print(str(e))

s.listen(2)
print('Waiting for connection, Server Started')


class Online:
    def __init__(self):
        self.p1_pos = (-500, -500)
        self.p1_angle = 0
        self.p2_pos = (-500, -500)
        self.p2_angle = 0

        self.bullets_1 = []
        self.bullets_2 = []

        self.score = [0, 0]  # для 0 и 1 игрока соответсвенно

        self.level = None


online = Online()
current_player = 0


def threaded_client(conn, player):
    from webContainer import WebContainer
    global current_player

    conn.send(str.encode(str(player)))

    if player == 0:
        online.level = conn.recv(4096).decode()
    elif player == 1:
        conn.send(str.encode(str(online.level)))

    reply = ""
    while True:
        try:
            data = pickle.loads(conn.recv(4096))

            if not data:
                print('Disconnected')
                break
            else:
                if player == 0:
                    online.p1_pos = data.player_pos
                    online.p1_angle = data.player_angle
                    online.bullets_1 = data.bullets
                    online.score[1] = data.k_death
                    reply = WebContainer(player_pos=online.p2_pos, player_angle=online.p2_angle,
                                         bullets=online.bullets_2[:], score=online.score[0])
                    online.bullets_2.clear()
                else:
                    online.p2_pos = data.player_pos
                    online.p2_angle = data.player_angle
                    online.bullets_2 = data.bullets
                    online.score[0] = data.k_death
                    reply = WebContainer(player_pos=online.p1_pos, player_angle=online.p1_angle,
                                         bullets=online.bullets_1[:], score=online.score[1])
                    online.bullets_1.clear()

                print('Received:', data)
                print('Sending:', reply)
            conn.sendall(pickle.dumps(reply))
        except:
            break
    print('Lost Connection')
    conn.close()
    current_player -= 1
    online.level = None


while True:
    conn, addr = s.accept()
    print('Connected to:', addr)

    start_new_thread(threaded_client, (conn, current_player))
    current_player += 1
