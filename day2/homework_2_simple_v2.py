from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.tasks.networking import tcp_ping
import re
import sys

with open('input_mac','r') as f:
    input_mac = f.read().strip()
if re.match(r'([0-9a-fA-F]{2}([:-]|$)){6}$|([0-9a-fA-F]{4}([.]|$)){3}|([0-9a-fA-F]){12}$',input_mac):
    print("We need to find this mac address: "+input_mac)
else:
    print('MAC is incorrect! Please check it!')
    sys.exit()

nr = InitNornir(config_file=r"C:\Users\alexa\PycharmProjects\untitled\denvet_day2\inventory\config.yaml")
alive_hosts= []
int_dict ={}
flag = False

print('='*10,'Scan network by icmp. Ping devices in network 192.168.1.0/24...',sep='\n')

ping_res = nr.run(task=tcp_ping, ports = 23) #command_string="show ver")
count = 0
count_all = 0
for host, r in ping_res.items():
    r.host['marked'] = False
    count_all+=1
    if ping_res[host][0].result[23]:
        r.host['marked'] = True
        count+=1

print('='*10,'We have '+str(count)+' alive hosts from '+str(count_all)+'.',sep='\n')

filtered = nr.filter(marked=True)

print('='*10,'Get mac address table from all alive hosts...',sep='\n')

mac_tables = filtered.run(task=netmiko_send_command, command_string='sh mac address-table',use_textfsm=True)

print('='*10,'Get interfaces switchport table from all alive hosts...',sep='\n')

int_sws = filtered.run(task=netmiko_send_command, command_string='sh int sw',use_textfsm=True)

print('='*10,'Remove all trunk ports and make dict - SWITCH:[PORT1,PORT2,...]',sep='\n')

for host, int_sw in int_sws.items():
    int_dict[host] = []
    for int in int_sw[0].result:
        if int['admin_mode'] == 'static access':
            int_dict[host].append(int['interface'])
print('='*10,'Find input mac on access ports and return HOST and dict - MAC',sep='\n')

for host, mac_table in mac_tables.items():
    for mac in mac_table[0].result:
        if mac['destination_address'] == input_mac and mac['destination_port'] in int_dict[host]:
            flag = True
            true_host = host
            true_mac = mac

if flag:
    print('='*10,'Get ip addres of HOST...',sep='\n')
    true_hostname = nr.filter(name=true_host).inventory.hosts[true_host].hostname
    print('='*10,'MAC {} was found at switch {} ({}) on port {} in vlan {}'.format(input_mac,true_host,true_hostname,true_mac['destination_port'],true_mac['vlan']),sep='\n')
if not flag:
    print('='*10,"MAC wasn't found!",sep='\n')

