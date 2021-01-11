import socket
import pickle

from webContainer import WebContainer


class Network:
    def __init__(self, client_ip):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = client_ip
        self.port = 5555
        self.addr = (self.host, self.port)
        self.p = self.connect()

    def getP(self):
        return self.p

    def connect(self):
        self.client.connect(self.addr)
        return int(self.client.recv(4096).decode())

    def send(self, player_pos, player_angle, bullets, k_death):
        try:
            data = WebContainer(player_pos=player_pos, player_angle=player_angle, bullets=bullets, k_death=k_death)
            self.client.send(pickle.dumps(data))
            data = pickle.loads(self.client.recv(4096))
            return data.player_pos, data.player_angle, data.bullets, data.score
        except socket.error as e:
            print(e)

    def set_level(self, level):
        self.client.send(str.encode(str(level), encoding='utf-8'))

    def get_level(self):
        return self.client.recv(4096).decode()
