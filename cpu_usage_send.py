__author__ = 'adamg'
import socket
import sys
import psutil
import time

server_ip = raw_input("Input server address: ")

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = (server_ip, 9000)

try:

    while True:
        # Send data
        time.sleep(1)
        message = str(psutil.cpu_percent(interval=0.9))
        print sys.stderr, 'sending "%s"' % message
        sent = sock.sendto(message, server_address)

        # Receive response
        print sys.stderr, 'waiting to receive'
        data, server = sock.recvfrom(4096)
        print sys.stderr, 'received "%s"' % data

finally:
    print sys.stderr, 'closing socket'
    sock.close()