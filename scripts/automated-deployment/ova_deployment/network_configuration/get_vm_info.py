import os
import re
import atexit

from pyVim import connect
from pyVmomi import vmodl
from pyVmomi import vim

from ..tools import cli as cli


def get_args():
    parser = cli.build_arg_parser()
    parser.add_argument('-f', '--find',
                        required=False,
                        action='store',
                        help='String to match VM names')
    args = parser.parse_args()

    return cli.prompt_for_password(args)


""" Class to return specified VM info in a dictionary. """
class GetVMInfo():
    
    def __init__(self):
        pass

    def print_vm_info(self, virtual_machine):
        """
        Print information for a particular virtual machine or recurse into a
        folder with depth protection
        """
        vm_info_dict = dict()

        summary = virtual_machine.summary
        print("Name       : ", summary.config.name)
        print("Template   : ", summary.config.template)
        print("Path       : ", summary.config.vmPathName)
        print("Guest      : ", summary.config.guestFullName)
        print("Instance UUID : ", summary.config.instanceUuid)
        print("Bios UUID     : ", summary.config.uuid)

        vm_info_dict["name"] = summary.config.name
        vm_info_dict["template"] = summary.config.template
        vm_info_dict["path"] = summary.config.vmPathName
        vm_info_dict["guest"] = summary.config.guestFullName
        vm_info_dict["instance_uuid"] = summary.config.instanceUuid
        vm_info_dict["bios_uuid"] = summary.config.uuid

        annotation = summary.config.annotation
        vm_info_dict["annotation"] = annotation

        if annotation:
            print("Annotation : ", annotation)
        print("State      : ", summary.runtime.powerState)
        vm_info_dict["state"] = summary.runtime.powerState

        if summary.guest is not None:
            ip_address = summary.guest.ipAddress
            tools_version = summary.guest.toolsStatus
            if tools_version is not None:
                print("VMware-tools: ", tools_version)
            else:
                print("Vmware-tools: None")
            if ip_address:
                print("IP         : ", ip_address)
            else:
                print("IP         : None")
        if summary.runtime.question is not None:
            print("Question  : ", summary.runtime.question.text)
        print("")
        
        return vm_info_dict


    def main(self):
        """
        Simple command-line program for listing the virtual machines on a system.
        """

        vm_info = GetVMInfo()
        vm_info_data = {}

        args = get_args()
        args.find = os.environ.get("VM_NAME")

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

            container = content.rootFolder  # starting point to look into
            viewType = [vim.VirtualMachine]  # object types to look for
            recursive = True  # whether we should look into it recursively
            containerView = content.viewManager.CreateContainerView(
                container, viewType, recursive)

            children = containerView.view
            if args.find is not None:
                pat = re.compile(args.find, re.IGNORECASE)
            for child in children:
                if args.find is None:
                    vm_info_data = vm_info.print_vm_info(child)
                else:
                    if pat.search(child.summary.config.name) is not None:
                        vm_info_data = vm_info.print_vm_info(child)

        except vmodl.MethodFault as error:
            print("Caught vmodl fault : " + error.msg)
            return -1

        return vm_info_data


# Start program
if __name__ == "__main__":
    vm_info = GetVMInfo()
    vm_data = vm_info.main()
    print("Returned info:", vm_data)
    print("instance UUID: %s" % vm_data.get("instance_uuid"))