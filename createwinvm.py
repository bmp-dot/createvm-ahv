import json
import requests
import urllib3
import getpass
import base64
from requests.auth import HTTPBasicAuth

#vm variables
local_admin = "Administrator"
admin_password = "NUTANIX"
vcpu = 2
memory = 2048
vlanname ="<Network-Name>"
static_ip = "192.168.200.200"
gateway = "192.168.200.1"
hostname = "W2016"
sourcedisk = "<Image-Name>"

#cluster variables
uri = "https://<PC-IP>:9440/api/nutanix/v3/"
cluster = "<Nutanix-Cluster-Name>"
user = "admin"
password = getpass.getpass(prompt='PC password: ',stream=None)
vmname = "<Name-In-AHV>"
desc = "Created by py script"


#####Do not modify below#####

#Suppress Warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


#Set headers
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}


#Get Subnet UUID
paylod = {}
r = requests.post(uri+"subnets/list", auth = HTTPBasicAuth(user, password), data=json.dumps(paylod), headers=headers, verify=False)
subnet_json = json.loads(r.content)
for subnet in subnet_json['entities']:
    if subnet['status']['cluster_reference']['name'] == cluster and subnet['spec']['name'] == vlanname:
        vlanuuid = subnet['metadata']['uuid']
        
        
#Get disk UUID
paylod = {"length":100}
r = requests.post(uri+"images/list", auth = HTTPBasicAuth(user, password), data=json.dumps(paylod), headers=headers, verify=False)
disk_json = json.loads(r.content)
for disk in disk_json['entities']:
    if disk['status']['name'] == sourcedisk:
        diskuuid = disk['metadata']['uuid']
        

#Read base sysprep
with open('base-sysprep.xml', encoding="utf8") as sysprep_file :
    xml_data = sysprep_file.read()
#Modify base sysprep
    xml_data = xml_data.replace('LOCALADMIN_USER', local_admin)
    xml_data = xml_data.replace('LOCALADMIN_SECRET', admin_password)
    xml_data = xml_data.replace('COMPNAME', hostname)
    xml_data = xml_data.replace('STATICIP', static_ip)
    xml_data = xml_data.replace('GW', gateway)

#Encode sysprep to base64
encoded = base64.b64encode(xml_data.encode('utf8'))
b64sysprep = encoded.decode('utf8')

#Read base JSON spec
with open('vm.json') as json_file:
    json_data = json.load(json_file)
#Modify base JSON payload   
    json_data['spec']['name'] = vmname
    json_data['spec']['description'] = desc
    json_data['spec']['resources']['num_sockets'] = vcpu
    json_data['spec']['resources']['memory_size_mib'] = memory
    json_data['spec']['resources']['nic_list'][0]['subnet_reference']['uuid'] = vlanuuid
    json_data['spec']['resources']['disk_list'][0]['data_source_reference']['uuid'] = diskuuid
    json_data['spec']['resources']['guest_customization']['sysprep']['unattend_xml'] = b64sysprep


#Send paylod to Prism Centeral
response = requests.post(uri+"vms", auth = HTTPBasicAuth(user, password), data=json.dumps(json_data), verify=False, headers=headers)


#print(xml_data)
#print(b64sysprep)
#print(json_data)
print("disk_uuid:", diskuuid)
print("vlan_uuid:", vlanuuid)
print("response_code:", response.status_code)
