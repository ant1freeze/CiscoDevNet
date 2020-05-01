#Imports
from netmiko import ConnectHandler
import csv
import logging
import datetime
import multiprocessing as mp
import textfsm
import re
import sys
import os

DEVICE_FILE_PATH = 'dev_list' # file should contain a list of devices in format: ip,username,password,device_type
BACKUP_DIR_PATH = r'C:\Users\alexa\PycharmProjects\untitled\devnetcisco\backups' # complete path to backup directory

with open(r'C:\Users\alexa\ntc-templates\templates\cisco_ios_show_cdp_neighbors.textfsm') as template:
    fsm = textfsm.TextFSM(template)

def enable_logging():
    logging.basicConfig(filename='test.log', level=logging.DEBUG)
    logger = logging.getLogger("netmiko")

def get_devices_from_file(device_file):
    device_list = list()

    with open(device_file, 'r') as f:
        reader = csv.DictReader(f, delimiter=';')

        for row in reader:
            device_list.append(row)

    print ("Got the device list from inventory")
    print('-*-' * 10)
    print ()

    return device_list

def get_current_date_and_time():
    now = datetime.datetime.now()

    print("Got a timestamp")
    print('-*-' * 10)
    print()

    return now.strftime("%Y_%m_%d-%H_%M_%S")

def connect_to_device(device):

    connection = ConnectHandler(
        host = device['ip'],
        username = device['username'],
        password=device['password'],
        device_type=device['device_type'],
        secret=device['secret']
    )

    print ('Opened connection to '+device['ip'])
    print('-*-' * 10)
    print()

    return connection

def disconnect_from_device(connection, hostname):

    connection.disconnect()

def get_backup_file_path(hostname,timestamp):
    if not os.path.exists(os.path.join(BACKUP_DIR_PATH, hostname)):
        os.mkdir(os.path.join(BACKUP_DIR_PATH, hostname))

    backup_file_path = os.path.join(BACKUP_DIR_PATH, hostname, '{}-{}.txt'.format(hostname, timestamp))
    print('Backup file path will be '+backup_file_path)
    print('-*-' * 10)
    print()

    return backup_file_path

def create_backup(connection, backup_file_path, hostname):

    try:
        output = connection.send_command('sh run')

        with open(backup_file_path, 'w') as file:
            file.write(output)
        print("Backup of " + hostname + " is complete!")
        print('-*-' * 10)
        print()

        return True

    except:
        print('Error! Unable to backup device ' + hostname)
        return False

def check_cdp(connection):
    try:
        output = connection.send_command('sh cdp')
        if 'CDP is not enabled' in output.splitlines()[0]:
            result = 'OFF'
        else:
            result = 'ON'
        return result

    except:
        print('Error! Can not get status of CDP!')

def get_count_cdp_neighbors(connection):
    output = connection.send_command('sh cdp neighbors')
    result_textfsm = fsm.ParseText(output)
    return len(result_textfsm)

def get_dev_ver(connection):
    output = connection.send_command('sh ver')
    sh_ver_strings = output.splitlines()
    for i in range(0, len(sh_ver_strings)):
        if 'System image file is' in sh_ver_strings[i]:
            sys_img = re.findall(r'"(.*?)"',sh_ver_strings[i])[0]
            break
    return sys_img

def get_model_num(connection):
    output = connection.send_command('show inventory raw')
    sh_ver_strings = output.splitlines()
    for i in range(0, len(sh_ver_strings)):
        if 'PID' in sh_ver_strings[i]:
            model_num = sh_ver_strings[i].split(',')[0].lstrip('PID:').strip()
            break
    return model_num

def get_ntp_status(connection):
    output = connection.send_command('sh ntp status')
    if 'Clock is synchronized' in output:
        ntp_status = 'sync'
    else:
        ntp_status = 'not sync'
    return ntp_status

def process_target(device, timestamp):
    connection = connect_to_device(device)

    backup_file_path = get_backup_file_path(device['hostname'], timestamp)
    backup_result = create_backup(connection, backup_file_path, device['hostname'])
    cdp_status = check_cdp(connection)
    count_cdp_neighbors = get_count_cdp_neighbors(connection)
    sys_img = get_dev_ver(connection).split('flash:')[1].lstrip('/')
    ntp_status = get_ntp_status(connection)
    model_num = get_model_num(connection)
    if 'npe' in sys_img:
       pe_npe = 'NPE'
    else:
       pe_npe = 'PE'

    disconnect_from_device(connection, device['hostname'])

    print(device['hostname']+'|'+model_num+'|'+sys_img+'|'+pe_npe+'|CDP is '+cdp_status+', '+str(count_cdp_neighbors)+' peers|Clock in '+ntp_status)

def main(*args):
    enable_logging()

    timestamp = get_current_date_and_time()

    device_list = get_devices_from_file(DEVICE_FILE_PATH)

    processes=list()

    with mp.Pool(4) as pool:
        for device in device_list:
            processes.append(pool.apply_async(process_target, args=(device,timestamp)))
        for process in processes:
            process.get()

if __name__ == '__main__':
    _, *script_args = sys.argv

    main(*script_args)
