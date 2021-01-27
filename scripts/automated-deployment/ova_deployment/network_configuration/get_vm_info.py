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

        self.args = get_args()
        
        try:
            self.si = SmartConnectNoSSL(host=self.args.host,
                                        user=self.args.user,
                                        pwd=self.args.password,
                                        port=self.args.port)

            atexit.register(Disconnect, self.si)

            print("connected successfully to esxi server %s!" % self.args.host)
        
        except Exception as e:
            
            print("Unable to connect to %s" % self.args.host)
            raise e

    def collect_vm_info(self, virtual_machine):
        """
        Print information for a particular virtual machine or recurse into a
        folder with depth protection
        """
        vm_info_dict = dict()
        summary = virtual_machine.summary

        vm_info_dict["name"] = summary.config.name
        vm_info_dict["template"] = summary.config.template
        vm_info_dict["path"] = summary.config.vmPathName
        vm_info_dict["guest"] = summary.config.guestFullName
        vm_info_dict["instance_uuid"] = summary.config.instanceUuid
        vm_info_dict["bios_uuid"] = summary.config.uuid
        vm_info_dict["annotation"] = summary.config.annotation
        vm_info_dict["state"] = summary.runtime.powerState

        print("Name       : ", vm_info_dict["name"])
        print("Template   : ", vm_info_dict["template"])
        print("Path       : ", vm_info_dict["path"])
        print("Guest      : ", vm_info_dict["guest"])
        print("Instance UUID : ", vm_info_dict["instance_uuid"])
        print("Bios UUID     : ", vm_info_dict["bios_uuid"])

        if annotation:
            print("Annotation : ", vm_info_dict["annotation"])
        print("State      : ", vm_info_dict["state"])

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

        self.args.find = os.environ.get("VM_NAME")

        try:
        
            content = self.service_instance.RetrieveContent()

            container = content.rootFolder  # starting point to look into
            viewType = [vim.VirtualMachine]  # object types to look for
            recursive = True  # whether we should look into it recursively
            containerView = content.viewManager.CreateContainerView(
                container, viewType, recursive)

            children = containerView.view
            if self.args.find is not None:
                pat = re.compile(args.find, re.IGNORECASE)
            for child in children:
                if self.args.find is None:
                    vm_info_data = vm_info.collect_vm_info(child)
                else:
                    if pat.search(child.summary.config.name) is not None:
                        vm_info_data = vm_info.collect_vm_info(child)

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