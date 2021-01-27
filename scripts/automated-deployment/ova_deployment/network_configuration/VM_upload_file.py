#!/usr/bin/env python
from __future__ import with_statement
import atexit
import requests
from ..tools import cli
from ..tools import tasks
from pyVim import connect
from pyVmomi import vim, vmodl
import re
import os

from .get_vm_info import GetVMInfo
from k8_vmware.vsphere.Sdk import Sdk


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

    parser.add_argument('-l', '--path_inside_vm',
                        required=False,
                        action='store',
                        help='Path inside VM for upload')

    parser.add_argument('-f', '--upload_file',
                        required=False,
                        action='store',
                        help='Path of the file to be uploaded from host')

    args = parser.parse_args()

    cli.prompt_for_password(args)
    return args


class VMUploadFile:

    def __init__(self):

        self.args = get_args()
        
        # path of file to upload
        self.host_file_path = os.path.dirname(os.path.realpath(__file__))

        # inside vm path to upload to
        self.vm_path = os.environ.get("VM_UPLOAD_PATH")

        try:
            self.service_instance = connect.SmartConnectNoSSL(  host=self.args.host,
                                                                user=self.args.user,
                                                                pwd=self.args.password,
                                                                port=self.args.port)

            atexit.register(connect.Disconnect, self.service_instance)
            print("connected successfully to esxi server %s!" % self.args.host)
        
        except Exception as e:     
            print("Unable to connect to %s" % self.args.host)
            raise e

    def get_instance_uuid(self):
        vm_info_data = GetVMInfo().main()
        print(vm_info_data)
        inst_uuid = vm_info_data.get("instance_uuid")
        return inst_uuid

    def main(self):
        """
        Simple command-line program for Uploading a file from host to guest
        """
        instance_uuid = self.get_instance_uuid()
        print("Instance UUID: %s" % instance_uuid)
        
        upload_file = os.path.join(self.host_file_path, os.environ.get("UPLOAD_FILE_NAME"))
        self.args.upload_file = upload_file
        print(upload_file)

        try:
            
            content = self.service_instance.RetrieveContent()

            # vm = content.searchIndex.FindByUuid(None, args.vm_uuid, True)
            vm = content.searchIndex.FindByUuid(datacenter=None,
                                                uuid=instance_uuid,
                                                vmSearch=True,
                                                instanceUuid=True)
            
            # sdk = Sdk()
            # vm = sdk.find_by_uuid(instance_uuid)

            print("vm:", vm)
            
            creds = vim.vm.guest.NamePasswordAuthentication(
                username=self.args.vm_user, password=self.args.vm_pwd)
            with open(self.args.upload_file, 'rb') as myfile:
                fileinmemory = myfile.read()

            try:
                file_attribute = vim.vm.guest.FileManager.FileAttributes()
                url = content.guestOperationsManager.fileManager. \
                    InitiateFileTransferToGuest(vm, creds, self.vm_path,
                                                file_attribute,
                                                len(fileinmemory), True)
                # When : host argument becomes https://*:443/guestFile?
                # Ref: https://github.com/vmware/pyvmomi/blob/master/docs/ \
                #            vim/vm/guest/FileManager.rst
                # Script fails in that case, saying URL has an invalid label.
                # By having hostname in place will take take care of this.
                url = re.sub(r"^https://\*:", "https://"+str(self.args.host)+":", url)
                resp = requests.put(url, data=fileinmemory, verify=False)
                if not resp.status_code == 200:
                    print("Error while uploading file")
                else:
                    print("Successfully uploaded file")
            except IOErrorn as e:
                print(e)
        except vmodl.MethodFault as error:
            print("Caught vmodl fault : " + error.msg)
            return -1

        return 0

# Start program
if __name__ == "__main__":
    VMUploadFile().main()