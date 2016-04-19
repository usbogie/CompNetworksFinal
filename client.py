__author__ = 'adamg'
import socket
import sys
import psutil
import time
import subprocess
server_ip = raw_input("Input server address: ")

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = (server_ip, 10000)

try:

    while True:
        # Send data
        message = raw_input("input message")
        print sys.stderr, 'sending "%s"' % message
        sent = sock.sendto(message, server_address)

        # Receive response
        print sys.stderr, 'waiting to receive'
        data, server = sock.recvfrom(4096)
        print sys.stderr, 'received "%s"' % data
        message, ip_dst = data.split("|")
        new_address = (str(ip_dst), server_address[1])
        sock.sendto(message, new_address)

finally:
    print sys.stderr, 'closing socket'
    sock.close()