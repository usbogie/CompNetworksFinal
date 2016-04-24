import socket
import boto3
import pprint
from threading import Thread

LOAD_BALANCE_PORT = 10000
METRICS_PORT = 9000
ECHO_PORT = 20000

live_cpus = {}
instance_IPs = {}

pp = pprint.PrettyPrinter(indent=2)


def run_front_end():
    num_of_cpus = len(live_cpus)
    print '\n--------------------------'
    print 'Number of live CPUs: ' + str(num_of_cpus)
    for IP in live_cpus:
        print '\t-----'
        print '\tInstance at IP ' + str(IP) + ':'
        print '\tid:\t\t' + str(instance_IPs[IP])
        print '\tCPU usage:\t' + str(live_cpus[IP])


def update(message):
    instance, tempIP, new_val = message.split('|')
    IP = ".".join(tempIP.split('-')[1:])

    # Instance has disconencted
    if "disconnect" in new_val:
        try:
            # remove from instance trackers
            live_cpus.pop(IP)
            instance_IPs.pop(IP)
        except:
            print "instance to remove wasn't present"

    # Instance's first message
    elif IP not in live_cpus:
        live_cpus[IP] = (new_val, -1)

    # Update pre-existing information
    else:
        old_val = live_cpus[IP][0]
        live_cpus[IP] = (new_val,old_val)

    instance_IPs[IP] = instance
    run_front_end()



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

#TODO maybe split ^method and this method into two?
# using this will just shutdown one idle CPU at a time
# upon its next usage transmission
def check_shutdown():
    for ip in live_cpus:
        old_val = float(live_cpus[ip][1])
        new_val = float(live_cpus[ip][0])
        if old_val==new_val and old_val==0.0:
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
                update(data)
                instance, tempIP, new_val = data.split('|')
                to_shut_down = check_shutdown()
                if to_shut_down == ".".join(tempIP.split('-')[1:]):
                    print 'sending shutdown'
                    sock.sendto('shutdown', address)
                else:
                    sock.sendto(data, address)
    except:
        print 'METRICS SOCKET EXCEPTION'
    finally:
        print 'Closing metrics socket...'
        sock.close()

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
    usage_monitor.start()
    load_balancer.start()



