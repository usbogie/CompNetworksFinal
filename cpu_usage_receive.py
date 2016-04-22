import socket
import boto3
import pprint
from threading import Thread

live_cpus = {}
instance_IPs = {}

pp = pprint.PrettyPrinter(indent=2)

def update(message):
    instance, tempIP, new_val = message.split('|')
    IP = ".".join(tempIP.split('-')[1:])
    if IP not in live_cpus:
        live_cpus[IP] = (new_val, -1)
    else:
        old_val = live_cpus[IP][0]
        live_cpus[IP] = (new_val,old_val)
    instance_IPs[IP] = instance
    pp.pprint(instance_IPs)
    pp.pprint(live_cpus)

def check_activity():
    ec2 = boto3.resource('ec2')
    need_to_launch = True
    instance_terminated = False
    for cpu in live_cpus:
        old_val = live_cpus[cpu][1]
        new_val = live_cpus[cpu][0]
        if old_val==new_val and old_val==0.0:
            instance = ec2.Instance(instance_IPs[cpu])
            instance.stop()
        if not (new_val>old_val and new_val>50):
            need_to_launch = False
    if need_to_launch:
        instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}])
        instance_to_launch = instances[0]
        instance_to_launch.start()


def receive_cpu_usage():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the port
    server_address = ('0.0.0.0', 9000)
    print 'starting up on %s port %s' % server_address
    sock.bind(server_address)

    while True:
        print '\nwaiting to receive message'
        data, address = sock.recvfrom(4096)

        print 'received %s bytes from %s' % (len(data), address)
        print data
        update(data)

        if data:
            sent = sock.sendto(data, address)
            print 'sent %s bytes back to %s' % (sent, address)


def choose_cpu():
    return min(live_cpus, key=live_cpus.get)


def load_balance():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the port
    server_address = ('0.0.0.0', 10000)
    print 'starting up on %s port %s' % server_address
    sock.bind(server_address)

    while True:
        print '\nwaiting to receive message'
        data, address = sock.recvfrom(4096)

        print 'received %s bytes from %s' % (len(data), address)
        print data

        if data:
            ip_dst = choose_cpu()
            msg = data + "|" + str(ip_dst) + "|20000"
            sock.sendto(msg, address)
            print 'sent %s back to %s' % (msg, address)


usage_monitor = Thread(target=receive_cpu_usage)
load_balancer = Thread(target=load_balance)
usage_monitor.start()
load_balancer.start()
