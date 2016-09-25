Deploying a new release to a village of Pis
-------------------------------------------
All commands may be issued from the top level directory of the project.

Be sure ansible and cryptography are installed in your active python environment:

```
pip install ansible cryptography
```

You'll want to set a few environment variables in order to run a deployment:
```
export ANSIBLE_HOST_KEY_CHECKING=False
export NGROK_PUBLIC_ID=<ngrok public id>
export NGROK_SECRET_TOKEN=<ngrok secret token>
```
Note that host key checking is disabled as tunnels may be restarted periodically.
This is OK for our use given we build our hosts inventory from out ngrok
account.

Ensure that your ansible hosts inventory is up-to-date with Pis with active
tunnels:

```
python ops/build_ansible_host_inventory.py > ops/video_village_hosts
```

this will output a proper ansible hosts file to standard output
if the ngrok tunnels API request is successful.  We'll redirect that
output to a video_village_hosts file.  

Now verify that you can connect to all of the Pis in the
video_village_hosts file:

```
ansible -i ops/video_village_hosts --private-key ~/.ssh/vvprivate-mac.ppk all -m ping -u pi --sudo
```
Your value for your private key file may be different.  Replace the private key
path with a value suitable for your set up.

The video_village_update.yml playbook handles the operations necessary to
upgrade Pis to a specific release of the pivideo software.

```
ansible-playbook -i ops/video_village_hosts --private-key ~/.ssh/vvprivate-mac.ppk ops/video_village_update.yml
```
