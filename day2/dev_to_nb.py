import pynetbox
from nornir import InitNornir

NETBOX_URL = 'http://192.168.20.201:8080/'
TOKEN = 'c6d1b65de45b1e0635ca0bb924240ab073f29795'

nb = pynetbox.api(url=NETBOX_URL, token=TOKEN)

def check_and_create_site():
    try:
        nb.dcim.sites.create(name='CiscoDevNetSite',slug='ciscodevnetsite')
        site_id = nb.dcim.sites.get(slug='ciscodevnetsite').id
    except:
        site_id = nb.dcim.sites.get(slug='ciscodevnetsite').id
    return site_id

def check_and_create_dev_role(role):
    try:
        nb.dcim.device_roles.create(name='CiscoDevNet'+role, slug='ciscodevnet'+role.lower(),color='ff0000')
        dev_role_id = nb.dcim.device_roles.get(slug='ciscodevnet'+role.lower()).id
    except:
        dev_role_id = nb.dcim.device_roles.get(slug='ciscodevnet'+role.lower()).id
    return dev_role_id

def check_and_create_manufacturer():
    try:
        nb.dcim.manufacturers.create(name='CiscoDevNetCisco', slug='ciscodevnetcisco')
        manufacturer_id = nb.dcim.manufacturers.get(slug='ciscodevnetcisco').id
    except:
        manufacturer_id = nb.dcim.manufacturers.get(slug='ciscodevnetcisco').id
    return manufacturer_id

def check_and_create_dev_type(manufacturer_id):
    try:
        nb.dcim.device_types.create(name='CiscoDevNetSwitch', slug='ciscodevnetswitch', model='CiscoDevNetTestSwitch',
                                          height='1',manufacturer=manufacturer_id)
        dev_type_id = nb.dcim.device_types.get(slug='ciscodevnetswitch').id
    except:
        dev_type_id = nb.dcim.device_types.get(slug='ciscodevnetswitch').id
    return dev_type_id

def check_and_create_ip_vrf():
    try:
        nb.ipam.vrfs.create(name='CiscoDevNetVrf')
        vrf_id = nb.ipam.vrfs.get(name='CiscoDevNetVrf').id
    except:
        vrf_id = nb.ipam.vrfs.get(name='CiscoDevNetVrf').id
    return vrf_id

def check_and_create_ip_pref(vrf_id):
    try:
        nb.ipam.prefixes.create(prefix='192.168.1.0/24', vrf=vrf_id)
    except:
        print('Что-то пошло не так!')
if not nb.ipam.vrfs.get(name='CiscoDevNetVrf'):
    vrf_id = check_and_create_ip_vrf()
else:
    vrf_id = nb.ipam.vrfs.get(name='CiscoDevNetVrf').id
if not nb.ipam.prefixes.get(prefix='192.168.1.0/24', vrf_id=vrf_id):
    prefix = check_and_create_ip_pref(vrf_id)
else:
    print('Уже есть префикс!')

manufacturer_id = check_and_create_manufacturer()
dev_type_id = check_and_create_dev_type(manufacturer_id)
access_dev_role_id = check_and_create_dev_role('Access')
core_dev_role_id = check_and_create_dev_role('Core')
site_id = check_and_create_site()

nr = InitNornir(config_file=r"C:\Users\alexa\PycharmProjects\untitled\denvet_day2\inventory\config.yaml")

for i in range(1,254):
    hostname = 'sw'+str(i)
    ip = '192.168.1.'+str(i)+'/24'
    print('Switch: '+hostname,'ip; '+ip)
    if not nb.ipam.ip_addresses.get(address=ip, vrf_id=vrf_id):
        ip_id = nb.ipam.ip_addresses.create(address=ip, vrf=vrf_id).id
    else:
        ip_id = nb.ipam.ip_addresses.get(address=ip, vrf_id=vrf_id).id
    try:
        if not nb.dcim.devices.get(name=hostname,site_id=site_id):
            dev_id = (nb.dcim.devices.create(name=hostname,
                                   device_role=access_dev_role_id,
                                   manufacturer='CiscoDevNetCisco',
                                   device_type=dev_type_id,
                                   site=site_id,
                                   status=0).id)
        else:
            dev_id = nb.dcim.devices.get(name=hostname, site_id=site_id).id
        if not nb.dcim.interfaces.get(device_id=dev_id, name='Loopback0'):
            int_id = nb.dcim.interfaces.create(device=dev_id, name='Loopback0').id
        else:
            int_id = nb.dcim.interfaces.get(device_id=dev_id, name='Loopback0').id

        int_ip = nb.ipam.ip_addresses.get(address=ip, vrf_id=vrf_id)
        int_ip_id = nb.ipam.ip_addresses.get(address=ip, vrf_id=vrf_id).id
        int_ip.interface = {'id': int_id}
        int_ip.save()
        dev = nb.dcim.devices.get(name=hostname,site_id=site_id)
        dev.primary_ip = {'id': ip_id}
        dev.primary_ip4 = {'id': ip_id}
        dev.tags.remove('offline')
        dev.save()
        print(dict(dev))
    except:
        print('Try again by hands!')
