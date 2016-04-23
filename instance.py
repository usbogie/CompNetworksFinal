__author__ = 'adamg'
import socket
import sys
import psutil
import subprocess
from threading import Thread

SAMPLE_SIZE = 5
INTERVAL = 1
ECHO_PORT = 20000

def send_metrics():
    server_ip = raw_input("Input server address: ")

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (server_ip, 9000)

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
    except:
        print 'SEND_METRICS EXCEPTION'

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


def run_echo_server():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the port
    server_address = ('0.0.0.0', ECHO_PORT)
    print 'starting up on %s port %s' % server_address
    sock.bind(server_address)

    # Simple UDP echo server
    try:
        while True:
            print '\nwaiting to receive message'
            data, address = sock.recvfrom(4096)

            print 'received %s bytes from %s' % (len(data), address)
            print data

            if data:
                sent = sock.sendto(data, address)
                print 'sent %s bytes back to %s' % (sent, address)
    except:
        print 'ECHO SERVER EXCEPTION'
    finally:
        print 'Disconnecting Echo Server'
        sock.close()

if __name__ == "__main__":
    usage_sender = Thread(target=send_metrics)
    echo_server = Thread(target=run_echo_server)
    usage_sender.start()
    echo_server.start()
