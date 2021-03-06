import socket
import boto3
import pprint
import traceback
import sys
import time
import os

from threading import Thread

os.environ['TZ'] = 'CST+06CDT,M4.1.0,M10.5.0'
time.tzset()

LOAD_BALANCE_PORT = 10000
METRICS_PORT = 9000
ECHO_PORT = 20000

live_cpus = {}
instance_IPs = {}
ec2 = boto3.resource('ec2')

pp = pprint.PrettyPrinter(indent=2)


def run_front_end():
    num_of_cpus = len(live_cpus)
    print '\n-------------' + time.strftime('%X %x %Z') + '---------------'
    print 'Number of live CPUs: ' + str(num_of_cpus)
    for IP in live_cpus:
        print '\t--------------------'
        print '\tInstance at IP ' + str(IP) + ':'
        print '\tid:\t\t' + str(instance_IPs[IP])
        print '\tCPU usage:\t' + str(live_cpus[IP])


def update(message):
    instance, IP, new_val = message.split('|')
    # Instance has disconencted
    if "disconnect" in new_val:
        try:
            # remove from instance trackers
            instance = ec2.Instance(instance_IPs[IP])
            instance.stop()
            live_cpus.pop(IP)
            instance_IPs.pop(IP)
            print 'shutdown instance: ' + IP
        except:
            print "instance to remove wasn't present"
            traceback.print_exc()

    # Instance's first message
    elif IP not in live_cpus:
        live_cpus[IP] = (new_val, -1)

    # Update pre-existing information
    else:
        old_val = live_cpus[IP][0]
        live_cpus[IP] = (new_val, old_val)

    instance_IPs[IP] = instance
    run_front_end()


def check_startup():
    need_to_launch = True
    for cpu in live_cpus:
        new_val = float(live_cpus[cpu][0])
        old_val = float(live_cpus[cpu][1])
        if not (new_val > 70 and old_val > 70) or old_val < 0:
            need_to_launch = False
    if need_to_launch:
        try:
            print "Attempting to launch new instance..."
            instances = list(ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}]))
            if instances:
                instance_to_launch = instances[0]
                instance_to_launch.start()
            else:
                print 'All instances running. No further instances to launch.'
        except:
            print "Error launching"
            print traceback.print_exc()


# using this will just shutdown one idle CPU at a time
# upon its next usage transmission
def check_shutdown():
    for ip in live_cpus:
        old_val = float(live_cpus[ip][1])
        new_val = float(live_cpus[ip][0])
        if old_val == new_val and old_val == 0.0:
            return ip


def receive_cpu_usage():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the port
    server_address = ('0.0.0.0', METRICS_PORT)
    print 'Starting up metrics monitor at %s on port %s' % server_address
    sock.bind(server_address)
    try:
        while True:
            data, address = sock.recvfrom(4096)

            # Update the live_cpus and instance_ips information
            # based on incoming message contents
            if data:
                print '\nreceived message: ' + data
                update(data)
                instance, IP, new_val = data.split('|')
                """
                live_cpu_len = len(live_cpus)
                instances = list(ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]))
                instances_len = -1 + len(instances)
                #print live_cpu_len, instances, instances_len
                if live_cpu_len == instances_len:
                    check_startup()
                """
                to_shut_down = check_shutdown()
                if to_shut_down == IP and len(live_cpus) > 1:
                    print 'sending shutdown'
                    sock.sendto('shutdown', address)
                else:
                    sock.sendto(data, address)
    except:
        print 'METRICS SOCKET EXCEPTION'
        traceback.print_exc(file=sys.stdout)
    finally:
        print 'Closing metrics socket...'
        sock.close()

def startup_check_cycle():
    while True:
        time.sleep(45)
        check_startup()

def load_balance():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the port
    server_address = ('0.0.0.0', LOAD_BALANCE_PORT)
    print 'Starting up load balancer at %s on port %s' % server_address
    sock.bind(server_address)
    try:
        while True:
            data, address = sock.recvfrom(4096)
            if data:
                # Finds instance with lowest CPU usage
                ip_dst = min(live_cpus, key=live_cpus.get)

                # Sends client its original message, along with
                # an IP and port number to resend it to
                msg = data + "|" + str(ip_dst) + "|" + str(ECHO_PORT)
                sock.sendto(msg, address)
                print 'sent \"%s\" back to %s' % (msg, address)
    except:
        print 'LOAD BALANCE SOCKET EXCEPTION'
    finally:
        print 'Closing load balancer socket...'
        sock.close()


if __name__ == "__main__":
    usage_monitor = Thread(target=receive_cpu_usage)
    load_balancer = Thread(target=load_balance)
    startup_check = Thread(target=startup_check_cycle)
    usage_monitor.start()
    load_balancer.start()
    startup_check.start()
