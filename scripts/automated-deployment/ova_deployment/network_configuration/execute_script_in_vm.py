from __future__ import with_statement
import os
import atexit
import re
import time
from ..tools import cli
from pyVim import connect
from pyVmomi import vim, vmodl

from .get_vm_info import GetVMInfo

from k8_vmware.vsphere.VM_Keystroke import VM_Keystroke
from k8_vmware.vsphere.VM_Screenshot import VM_Screenshot


def get_args():
    """Get command line args from the user.
    """

    parser = cli.build_arg_parser()

    parser.add_argument('-v', '--vm_uuid',
                        required=False,
                        action='store',
                        help='Virtual machine uuid')

    parser.add_argument('-r', '--vm_user',
                        required=False,
                        action='store',
                        help='virtual machine user name')

    parser.add_argument('-w', '--vm_pwd',
                        required=False,
                        action='store',
                        help='virtual machine password')

    parser.add_argument('-l', '--path_to_program',
                        required=False,
                        action='store',
                        help='Path inside VM to the program')

    parser.add_argument('-f', '--program_arguments',
                        required=False,
                        action='store',
                        help='Program command line options')

    args = parser.parse_args()

    cli.prompt_for_password(args)
    return args


def get_instance_uuid():
    vm_info_data = GetVMInfo().main()
    print(vm_info_data)
    inst_uuid = vm_info_data.get("instance_uuid")
    return inst_uuid


def main():
    """
    Simple command-line program for executing a process in the VM without the
    network requirement to actually access it.
    """

    args = get_args()
    instance_uuid = get_instance_uuid()
    try:
        # if args.disable_ssl_verification:
        service_instance = connect.SmartConnectNoSSL(host=args.host,
                                                        user=args.user,
                                                        pwd=args.password,
                                                        port=int(args.port))
        # else:
        #     service_instance = connect.SmartConnect(host=args.host,
        #                                             user=args.user,
        #                                             pwd=args.password,
        #                                             port=int(args.port))

        atexit.register(connect.Disconnect, service_instance)
        content = service_instance.RetrieveContent()

        # if instanceUuid is false it will search for VM BIOS UUID instead
        vm = content.searchIndex.FindByUuid(datacenter=None,
                                            uuid=instance_uuid,
                                            vmSearch=True,
                                            instanceUuid=True)

        if not vm:
            raise SystemExit("Unable to locate the virtual machine.")

        tools_status = vm.guest.toolsStatus
        if (tools_status == 'toolsNotInstalled' or
                tools_status == 'toolsNotRunning'):
            raise SystemExit(
                "VMwareTools is either not running or not installed. "
                "Rerun the script after verifying that VMwareTools "
                "is running")

        creds = vim.vm.guest.NamePasswordAuthentication(
            username=args.vm_user, password=args.vm_pwd
        )

        try:
            # initialize process manager
            pm = content.guestOperationsManager.processManager
            
            # getting ready to send the command through keystroke interaction
            ks_inst = VM_Keystroke(vm)

            # construct command
            vm_ip = os.environ.get("VM_IP")
            vm_gateway = os.environ.get("VM_GATEWAY")
            vm_dns = os.environ.get("VM_DNS")
            vm_sudo_pwd = os.environ.get("VM_SUDO_PASSWORD")

            # convert the bash file from dos to unix
            # ks_inst.send_text("sed -i 's/\r$//' /home/glasswall/network.sh")
            command = "/usr/bin/sudo /usr/bin/bash /home/glasswall/network.sh %s %s %s" % (vm_ip, vm_gateway, vm_dns)
            res = ks_inst.send_text(command).enter().send_text(vm_sudo_pwd).enter()

            # ks_inst.send_text("/usr/bin/sudo /usr/bin/bash /home/glasswall/network.sh 2.2.2.2 3.3.3.3 8.8.8.8").enter().send_text("glasswall").enter()

            print("finishing task :%s!" % res)

            # if res > 0:
            #     print("Program submitted, PID is %d" % res)
            #     pid_exitcode = pm.ListProcessesInGuest(vm, creds,
            #                                            [res]).pop().exitCode
            #     # If its not a numeric result code, it says None on submit
            #     while (re.match('[^0-9]+', str(pid_exitcode))):
            #         print("Program running, PID is %d" % res)
            #         time.sleep(5)
            #         pid_exitcode = pm.ListProcessesInGuest(vm, creds,
            #                                                [res]).pop().\
            #             exitCode
            #         if (pid_exitcode == 0):
            #             print("Program %d completed with success" % res)
            #             break
            #         # Look for non-zero code to fail
            #         elif (re.match('[1-9]+', str(pid_exitcode))):
            #             print("ERROR: Program %d completed with Failute" % res)
            #             print("  tip: Try running this on guest %r to debug" \
            #                 % summary.guest.ipAddress)
            #             print("ERROR: More info on process")
            #             print(pm.ListProcessesInGuest(vm, creds, [res]))
            #             break

        except IOError as e:
            print(e)
    except vmodl.MethodFault as error:
        print("Caught vmodl fault : " + error.msg)
        return -1

    return 0

# Start program
if __name__ == "__main__":
    main()