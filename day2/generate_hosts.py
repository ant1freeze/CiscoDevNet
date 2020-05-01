import os

path = r"C:\Users\alexa\PycharmProjects\untitled\denvet_day2\inventory"
file = 'hosts.yaml'
print(os.listdir(path))
if 'hosts.yaml' in os.listdir(path):
    os.remove(os.path.join(path,file))
for i in range(1,254):
    dev = 'sw' + str(i) + ':\n    hostname: 192.168.1.' + str(i) + '\n    groups:\n        - switch\n'
    print(dev)

    with open(os.path.join(path, file), 'a') as yaml:
        yaml.write(dev + '\n')
