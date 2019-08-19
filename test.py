#!/usr/local/bin/python3
# Filename: test.py

import subprocess
import paramiko
from modify_file_content_using_re import modify_file_content_using_re


FEDERATION_CHILD_IP = "10.30.170.105"
FMS_INSTALL_TARGET_PATH = "/home/test/testInstallFMS/Foglight"
FMS_INSTALLER_PATH = "/home/test/pythonScripts/Downloads/ACE3_703/Foglight-5_9_3-install_linux-x86_64.bin"
FMS_LICENSE_FILE_PATH = "/home/test/pythonScripts/Downloads/ACE3_703/Foglight.license"
FMS_PROPERTIES_FILE_PATH = "/home/test/pythonScripts/Downloads/ACE3_703/fms_silent_install.properties"

# Use paramiko module to send FMS install, FMS properties file and federation-child.keystore file to child machine /home/test/ path
print("Sending files to child machine...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ssh_stdin = ssh_stdout = ssh_stderr = None

ssh.connect(FEDERATION_CHILD_IP, username="test", password="rdisfun")

sftp = ssh.open_sftp()
# Send "federation-child.keystore" to child
print("Sending \"federation-child.keystore\" file to Federation child machine...")
sftp.put("%s/config/federation-child.keystore" % FMS_INSTALL_TARGET_PATH, "/home/test/Downloads/federation-child.keystore")
print("\"federation-child.keystore\" file has been sent to Federation child machine.")
# Send FMS installer to Federation child machine
print("Sending FMS installer to Federation child machine...")
fms_installer_filename = FMS_INSTALLER_PATH[FMS_INSTALLER_PATH.rfind("/")+1:]
child_fms_insatller_path = "/home/test/Downloads/" + fms_installer_filename
sftp.put(FMS_INSTALLER_PATH, child_fms_insatller_path)
print("FMS installer has been sent to Federation child machine.")
# Send Foglight license to Federation child machine
print("Sending Foglight license to Federation child machine...")
fms_license_filename = FMS_LICENSE_FILE_PATH[FMS_LICENSE_FILE_PATH.rfind("/")+1:]
sftp.put(FMS_LICENSE_FILE_PATH, "/home/test/Downloads/%s" % fms_license_filename)
print("Foglight license has been sent to Federation child machine.")
# Modify FMS properties file to prepare to send to Federation child
print("Duplicate a FMS properties file for child.")
# Get the original FMS properties file directory
fms_properties_file_directory = FMS_PROPERTIES_FILE_PATH[:FMS_PROPERTIES_FILE_PATH.rfind("/")] + "/"
fms_child_properties_file_path = fms_properties_file_directory + "fms_silent_install_for_federation_child.properties"
# Duplicate the FMS properties file for Federation child
subprocess.call("cp %s %s" % (FMS_PROPERTIES_FILE_PATH, fms_child_properties_file_path), shell=True)
child_fms_properties_file_path = "/home/test/Downloads/fms_silent_install_for_federation_child.properties"
# Modify the child FMS properties file
print("Modifying child FMS properties file...")
modify_file_content_using_re(fms_child_properties_file_path, "^(#)?USER_INSTALL_DIR=.*", "USER_INSTALL_DIR=/home/test/testInstallChildFMS/Foglight")
modify_file_content_using_re(fms_child_properties_file_path, "^(#)?FMS_LICENSE_FILE=.*", "FMS_LICENSE_FILE=/home/test/Downloads/Foglight.license")
print("Child FMS properties file has been modified.")
# Send child FMS properties file to Federation child machine
print("Sending child FMS properties file to Federation child machine...")
fms_child_properties_filename = fms_child_properties_file_path[fms_child_properties_file_path.rfind("/")+1:]
sftp.put(fms_child_properties_file_path, "/home/test/Downloads/%s" % fms_child_properties_filename)
print("Child FMS properties file has been sent to Federation child machine.")

sftp.close()

# On child machine, give FMS installer execution permission
print("On child machine, give FMS installer execution permission.")
ssh.exec_command("chmod +x %s" % child_fms_insatller_path)
# On child machine, use FMS properties file to silent install Child FMS
print("On child machine, installing FMS...")
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("sudo -u test %s -i silent -f %s" % (child_fms_insatller_path, child_fms_properties_file_path))
print(ssh_stdout.read())
print(ssh_stderr.read())

ssh.close()
