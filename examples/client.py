import socket

from helixir import Packet, send_packet, receive_packet

sock = socket.create_connection(('127.0.0.1', 1667))
send_packet(sock, Packet('protocol', [], {}))
print(receive_packet(sock))
sock.close()
