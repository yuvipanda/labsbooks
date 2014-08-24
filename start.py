import time
import os
import re
import xml.etree.ElementTree as ET

import paramiko
from forward import forward_tunnel

JSUB_OUTPUT_REGEX = re.compile(r'Your job (\d+) \("(.*)"\) has been submitted')

ssh_config = paramiko.SSHConfig()
ssh_config.parse(open(os.path.expanduser('~/.ssh/config')))
labs_config = ssh_config.lookup('tools-dev.wmflabs.org')

def get_job_host(ssh):
    _, stdout, _ = ssh.exec_command('qstat -xml')
    xml = ET.parse(stdout)
    queues = xml.findall("//job_list[@state='running']/queue_name")
    if queues:
        return queues[0].text.replace('task@', '').strip()
    else:
        return None


def get_primary_ssh():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('tools-dev.wmflabs.org', username=labs_config['user'])
    return ssh


def start_notebook(ssh):
    # Setup the local notebook environment!
    _, out, _ = ssh.exec_command('bash -e /data/project/notebooks/env/setup.bash')
    print out.read()

    # Check if job already exists, if so, reuse!
    host = get_job_host(ssh)
    if host:
        print "Re-using existing kernel"
        return host

    # Start the server!
    _, stdout, _ = ssh.exec_command('jsub -mem 4g /data/project/notebooks/env/start.bash')
    jsub_output = stdout.read()

    job_num, job_name = JSUB_OUTPUT_REGEX.match(jsub_output).groups()

    print job_num, job_name

    # Wait for the job to start before returning
    while True:
        host = get_job_host(ssh)
        if host:
            return host
            break
        else:
            time.sleep(2)

def get_exec_ssh(host):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    proxy = paramiko.ProxyCommand('ssh -e none tools-dev.wmflabs.org exec nc -w 3600 %s 22' % host)
    ssh.connect(
        host,
        username=labs_config['user'],
        key_filename=labs_config['identityfile'],
        sock=proxy
    )
    forward_tunnel(9500, 'localhost', 9000, ssh.get_transport())

ssh = get_primary_ssh()
host = start_notebook(ssh)
get_exec_ssh(host)
ssh.close()

