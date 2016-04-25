__author__ = 'adamg'
import socket
import sys
import psutil
from threading import Thread
import threading
import subprocess

SAMPLE_SIZE = 7
INTERVAL = 1
ECHO_PORT = 20000


def send_metrics():

    server_ip = '54.85.143.180'

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (server_ip, 9000)
    print 'starting up metrics sending to %s on port %s' % server_address

    try:
        while True:

            # Get an average CPU usage of SAMPLE_SIZE
            # over time interval INTERVAL
            sum = 0
            for i in range(SAMPLE_SIZE):
                sum += psutil.cpu_percent(interval=INTERVAL)
            cpu_avg = float(sum / SAMPLE_SIZE)

            # Get instance ID with shell 'wget' call
            instance_id = subprocess.check_output(['wget', '-q',
                                                   '-O', '-',
                                                   'http://instance-data/latest/meta-data/instance-id'])

            # Compose and send CPU usage message to load balancer
            from urllib2 import urlopen
            my_ip = urlopen('http://ip.42.pl/raw').read()
            message = instance_id + "|" + my_ip + "|" + str(cpu_avg)
            print 'sending "%s"' % message
            sent = sock.sendto(message, server_address)

            # Receive response/acknowledgement
            print 'waiting to receive...'
            data, server = sock.recvfrom(4096)
            if 'shutdown' in data:
                print 'shutting down'
                # Get instance ID
                instance_id = subprocess.check_output(['wget', '-q',
                                                       '-O', '-',
                                                       'http://instance-data/latest/meta-data/instance-id'])

                # Compose disconnect message, and disconnect
                message = instance_id + "|" + urlopen('http://ip.42.pl/raw').read() + "|disconnect"
                sock.sendto(message, server_address)
                subprocess.call(['killall', 'python'])
            else:
                print '\t\treceived acknowledgement\n'

    except:
        print 'SEND_METRICS EXCEPTION'

    # Disconnects with any ungraceful exit such as CTRL-C
    finally:
        print 'Closing socket'
        sock.close()


def run_echo_server():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the port
    server_address = ('0.0.0.0', ECHO_PORT)
    print 'starting up echo server at %s on port %s' % server_address
    sock.bind(server_address)

    # Simple UDP echo server
    try:
        while True:
            print '\nwaiting to receive message'
            data, address = sock.recvfrom(4096)

            print 'received %s bytes from %s' % (len(data), address)
            print data

            if data:
                if "fib=" in data:
                    num = int(data.split('|')[0].split('=')[1])
                    if num < 40:
                        data += ", result: " + str(fibonacci(num)) + " in background process."
                    else:
                        data += "--ERROR: number too large to compute."
                sent = sock.sendto(data, address)
                print 'sent %s bytes back to %s' % (sent, address)
            else:
                sock.sendto("Received empty message", address)
    except:
        print 'ECHO SERVER EXCEPTION'
    finally:
        print 'Disconnecting Echo Server'
        sock.close()
        threading.currentThread().join()

def fibonacci(i):
    if i == 0:
        return 1
    if i == 1:
        return 1
    else:
        return fibonacci(i-2) + fibonacci(i-1)


if __name__ == "__main__":
    usage_sender = Thread(target=send_metrics)
    echo_server = Thread(target=run_echo_server)
    echo_server.start()
    usage_sender.start()
