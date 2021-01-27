import yaml
import os
with open("icap-servers.yaml", 'r') as yamlFile:
    data = yaml.safe_load(yamlFile)

# Get target value
target = data.get("all.icap.glasswall-icap.com")
names = []
ips = []
port = []
for server in target:
    names.append(server.get('name'))
    ips.append(server.get('ip'))
    port.append(server.get('port'))

servers = []
for x, y, z in zip(names, ips, port):
    servers.append("  server " + x + " " + y + ":" + str(z) + " check")
servers = "\n".join(servers)
template_file = open("haproxy.tmp", "r")
content = template_file.readlines()
template_file.close()
content.insert(45, servers)
generated_file = open("/etc/haproxy/haproxy.cfg", "w")
content = "".join(content)
generated_file.write(content)
generated_file.close()
os.system("sudo /etc/init.d/haproxy reload")
os.system("sudo /etc/init.d/haproxy status | head -11")