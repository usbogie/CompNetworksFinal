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
        message = raw_input("input message: ")
        print sys.stderr, 'sending "%s"' % message
        sent = sock.sendto(message, server_address)

        # Receive response
        print 'waiting to receive'
        data, server = sock.recvfrom(4096)
        print 'received "%s"' % data
        message, ip_dst, port = data.split("|")
        new_address = (str(ip_dst), int(port))
        sock.sendto(message, new_address)

        print '\nwaiting to receive message'
        data, address = sock.recvfrom(4096)
        print 'received %s from %s' % (data, address)


finally:
    print sys.stderr, 'closing socket'
    sock.close()