import os

from re import sub, finditer, MULTILINE


def snake_case(s):
  return '_'.join(
    sub('([A-Z][a-z]+)', r' \1',
    sub('([A-Z]+)', r' \1',
    s.replace('-', ' '))).split()).lower()


def port_parser(config_str):
    regex = r"(AllowedIPs = )([^\/]*)"
    matches = finditer(regex, config_str, MULTILINE)
    port_max = -1
    port = '0.0'

    for matchNum, match in enumerate(matches, start=1):
        port = match.group(2)
        port_max = max(port_max, int(port[-1]))

    port = list(port)
    port[-1] = str(port_max+1)
    port = ''.join(port)
    return port


paths = {
    'config': '/etc/wireguard/wg0.conf',
    'keys': '/etc/wireguard/keys/',
    'user_configs': '/etc/wireguard/configs/'
}


def generate_keys(name):
    name = snake_case(name)
    pub = os.popen(f'wg genkey | tee {paths["keys"]}{name}_privatekey | wg pubkey | tee {paths["keys"]}{name}_publickey').read()
    priv = os.popen(f'cat {paths["keys"]}{name}_privatekey').read()
    return pub[:-2], priv[:-2]


name = input('user name: ')
pub, priv = generate_keys(name)

keys = {
    'user_private': priv,
    'user_public': pub,
    'server_public': os.environ.get('WG_PUBLIC'),
    'server_private': os.environ.get('WG_PRIVATE'),
    'server_ip': os.environ.get('SERVER_IP')
}

print(os.environ.get('WG_PUBLIC'), os.environ.get('SERVER_IP'))
input()

config_section = 'config section'
section_pos = 0
print(priv, pub)


def generate_config(port):
    server_ip = 1
    config = f'''[Interface]
PrivateKey = {keys['user_private']}
Address = {port}/32
DNS = 8.8.8.8

[Peer]
PublicKey = {keys['server_public']}
Endpoint = {keys['server_ip']}:51830
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 20
'''
    return config


def add_config(name, port):
    name = snake_case(name)

    config = f'''
\n
# config: {name}
[Peer]
PublicKey = {keys['user_public']}
AllowedIPs = {port}/32
# end config\n'''
    return config


with open(paths['config'], 'r') as f:
    lines = f.readlines()
    for line in lines:
        section_pos += 1
        if config_section in line:
            break


with open(paths['config'], 'w') as f:
    port = port_parser(''.join(lines))
    new_config = add_config(name, port)
    lines.insert(section_pos, new_config)
    f.writelines("".join(lines))


with open(f'{paths["user_configs"]}{snake_case(name)}.conf', 'w') as f:
    f.writelines(generate_config(port))

os.system(f'qrencode -t ansiutf8 < {paths["user_configs"]}{snake_case(name)}.conf')

