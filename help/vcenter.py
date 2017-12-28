import atexit
from pyVmomi import vim, vmodl
from pyVim.task import WaitForTask
from pyVim import connect
from pyVim.connect import Disconnect


class VCenter:
    def __init__(self, host, user, password):
        si = connect.SmartConnectNoSSL(host=host, user=user, pwd=password, port=443)
        atexit.register(Disconnect, si)
        self.content = si.RetrieveContent()

    @staticmethod
    def __print_vm_info(vm):
        info = dict()
        summary = vm.summary
        info['name'] = summary.config.name
        info['template'] = summary.config.template
        info['path'] = summary.config.vmPathName
        info['guest'] = summary.config.guestFullName
        info['instance_uuid'] = summary.config.instanceUuid
        info['bios_uuid'] = summary.config.uuid

        annotation = summary.config.annotation
        if annotation:
            info['annotation'] = annotation

        info['state'] = summary.runtime.powerState

        if summary.guest is not None:
            tools_version = summary.guest.toolsStatus
            if tools_version is not None:
                info['vmware_tools'] = tools_version

            ip_address = summary.guest.ipAddress
            if ip_address:
                info['ip_address'] = ip_address

        if summary.runtime.question is not None:
            info['question'] = summary.runtime.question.text

        return info

    def get_all_vms(self):

        container = self.content.rootFolder
        view_type = [vim.VirtualMachine]
        recursive = True
        container_view = self.content.viewManager.CreateContainerView(container, view_type, recursive)

        children = container_view.view
        vms = list()
        for child in children:
            vms.append(self.__print_vm_info(child))

        return vms

    def remove_snapshot(self, vm_name, snapshot_name):
        vm = self.__get_obj(self.content, [vim.VirtualMachine], vm_name)

        if vm.snapshot is not None:
            snap_obj = self.__get_snapshots_by_name_recursively(vm.snapshot.rootSnapshotList, snapshot_name)

            if len(snap_obj) == 1:
                snap_obj = snap_obj[0].snapshot
                # print('Removendo snapshot {0}'.format(snapshot_name))
                WaitForTask(snap_obj.RemoveSnapshot_Task(True))
            # else:
                # print('Nenhum snapshot encontrado com o nome {0} na VM: {1}'.format(snap_obj, vm.name))

    def snapshot_list(self, vm_name):
        vm = self.__get_obj(self.content, [vim.VirtualMachine], vm_name)
        # if not vm:
        #     print('A VM {0} nao existe!'.format(vm_name))
        #     pass

        snapshots = list()
        if vm.snapshot is not None:
            snapshot_paths = self.__list_snapshots_recursively(vm.snapshot.rootSnapshotList)
            for snapshot in snapshot_paths:
                snapshots.append(snapshot)

        return snapshots

    @staticmethod
    def __get_obj(content, vimtype, name):
        obj = None
        container = content.viewManager.CreateContainerView(
            content.rootFolder, vimtype, True)
        for c in container.view:
            if c.name == name:
                obj = c
                break
        return obj

    def __list_snapshots_recursively(self, snapshots):
        snapshot_data = []
        for snapshot in snapshots:
            snap_text = {'Name': snapshot.name, 'Description': snapshot.description, 'CreateTime': '%s' % snapshot.createTime, 'State': snapshot.state}
            snapshot_data.append(snap_text)
            snapshot_data = snapshot_data + self.__list_snapshots_recursively(snapshot.childSnapshotList)
        return snapshot_data

    def __get_snapshots_by_name_recursively(self, snapshots, snap_name):
        snap_obj = []
        for snapshot in snapshots:
            if snapshot.name == snap_name:
                snap_obj.append(snapshot)
            else:
                snap_obj = snap_obj + self.__get_snapshots_by_name_recursively(snapshot.childSnapshotList, snap_name)
        return snap_obj

    def __get_current_snap_obj(self, snapshots, snapob):
        snap_obj = []
        for snapshot in snapshots:
            if snapshot.snapshot == snapob:
                snap_obj.append(snapshot)
            snap_obj = snap_obj + self.__get_current_snap_obj(snapshot.childSnapshotList, snapob)
        return snap_obj
