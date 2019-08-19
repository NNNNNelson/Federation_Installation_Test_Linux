#!/usr/local/bin/python3
# Filename: main.py

import os
import sys
import stat
import subprocess
import re
import time
import glob
import psutil
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import paramiko
from modify_file_content_using_re import modify_file_content_using_re
from find_file_and_get_path import find_file_and_get_path

if __name__ == "__main__":
    global FMS_INSTALLER_PATH
    global FMS_PROPERTIES_FILE_PATH
    global FMS_INSTALL_TARGET_PATH
    global FMS_LICENSE_FILE_PATH
    global FEDERATION_ROLE
    global FEDERATION_CHILD_IP
    global CHILD_FMS_INSTALL_TARGET_PATH

    # Print the Hint Information
    print("For Federation test, will use embedded DB.\n"
          "Before test starts, you need to specify:\n"
          "1. FMS installer path\n"
          "2. FMS properties file path\n"
          "3. FMS license file path\n"
          "4. Installation target path\n"
          "5. This FMS run as master or child (if run as master, need to specify the child IP)\n")

    # Get installation information
    FMS_INSTALLER_PATH = input("Specify your FMS installer path: ")
    FMS_PROPERTIES_FILE_PATH = input("Specify your properties file path: ")
    FMS_INSTALL_TARGET_PATH = input("Specify your install target path: ")
    FMS_LICENSE_FILE_PATH = input("Specify your Foglight license path: ")
    FEDERATION_ROLE = input("This FMS will run as Federation master or child?[master/child]: ")
    if FEDERATION_ROLE == "master":
        FEDERATION_CHILD_IP = input("Specify the Federation child IP: ")

    # Print the installation information summary, let user have a check, if agree, continue to start install
    print("Summry:")
    print("Your FMS installer path: %s" % FMS_INSTALLER_PATH)
    print("Your properties path: %s" % FMS_PROPERTIES_FILE_PATH)
    print("Your install target path: %s" % FMS_INSTALL_TARGET_PATH)
    print("Your Foglight license path: %s" % FMS_LICENSE_FILE_PATH)
    print("Your Federation role: %s" % FEDERATION_ROLE)
    if FEDERATION_ROLE == "master":
        print("Your Federation child IP: %s" % FEDERATION_CHILD_IP)
    summayAcceptance = input("Do you agree with the summary? [y/n]")
    if summayAcceptance == "y":
        print("Install starts...")
    else:
        print("Program exists.")
        exit()

    # Check whether installer exists
    print("Checking whether FMS installer file exists...")
    # If file exists, continue to check execution permission. Else, exit the program
    if os.path.exists(FMS_INSTALLER_PATH):
        print("FMS installer file exists.")
        # Check whether current user has execution permission of the installer
        print("Checking wheter user has execution permission to FMS installer file...")
        file_stat = os.stat(FMS_INSTALLER_PATH)
        other_user_executable = (file_stat.st_mode & stat.S_IXOTH) | (file_stat.st_mode & stat.S_IXGRP) | (file_stat.st_mode & stat.S_IXUSR)
        # If no execution permission, set execution permission to other user of this file
        if not other_user_executable:
            print("The FMS installer file has no execution permission, now set other user execution permission to it...")
            os.chmod(FMS_INSTALLER_PATH, file_stat.st_mode | stat.S_IXOTH)
            print("Other user execution permission has been set.")
        else:
            print("The FMS installer file already has execution permission.")
    else:
        print("FMS installer file DOES NOT exist! Please check your FMS isntaller path.")
        print("Program exits.")
        exit()

    # Check if FMS properties file exists
    print("Checking whether FMS properties file exists...")
    # If file exists, continue. Else, exit program
    if os.path.exists(FMS_PROPERTIES_FILE_PATH):
        print("FMS properties file exists.")
    else:
        print("FMS properties file DOES NOT exist! Please check your FMS properties file path.")
        print("Program exits.")
        exit()

    # Check if Foglight license file exists
    print("Checking whether Foglight license file exists...")
    # If file exists, continue. Else, exit program
    if os.path.exists(FMS_LICENSE_FILE_PATH):
        print("Foglight license file exists.")
    else:
        print("Foglight license file DOES NOT exist! Please check your Foglight license file path.")
        print("Program exits.")
        exit()

    # If current FMS is Federation Master, check if Child can be pinged
    if FEDERATION_ROLE == "master":
        print("Checking if child machine can be pinged...")
        ping_child_response = os.system("ping -c 1 " + FEDERATION_CHILD_IP)
        if ping_child_response == 0:
            print("Child machine can be pinged.")
        else:
            print("Child machine CAN NOT be pingged! Please check your child machine IP or check the child machine status.")
            print("Program exits.")
            exit()

    # Modify the FMS properties file to prepare for installation
    # Modify the install target path
    modify_file_content_using_re(FMS_PROPERTIES_FILE_PATH, "^(#)?USER_INSTALL_DIR=.*", "USER_INSTALL_DIR=%s" % FMS_INSTALL_TARGET_PATH)
    # Modify the Foglight license path
    modify_file_content_using_re(FMS_PROPERTIES_FILE_PATH, "^(#)?FMS_LICENSE_FILE=.*", "FMS_LICENSE_FILE=%s" % FMS_LICENSE_FILE_PATH)

    # Check if FMS process is already running, if yes, kill the process
    print("Checking if there's FMS process already running...")
    for proc in psutil.process_iter():
        if "Foglight 5" in proc.name():
            print("Found running FMS, now kill it...")
            proc.kill()
    print("No running FMS process found.")

    # Use silent mode to use FMS properties file to install FMS
    # TODO(nelson.wang@quest.com/nnnnnelson@gmail.com): Check if OS is Windows, use windows command to silent install (When deploy this code to Windows, complete this part of code)
    print("Silent installing FMS...")
    # Reason of using "shell=True": In subprocess.call, if not using "shell=Ture", it will use "shell=False" by default, that, the command is not running in shell, that, command like "cd", "ls" won't work. Here the command includes "sudo" command, so, must use "shell=Ture"
    silent_install_result = subprocess.call("sudo -u test %s -i silent -f %s" % (FMS_INSTALLER_PATH, FMS_PROPERTIES_FILE_PATH), shell=True)
    if silent_install_result == 0:
        print("The FMS has been successfully installed.")
    else:
        print("The FMS installation failed, please have a check.")
        print("Program exit.")
        exit()

    # Modify server.config file to set server.federation variable to TRUE
    # Find the server.config file and get its path
    server_config_file_path = find_file_and_get_path(FMS_INSTALL_TARGET_PATH, "server.config")
    # Set the server.federation variable to TRUE
    modify_file_content_using_re(server_config_file_path, "^server.federation = .*", "server.federation = true;")

    # Modify federation.config file to set FederationURLs list to child IP and port
    federation_config_file_path = find_file_and_get_path(FMS_INSTALL_TARGET_PATH, "federation.config")
    # Add child IP and port to fedecation.config file FederationURLs part
    with open(federation_config_file_path, "r", encoding="utf-8") as f1, open("%s.back" % federation_config_file_path, "w", encoding="utf-8") as f2:
        f2.write(re.sub("^FederationURLs = (.*\n)*?\);", "FederationURLs = (\n    \"rmi://%s:1099\",\n);" % FEDERATION_CHILD_IP, f1.read(), flags=re.MULTILINE))
    os.remove(federation_config_file_path)
    os.rename("%s.back" % federation_config_file_path, federation_config_file_path)

    # Startup FMS
    print("Now FMS starting...")
    subprocess.call("sudo -u test %s/bin/fms -d" % FMS_INSTALL_TARGET_PATH, shell=True)
    # Tested that, after "fms -d" start FMS, the server log appears about 8 seconds later, so, here wait for 10s
    time.sleep(10)

    def check_process_exists(process_identifier):
        process_exists_flag = False
        for proc in psutil.process_iter():
            if proc.name() == process_identifier:
                process_exists_flag = True
        return process_exists_flag

    list_of_server_logs = glob.glob("%s/logs/ManagementServer_2*" % FMS_INSTALL_TARGET_PATH)
    newest_server_log = max(list_of_server_logs, key=os.path.getmtime)

    def spinning_cursor():
        while True:
            for cursor in '|/-\\':
                yield cursor

    spinner = spinning_cursor()
    FMS_startup_complete_flag = False
    while check_process_exists("fms") & (not FMS_startup_complete_flag):
        sys.stdout.write(next(spinner))
        sys.stdout.flush()
        time.sleep(0.1)
        sys.stdout.write("\b")
        with open(newest_server_log, "r", encoding="utf-8") as f1:
            if "startup complete" in f1.read():
                FMS_startup_complete_flag = True
                print("FMS startup completed successfully.")

    # Use selenium and Chromium headless mode to visit Foglight jmx-console, and generate Keystore and certificate files
    print("Visiting Foglight jmx-console to generate Federation needed keystore and cer files...")
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--window-size=1420,1080")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.get("http://localhost:8080/")
    el = driver.find_element_by_id("user")
    el.send_keys("foglight")
    el = driver.find_element_by_id("password")
    el.send_keys("foglight")
    el.submit()
    WebDriverWait(driver, 20, 0.5).until(EC.title_is("Welcome - Foglight"))
    driver.get("http://localhost:8080/jmx-console/")
    locator = (By.XPATH, "//a[text()='service=FederationConfig']")
    WebDriverWait(driver, 20, 0.5).until(EC.presence_of_element_located(locator))
    el = driver.find_element_by_xpath("//a[text()='service=FederationConfig']")
    el.click()
    locator = (By.XPATH, "//input[@operation='generateFederationKeyStores']")
    WebDriverWait(driver, 20, 0.5).until(EC.presence_of_element_located(locator))
    el = driver.find_element_by_xpath("//input[@operation='generateFederationKeyStores']")
    el.click()
    driver.quit()
    print("Federation needed keystore and cer files have been generated.")

    # Modify federation.config file to umcomment "KeyStore" and "KeyStorePwd" lines
    # Find the federation.config file and get its path
    print("Modifying \"federation.config\" file...")
    federation_config_file_path = find_file_and_get_path(FMS_INSTALL_TARGET_PATH, "federation.config")
    # Umcomment "KeyStore" and "KeyStorePwd" lines
    modify_file_content_using_re(federation_config_file_path, "^# (KeyStore = .*)", "\\1")
    modify_file_content_using_re(federation_config_file_path, "^# (KeyStorePwd = .*)", "\\1")
    print("\"federation.config\" file has been modified.")

    # Use paramiko module to send FMS install, FMS properties file, FMS license and federation-child.keystore file to child machine /home/test/Downloads path
    print("Sending files to child machine...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_stdin = ssh_stdout = ssh_stderr = None

    ssh.connect(FEDERATION_CHILD_IP, username="root", password="rdisfun")

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
    print("On Child machine, silent installing FMS...")
    ssh.exec_command("chmod +x %s" % child_fms_insatller_path)
    # On child machine, use FMS properties file to silent install Child FMS
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("sudo -u test %s -i silent -f %s" % (child_fms_insatller_path, child_fms_properties_file_path))
    print(ssh_stdout.read())
    print(ssh_stderr.read())
    print("Child FMS has been installed.")

    # Copy federation-child.keystore file to Child's config path
    print("On Child machien, copying federation-child.keystore file to <Foglight HOME>/config/ path...")
    ssh.exec_command("cp /home/test/Downloads/federation-child.keystore /home/test/testInstallChildFMS/Foglight/config/")
    ssh.exec_command("chown test:test /home/test/testInstallChildFMS/Foglight/config/federation-child.keystore")
    print("Copying federation-child.keystore has been finished.")

    # Modify Child's server.config file
    print("On Child machien, modifying server.config file...")
    ssh.exec_command(r"sed -i -e 's/# \(server.federation.ssl\)/\1/g' /home/test/testInstallChildFMS/Foglight/config/server.config")
    ssh.exec_command(r"sed -i -e 's/# \(server.federation.keystore\)/\1/g' /home/test/testInstallChildFMS/Foglight/config/server.config")
    print("The modification of server.config file has been finished.")

    # Start Child FMS
    print("Starting Child FMS...")
    # Remote execute command to start fms
    ssh.exec_command("sudo -u test /home/test/testInstallChildFMS/Foglight/bin/fms -d")
    ssh_stdout = ""
    while not ssh_stdout:
        # Remote grep logs path all files for 'startup complete' string
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("grep 'startup complete' /home/test/testInstallChildFMS/Foglight/logs/*")
        sys.stdout.write(next(spinner))
        sys.stdout.flush()
        time.sleep(0.1)
        sys.stdout.write("\b")

    print("Child FMS completed startup.")

    ssh.close()
