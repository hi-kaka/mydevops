# -*- coding: utf-8 -*-
import os
PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))
# import sys
# os.environ["DJANGO_SETTINGS_MODULE"] = 'admin.settings.settings'
# import django
# django.setup()
from django.shortcuts import render
import json
from django.http import HttpResponseRedirect,JsonResponse
from django.http import HttpResponseRedirect,JsonResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse

from utils.ansible_api import ANSRunner
from scanhosts.lib.utils import prpcrypt

from taskdo.utils.base.MgCon import *
from taskdo.utils.base.RedisCon import *
import re

from detail.models import ConnectionInfo,GroupInfo
# from apps.test import test2
# from taskdo.utils.base.tools import CJsonEncoder


class DateEncoder(json.JSONEncoder ):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.__str__()
        return json.JSONEncoder.default(self, obj)

# Create your views here.
def adhoc_task(request):
    if request.method == "POST":
        result = {}
        jobs = request.body
        init_jobs = json.loads(jobs)

        mod_type = init_jobs["mod_type"] if init_jobs["mod_type"] else "shell"
        sn_keys = init_jobs["sn_key"]
        exec_args = init_jobs[u"exec_args"]
        group_name = init_jobs[u"group_name"] if init_jobs[u"group_name"] else "imoocc"
        taskid = init_jobs.get("taskid")
        if  not sn_keys or not exec_args or not taskid:
            result = {'status':"failed","code":002,"info":u"传入的参数不完整！"}
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            rlog = InsertAdhocLog(taskid=taskid)
        if mod_type not in ("shell","yum","copy"):
            result = {'status':"failed","code":003,"info":u"传入的参数mod_type不匹配！"}
            rlog.record(id=10008)
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            try:
                sn_keys = set(sn_keys)
                hosts_obj = ConnectionInfo.objects.filter(sn_key__in=sn_keys)
                rlog.record(id=10000)

                if len(sn_keys) != len(hosts_obj):
                    rlog.record(id=40004)
                else:
                    rlog.record(id=10002)
                    resource = {}
                    hosts_list = []
                    vars_dic = {}
                    cn = prpcrypt()
                    hosts_ip = []
                    for host in hosts_obj:
                        sshpasswd = cn.decrypt(host.ssh_userpasswd)
                        if host.ssh_type in (1,2):
                            """
                            #组装符合下面格式的resource传入到封装好的ansible API中
                            resource =  {
                                "dynamic_host": {
                                    "hosts": [
                                                {"hostname": "192.168.1.108", "port": "22", "username": "root", "ssh_key": "/etc/ansible/ssh_keys/id_rsa"},
                                                {"hostname": "192.168.1.109", "port": "22", "username": "root","ssh_key": "/etc/ansible/ssh_keys/id_rsa"}
                                              ],
                                    "vars": {
                                             "var1":"ansible",
                                             "var2":"saltstack"
                                             }
                                }
                            }
                            """
                            hosts_list.append({"hostname":host.sn_key,"ip":host.ssh_hostip,"port":host.ssh_host_port,"username":host.ssh_username,"ssh_key":host.ssh_rsa})
                            hosts_ip.append(host.sn_key)
                        elif host.ssh_type in (0,4):
                            hosts_list.append({"hostname":host.sn_key,"ip":host.ssh_hostip,"port":host.ssh_host_port,"username":host.ssh_username,"password":sshpasswd})
                            hosts_ip.append(host.sn_key)
                        elif host.ssh_type == 3:
                            hosts_list.append({"hostname":host.sn_key,"ip":host.ssh_hostip,"port":host.ssh_host_port,"username":host.ssh_username,"ssh_key":host.ssh_rsa,"password":sshpasswd})
                            hosts_ip.append(host.sn_key)


                    resource[group_name]={"hosts":hosts_list,"vars":vars_dic}
                    rlog.record(id=10003)
                    #任务锁检查
                    lockstatus = DsRedis.get(rkey="tasklock")
                    if lockstatus is None or lockstatus=='1':
                        # 已经有任务在执行
                        rlog.record(id=40005)
                        result = {'status':"failed","code":004,"info":u"已经有任务在执行,或者tasklock没有设置初始值！"}
                    else:
                        # 开始执行任务
                        rlog.record(id=10004)
                        DsRedis.setlock("tasklock",1)
                        jdo = ANSRunner(resource=resource)
                        jdo.run_model(host_list=hosts_ip,module_name=mod_type,module_args=exec_args)
                        res = jdo.get_model_result()
                        rlog.record(id=19999,input_con=res)
                        rlog.record(id=20000)
                        DsRedis.setlock("tasklock",0)
                        result = {"status":"success","code":001,"info":res}

            except Exception as e:
                import traceback
                print traceback.print_exc()
                DsRedis.setlock("tasklock",0)
                result = {"status":"failed","code":005,"info":e}
            finally:
                return HttpResponse(json.dumps(result), content_type="application/json")

def adhoc_task_h(request):
    if request.method == "POST":
        result = {}

        mod_type_tmp = request.POST.get('mod').strip()
        mod_type = mod_type_tmp if mod_type_tmp else "shell"
        host_text = request.POST.get('host')
        zhuji_list = re.split(r'[\s\,]+', host_text)
        exec_args = request.POST.get('execargs')
        group_name_tmp = request.POST.get('groupname').strip()
        group_name = group_name_tmp if group_name_tmp else "imoocc"
        taskid = request.POST.get('taskid').strip()
        if  not zhuji_list or not exec_args or not taskid:
            result = {'status':"failed","code":002,"info":u"传入的参数不完整！"}
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            rlog = InsertAdhocLog(taskid=taskid)
        if mod_type not in ("shell","yum","copy"):
            result = {'status':"failed","code":003,"info":u"传入的参数mod_type不匹配！"}
            rlog.record(id=10008)
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            try:
                zhuji_list = set(zhuji_list)
                hosts_obj = ConnectionInfo.objects.filter(ssh_hostip__in=zhuji_list)
                rlog.record(id=10000)

                if len(zhuji_list) != len(hosts_obj):
                    rlog.record(id=40004)
                else:
                    rlog.record(id=10002)
                    resource = {}
                    hosts_list = []
                    vars_dic = {}
                    cn = prpcrypt()
                    hosts_ip = []
                    for host in hosts_obj:
                        sshpasswd = cn.decrypt(host.ssh_userpasswd)
                        if host.ssh_type in (1,2):
                            """
                            #组装符合下面格式的resource传入到封装好的ansible API中
                            resource =  {
                                "dynamic_host": {
                                    "hosts": [
                                                {"hostname": "192.168.1.108", "port": "22", "username": "root", "ssh_key": "/etc/ansible/ssh_keys/id_rsa"},
                                                {"hostname": "192.168.1.109", "port": "22", "username": "root","ssh_key": "/etc/ansible/ssh_keys/id_rsa"}
                                              ],
                                    "vars": {
                                             "var1":"ansible",
                                             "var2":"saltstack"
                                             }
                                }
                            }
                            """
                            hosts_list.append({"hostname":host.sn_key,"ip":host.ssh_hostip,"port":host.ssh_host_port,"username":host.ssh_username,"ssh_key":host.ssh_rsa})
                            hosts_ip.append(host.sn_key)
                        elif host.ssh_type in (0,4):
                            hosts_list.append({"hostname":host.sn_key,"ip":host.ssh_hostip,"port":host.ssh_host_port,"username":host.ssh_username,"password":sshpasswd})
                            hosts_ip.append(host.sn_key)
                        elif host.ssh_type == 3:
                            hosts_list.append({"hostname":host.sn_key,"ip":host.ssh_hostip,"port":host.ssh_host_port,"username":host.ssh_username,"ssh_key":host.ssh_rsa,"password":sshpasswd})
                            hosts_ip.append(host.sn_key)


                    resource[group_name]={"hosts":hosts_list,"vars":vars_dic}
                    rlog.record(id=10003)
                    #任务锁检查
                    lockstatus = DsRedis.get(rkey="tasklock")
                    if lockstatus is None or lockstatus=='1':
                        # 已经有任务在执行
                        rlog.record(id=40005)
                        result = {'status':"failed","code":004,"info":u"已经有任务在执行,或者tasklock没有设置初始值！"}
                    else:
                        # 开始执行任务
                        rlog.record(id=10004)
                        DsRedis.setlock("tasklock",1)
                        jdo = ANSRunner(resource=resource)
                        jdo.run_model(host_list=hosts_ip,module_name=mod_type,module_args=exec_args)
                        res = jdo.get_model_result()
                        rlog.record(id=19999,input_con=res)
                        rlog.record(id=20000)
                        DsRedis.setlock("tasklock",0)
                        result = {"status":"success","code":001,"info":res}

            except Exception as e:
                import traceback
                print traceback.print_exc()
                DsRedis.setlock("tasklock",0)
                result = {"status":"failed","code":005,"info":e}
            finally:
                return HttpResponse(json.dumps(result), content_type="application/json")

def adhoc_task_g(request):
    if request.method == "POST":
        result = {}

        mod_type_tmp = request.POST.get('gmod').strip()
        mod_type = mod_type_tmp if mod_type_tmp else "shell"
        exec_args = request.POST.get('gexecargs')
        taskid = request.POST.get('gtaskid').strip()
        group_name = request.POST.get('group').strip()
        gob = GroupInfo.objects.filter(group_name=group_name)
        if not gob:
            result = {'status':"failed","code":006,"info":u"传入的组名不存在！"}
            return HttpResponse(json.dumps(result), content_type="application/json")
        if group_name.split('_')[1]=='1':
            zhuji_obj = ConnectionInfo.objects.filter(conn_grp1_id=gob[0].id)
        if group_name.split('_')[1]=='2':
            zhuji_obj = ConnectionInfo.objects.filter(conn_grp2_id=gob[0].id)
        if group_name.split('_')[1]=='3':
            zhuji_obj = ConnectionInfo.objects.filter(conn_grp3_id=gob[0].id)
        if group_name.split('_')[1]=='4':
            zhuji_obj = ConnectionInfo.objects.filter(conn_grp4_id=gob[0].id)
        if group_name.split('_')[1]=='5':
            zhuji_obj = ConnectionInfo.objects.filter(conn_grp5_id=gob[0].id)
        if group_name.split('_')[1]=='6':
            zhuji_obj = ConnectionInfo.objects.filter(conn_grp6_id=gob[0].id)
        if group_name.split('_')[1]=='7':
            zhuji_obj = ConnectionInfo.objects.filter(conn_grp7_id=gob[0].id)
        if group_name.split('_')[1]=='8':
            zhuji_obj = ConnectionInfo.objects.filter(conn_grp8_id=gob[0].id)
        if group_name.split('_')[1]=='9':
            zhuji_obj = ConnectionInfo.objects.filter(conn_grp9_id=gob[0].id)
        if group_name.split('_')[1]=='10':
            zhuji_obj = ConnectionInfo.objects.filter(conn_grp10_id=gob[0].id)
        if group_name.split('_')[1]=='11':
            zhuji_obj = ConnectionInfo.objects.filter(conn_grp11_id=gob[0].id)
        if group_name.split('_')[1]=='12':
            zhuji_obj = ConnectionInfo.objects.filter(conn_grp12_id=gob[0].id)
        if group_name.split('_')[1]=='13':
            zhuji_obj = ConnectionInfo.objects.filter(conn_grp13_id=gob[0].id)
        if group_name.split('_')[1]=='14':
            zhuji_obj = ConnectionInfo.objects.filter(conn_grp14_id=gob[0].id)
        if group_name.split('_')[1]=='15':
            zhuji_obj = ConnectionInfo.objects.filter(conn_grp15_id=gob[0].id)
        if not zhuji_obj:
            result = {'status':"failed","code":007,"info":u"传入的组为空，没有包含主机！"}
            return HttpResponse(json.dumps(result), content_type="application/json")
        zhuji_list = [i.ssh_hostip for i in zhuji_obj]
        if not exec_args or not taskid:
            result = {'status':"failed","code":002,"info":u"传入的参数不完整！"}
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            rlog = InsertAdhocLog(taskid=taskid)
        if mod_type not in ("shell","yum","copy"):
            result = {'status':"failed","code":003,"info":u"传入的参数mod_type不匹配！"}
            rlog.record(id=10008)
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            try:
                zhuji_list = set(zhuji_list)
                hosts_obj = ConnectionInfo.objects.filter(ssh_hostip__in=zhuji_list)
                rlog.record(id=10000)

                if len(zhuji_list) != len(hosts_obj):
                    rlog.record(id=40004)
                else:
                    rlog.record(id=10002)
                    resource = {}
                    hosts_list = []
                    vars_dic = {}
                    cn = prpcrypt()
                    hosts_ip = []
                    for host in hosts_obj:
                        sshpasswd = cn.decrypt(host.ssh_userpasswd)
                        if host.ssh_type in (1,2):
                            """
                            #组装符合下面格式的resource传入到封装好的ansible API中
                            resource =  {
                                "dynamic_host": {
                                    "hosts": [
                                                {"hostname": "192.168.1.108", "port": "22", "username": "root", "ssh_key": "/etc/ansible/ssh_keys/id_rsa"},
                                                {"hostname": "192.168.1.109", "port": "22", "username": "root","ssh_key": "/etc/ansible/ssh_keys/id_rsa"}
                                              ],
                                    "vars": {
                                             "var1":"ansible",
                                             "var2":"saltstack"
                                             }
                                }
                            }
                            """
                            hosts_list.append({"hostname":host.sn_key,"ip":host.ssh_hostip,"port":host.ssh_host_port,"username":host.ssh_username,"ssh_key":host.ssh_rsa})
                            hosts_ip.append(host.sn_key)
                        elif host.ssh_type in (0,4):
                            hosts_list.append({"hostname":host.sn_key,"ip":host.ssh_hostip,"port":host.ssh_host_port,"username":host.ssh_username,"password":sshpasswd})
                            hosts_ip.append(host.sn_key)
                        elif host.ssh_type == 3:
                            hosts_list.append({"hostname":host.sn_key,"ip":host.ssh_hostip,"port":host.ssh_host_port,"username":host.ssh_username,"ssh_key":host.ssh_rsa,"password":sshpasswd})
                            hosts_ip.append(host.sn_key)


                    resource[group_name]={"hosts":hosts_list,"vars":vars_dic}
                    rlog.record(id=10003)
                    #任务锁检查
                    lockstatus = DsRedis.get(rkey="tasklock")
                    if lockstatus is None or lockstatus=='1':
                        # 已经有任务在执行
                        rlog.record(id=40005)
                        result = {'status':"failed","code":004,"info":u"已经有任务在执行,或者tasklock没有设置初始值！"}
                    else:
                        # 开始执行任务
                        rlog.record(id=10004)
                        DsRedis.setlock("tasklock",1)
                        jdo = ANSRunner(resource=resource)
                        jdo.run_model(host_list=hosts_ip,module_name=mod_type,module_args=exec_args)
                        res = jdo.get_model_result()
                        rlog.record(id=19999,input_con=res)
                        rlog.record(id=20000)
                        DsRedis.setlock("tasklock",0)
                        result = {"status":"success","code":001,"info":res}

            except Exception as e:
                import traceback
                print traceback.print_exc()
                DsRedis.setlock("tasklock",0)
                result = {"status":"failed","code":005,"info":e}
            finally:
                return HttpResponse(json.dumps(result), content_type="application/json")

# Create your views here.
def adhoc_task_log(request):
    if request.method == "GET":
        taskid = request.GET.get("taskid")
        result = {}
        if taskid :
            rlog = InsertAdhocLog(taskid=taskid)
            res = rlog.getrecord()
            result = {"status":"success",'taskid':taskid,"info":res}
        else:
            result = {"status":"failed","info":u"没有传入taskid值"}
        res = json.dumps(result,cls=DateEncoder)
        return HttpResponse(res,content_type="application/json")

def adhoc_page(request):
    return render(request, 'taskdo/adhoc_page.html', {'title': "自动化任务控制台"})
