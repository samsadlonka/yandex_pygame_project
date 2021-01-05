import socket
from _thread import *
import sys
import pickle

import pygame

server = 'localhost'
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
        self.p1_pos = (100, 100)
        self.p1_angle = 0
        self.p2_pos = (400, 400)
        self.p2_angle = 0

        self.bullets_1 = []
        self.bullets_2 = []


online = Online()
current_player = 1


def threaded_client(conn, player):
    from webContainer import WebContainer

    conn.send(str.encode(str(player)))
    reply = ""
    while True:
        try:
            data = pickle.loads(conn.recv(4096))

            if not data:
                print('Disconnected')
                break
            else:
                if player == 1:
                    online.p1_pos = data.player_pos
                    online.p1_angle = data.player_angle
                    online.bullets_1 = data.bullets
                    reply = WebContainer(player_pos=online.p2_pos, player_angle=online.p2_angle,
                                         bullets=online.bullets_2[:])
                    online.bullets_2.clear()
                else:
                    online.p2_pos = data.player_pos
                    online.p2_angle = data.player_angle
                    online.bullets_2 = data.bullets
                    reply = WebContainer(player_pos=online.p1_pos, player_angle=online.p1_angle,
                                         bullets=online.bullets_1[:])
                    online.bullets_1.clear()

                print('Received:', data)
                print('Sending:', reply)
            conn.sendall(pickle.dumps(reply))
        except:
            break
    print('Lost Connection')
    conn.close()


while True:
    conn, addr = s.accept()
    print('Connected to:', addr)

    start_new_thread(threaded_client, (conn, current_player))
    current_player += 1
