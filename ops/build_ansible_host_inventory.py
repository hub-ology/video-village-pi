import json
import requests
import os
import urlparse


public_id = os.environ.get('NGROK_PUBLIC_ID')
secret_token = os.environ.get('NGROK_SECRET_TOKEN')

tunnels_response = requests.get('https://api.ngrok.com/tunnels', auth=(public_id, secret_token))

if tunnels_response.status_code == 200:
    print('[video_village]')
    tunnels = tunnels_response.json().get('tunnels', [])
    pi_number = 1
    for tunnel in tunnels:
        if tunnel['proto'] == 'tcp':
            public_url = tunnel['public_url']
            host, port = urlparse.urlparse(public_url).netloc.split(':')
            print('pi{} ansible_ssh_port={} ansible_ssh_host={}'.format(pi_number, port, host))
            pi_number += 1
else:
    print(tunnels_response.content)
