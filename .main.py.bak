#!/usr/bin/env python
# -*- coding:utf-8 -*-
import datetime
import os
import re
import yaml
#import sys
import time
PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))
os.environ["DJANGO_SETTINGS_MODULE"] = 'admin.settings.settings'
import django
django.setup()
from admin.settings.settings import BASE_DIR
import logging
logger = logging.getLogger("django")

from scanhosts.util.nmap_all_server import snmp_begin
from scanhosts.models import HostLoginifo
from detail.models import  PhysicalServerInfo,VirtualServerInfo,ConnectionInfo,OtherMachineInfo,StatisticsRecord
from scanhosts.util.j_filter import FilterRules
from scanhosts.util.get_pv_relation import GetHostType
from scanhosts.util.nmap_all_server import NmapDocker
from scanhosts.util.nmap_all_server import NmapKVM
from scanhosts.util.nmap_all_server import NmapVMX

def main():
    '''
    读取扫描所需配置文件
    :return:
    '''
    s_conf = yaml.load(file('conf/scanhosts.yaml'))
    s_nets = s_conf['hostsinfo']['nets']
    s_ports = s_conf['hostsinfo']['ports']
    s_pass = s_conf['hostsinfo']['ssh_pass']
    s_cmds = s_conf['hostsinfo']['syscmd_list']
    s_keys = s_conf['hostsinfo']['ssh_key_file']
    s_blacks = s_conf['hostsinfo']['black_list']
    s_emails = s_conf['hostsinfo']['email_list']

    n_sysname_oid = s_conf['netinfo']['sysname_oid']
    n_sn_oid = s_conf['netinfo']['sn_oids']
    n_commu = s_conf['netinfo']['community']
    n_login_sw = s_conf['netinfo']['login_enable']
    n_backup_sw = s_conf['netinfo']['backup_enable']
    n_backup_sever = s_conf['netinfo']['tfp_server']

    d_pass = s_conf['dockerinfo']['ssh_pass']
    starttime = datetime.datetime.now()
    
    # '''
    # 扫描主机信息
    # '''
    for nmap_type in s_nets:
        unkown_list,key_not_login_list = snmp_begin(nmap_type,s_ports,s_pass,s_keys,s_cmds,s_blacks,s_emails)
        #snmp_begin(nmap_type,s_ports,s_pass,s_keys,s_cmds,s_blacks,s_emails)
    print unkown_list
    print key_not_login_list

    '''
    扫描网络信息
    '''
    if key_not_login_list:
        for item in key_not_login_list:
            HostLoginifo.objects.update_or_create(ip=item,ssh_port=key_not_login_list[item],ssh_status=0)
            other_sn = item.replace('.','')
            ob = OtherMachineInfo.objects.filter(sn_key=other_sn)
            if not ob:
                print ".........................OtherMachineInfo",item,other_sn
                OtherMachineInfo.objects.create(ip=item,sn_key=other_sn,reson_str=u"SSH端口存活，无法登录",oth_cab_id=1)
    if unkown_list:
        for item in unkown_list:
            HostLoginifo.objects.update_or_create(ip=item,ssh_status=0)
            other_sn = item.replace('.','')
            ob = OtherMachineInfo.objects.filter(sn_key=other_sn)
            if not ob:
                OtherMachineInfo.objects.create(ip=item,sn_key=other_sn,reson_str=u"IP存活，非Linux服务器",oth_cab_id=2)

    '''
    把HostLoginifo中所有可以登录的信息以处理过的sn（没有sn用处理过的mac）为sn_key组成dict，利用该dict，全部插入ConnectionInfo，
    区分后kvm VMware虚拟机插入VirtualServerInfo，
    此处有个bug，此时PhysicalServerInfo为空，插入时指定了PhysicalServerInfo的外键vir_phy_id，所以在PhysicalServerInfo先插入一条，vir_phy_id指向它的id，后续扫描kvm ESXI宿主机时再把vir_phy_id更改为对应的宿主机id
    区分后留下的机器插入PhysicalServerInfo，返回所有物理机组成的dict:{sn_key:ip}
    '''
    ft = FilterRules()
    key_ip_dic = ft.run()
    print 'key_ip_dic:',key_ip_dic

    if key_ip_dic:
        '''
        区分物理机为kvm VMware docker宿主机，更新HostLoginifo中的host_type为对应的值，
        由于Esx宿主机无法通过dmicode命令获取mathine_type，更改PhysicalServerInfo中的machine_brand，
        返回检测命令对应宿主机类型list组成的dict
        '''
        pv = GetHostType()
        p_relate_dic = pv.get_host_type(key_ip_dic)
        
        '''
        更新physicalserverinfo中宿主机的类型，即vir_type
        '''
        ip_key_dic = {v:k for k,v in key_ip_dic.items()}
        docker_p_list = p_relate_dic["docker-containerd"]
        kvm_p_list = p_relate_dic["qemu-system-x86_64"]
        vmware_p_list = p_relate_dic["vmx"]
        for item in docker_p_list:
            PhysicalServerInfo.objects.filter(conn_phy__sn_key=ip_key_dic[item]).update(vir_type="1")
        for item in kvm_p_list:
            PhysicalServerInfo.objects.filter(conn_phy__sn_key=ip_key_dic[item]).update(vir_type="0")
        for item in vmware_p_list:
            PhysicalServerInfo.objects.filter(conn_phy__sn_key=ip_key_dic[item]).update(vir_type="2")
        
        '''
        首先对docker宿主机列表一个一个进行容器探测，得出容器ssh端口，然后用try_docker_login进行登录探测，
        当端口可以登录：
        插入一条到ConnectionInfo，指定ssh_type=4(docker可以登录)，sn_key=docker在宿主机中的唯一标识，
        插入一条到VirtualServerInfo，指定server_type="Docker Contianer"，插入登录执行命令返回后的各种信息，conn_vir_id外键等于ConnectionInfo中对应的id，
        当PhysicalServerInfo中一条记录对应ConnectionInfo中的记录的sn_key与ip_key_dic[docker宿主机ip]的值吻合时，此时PhysicalServerInfo的物理机为docker的宿主机，
        vir_phy_id外键等于这条记录的id（其实可以直接在PhysicalServerInfo中通过docker宿主机ip过滤得到物理机外键？）
        当端口不能登录：
        插入一条到ConnectionInfo，没有ssh_userpasswd，指定ssh_status=0,ssh_type=5(docker不能登录)，sn_key=docker在宿主机中的唯一标识，
        插入一条到VirtualServerInfo，指定server_type="Docker Contianer"，conn_vir_id外键等于ConnectionInfo中对应的id，vir_phy_id外键等于物理机id
        '''
        ds = NmapDocker(s_cmds,d_pass,ip_key_dic)
        ds.do_nmap(docker_p_list)
        
        '''
        对KVM宿主机进行mac地址探测，得到上面所有的虚拟机的mac地址，一一将mac地址与virtualserverinfo中虚拟机的mac地址比对，
        符合则得到该虚拟机的宿主机，update虚拟机记录的vir_phy_id和server_type
        '''
        ks = NmapKVM(ip_key_dic)
        ks.do_nmap(kvm_p_list)
        
        '''
        利用sdk SnmpVMS对VMware宿主机进行探测，得到上面所有的虚拟机，在virtualserverinfo中将虚拟机与宿主机关联对应，
        update虚拟机记录的vir_phy_id和server_type
        完成虚拟机关联宿主机后，可以把PhysicalServerInfo中人为插入的那条记录删掉了
        '''
        ne = NmapVMX(vmware_p_list,ip_key_dic)
        ne.dosnmp()

    # '''
    # 更新状态表，用户信息表，还未用到，还没有创建app operations
    # '''
    # c_sn_lst = [item.sn_key for item in ConnectionInfo.objects.all()]
    # o_sn_lst = [item.sn_key for item in OtherMachineInfo.objects.all()]
    # old_sn_list = [item.sn_key for item in MachineOperationsInfo.objects.all()]
    # new_sn_lst = c_sn_lst + o_sn_lst
    # diff_sn_lst = set(new_sn_lst + old_sn_list)
    #
    # for item in diff_sn_lst:
    #     try:
    #         nsin = MachineOperationsInfo.objects.filter(sn_key=item)
    #         if not nsin:
    #             MachineOperationsInfo.objects.create(sn_key=item)
    #     except Exception as e:
    #         print "Error:SN:%s not insert into database,reason is:%s"%(item,e)
    #         logger.error("Error:SN:%s not insert into database,reason is:%s"%(item,e))
    #
    # '''
    # 统计总数
    # '''
    # info_dic = Machines().get_all_count()
    # StatisticsRecord.objects.create(all_count=info_dic['all_c'],pyh_count=info_dic['pyh_c'],net_count=info_dic['net_c'],
    #                                 other_count=info_dic['other_c'],vmx_count=info_dic['vmx_c'],kvm_count=info_dic['kvm_c'],docker_count=info_dic['docker_c'])

if __name__ == '__main__':
    main()
