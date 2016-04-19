__author__ = 'adamg'
import socket
import sys
import psutil
import time
import subprocess
server_ip = raw_input("Input server address: ")

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = (server_ip, 9000)

try:

    while True:
        # Send data
        sum = 0
        for i in range(10):
            sum += psutil.cpu_percent(interval=10)
        cpu_avg = float(sum/10)
        instance_id = subprocess.check_output(['wget', '-q',
                                               '-O', '-',
                                               'http://instance-data/latest/meta-data/instance-id'])
        message = instance_id + "|" + socket.gethostname() + "|" + str(cpu_avg)
        print sys.stderr, 'sending "%s"' % message
        sent = sock.sendto(message, server_address)

        # Receive response
        print sys.stderr, 'waiting to receive'
        data, server = sock.recvfrom(4096)
        print sys.stderr, 'received "%s"' % data

finally:
    instance_id = subprocess.check_output(['wget', '-q',
                                           '-O', '-',
                                           'http://instance-data/latest/meta-data/instance-id'])
    message = instance_id + "|" + socket.gethostname() + "|disconnect"
    sock.sendto(message, server_address)
    print sys.stderr, 'closing socket'
    sock.close()