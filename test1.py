#!/usr/local/bin/python3
# Filename: test.py

import sys
import time
import paramiko


FEDERATION_CHILD_IP = "10.30.170.105"


def spinning_cursor():
    while True:
        for cursor in '|/-\\':
            yield cursor


spinner = spinning_cursor()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ssh_stdin = ssh_stdout = ssh_stderr = None

ssh.connect(FEDERATION_CHILD_IP, username="root", password="rdisfun")

print("Starting Child FMS...")
# Remote execute command to start fms
ssh.exec_command("sudo -u test /home/test/testInstallChildFMS/Foglight/bin/fms -d")
time.sleep(3)
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("grep 'startup complete' /home/test/testInstallChildFMS/Foglight/logs/*")

while "startup complete" not in ssh_stdout.read().decode("utf-8"):
    # Remote grep logs path all files for 'startup complete' string
    sys.stdout.write(next(spinner))
    sys.stdout.flush()
    time.sleep(0.1)
    sys.stdout.write("\b")
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("grep 'startup complete' /home/test/testInstallChildFMS/Foglight/logs/*")

print("Child FMS completed startup.")

ssh.close()
