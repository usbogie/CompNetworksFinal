import boto3
import datetime
import pprint

pp = pprint.PrettyPrinter(indent=2)
ec2 = boto3.resource('ec2')
def get_loads():
        instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
        instanceIDs = [instance.id for instance in instances]
        timedelt = datetime.timedelta(seconds=600)
        client = boto3.client('cloudwatch')
        CPU = {}
        for instanceID in instanceIDs:
                response = client.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName='CPUUtilization',
                        Dimensions=[
                                {
                                'Name': 'InstanceId',
                                'Value': instanceID
                                },
                        ],
                        StartTime=datetime.datetime.now() - timedelt,
                        EndTime=datetime.datetime.now(),
                        Period=60,
                        Statistics=['Average'],
                        Unit='Percent')
                CPU[instanceID] = response['Datapoints'][0]['Average']
        return CPU

def create_new_server():
        instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
        iIDs = [instance.id for instance in instances]
        print type(iIDs[0])
        image = ec2.Image(iIDs[0])
        new_server = ec2.create_instances(ImageId=image)
        new_server.start()

print ec2.images
instanceCPUs = get_loads()
threshhold = 1
create_new_server()
print ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
