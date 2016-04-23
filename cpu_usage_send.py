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
SAMPLE_SIZE = 5
INTERVAL = 1

try:

    while True:

        # Get an average CPU usage of SAMPLE_SIZE
        # over time interval INTERVAL
        sum = 0
        for i in range(SAMPLE_SIZE):
            sum += psutil.cpu_percent(interval=INTERVAL)
        cpu_avg = float(sum/SAMPLE_SIZE)

        # Get instance ID with shell 'wget' call
        instance_id = subprocess.check_output(['wget', '-q',
                                               '-O', '-',
                                               'http://instance-data/latest/meta-data/instance-id'])

        # Compose and send CPU usage message to load balancer
        message = instance_id + "|" + socket.gethostname() + "|" + str(cpu_avg)
        print 'sending "%s"' % message
        sent = sock.sendto(message, server_address)

        # Receive response/acknowledgement
        print 'waiting to receive'
        data, server = sock.recvfrom(4096)
        print 'received "%s"' % data

# Disconnects with any ungraceful exit such as CTRL-C
finally:
    # Get instance ID
    instance_id = subprocess.check_output(['wget', '-q',
                                           '-O', '-',
                                           'http://instance-data/latest/meta-data/instance-id'])

    # Compose disconnect message, and disconnect
    message = instance_id + "|" + socket.gethostname() + "|disconnect"
    sock.sendto(message, server_address)
    print sys.stderr, 'closing socket'
    sock.close()