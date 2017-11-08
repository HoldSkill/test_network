# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import datetime
from django.http import HttpResponse
from django.views.generic.base import View
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from ipad_weixin.weixin_bot import WXBot
from ipad_weixin.models import Qrcode, WxUser, ChatRoom, SignInRule
from ipad_weixin.heartbeat_manager import HeartBeatManager

import logging
logger = logging.getLogger('django_views')


class GetQrcode(View):
    """
    接口： http://s-prod-04.quinzhu666.com：8080/robot/getqrcode?username=md_username
    """
    def post(self, request):
        req_dict = json.loads(request.body)
        md_username = req_dict.get('username', '')
        platform_id = req_dict.get('platform_id', '')
        if not platform_id:
            return HttpResponse(json.dumps({"Error": "未知平台"}))

        wx_bot = WXBot()
        (oss_path, qrcode_rsp, deviceId, uuid) = wx_bot.get_qrcode(md_username)

        import thread
        thread.start_new_thread(wx_bot.check_and_confirm_and_load, (qrcode_rsp, deviceId, md_username, platform_id))

        response_data = {"qrcode_url": oss_path, "uuid": uuid}
        return HttpResponse(json.dumps(response_data), content_type="application/json")


class HostList(View):
    """
    接口： http://s-prod-04.quinzhu666.com:8080/robot/host_list?username=md_username
    """
    def get(self, request):
        username = request.GET.get('username', '')
        data = []
        try:
            wxusers = WxUser.objects.filter(user__username=username).all()
            for wxuser in wxusers:
                robot_chatroom_list = []
                production_chatroom_list = []
                ret = wxuser.login
                name = wxuser.nickname
                chatroom_list = ChatRoom.objects.filter(wx_user__username=wxuser.username)
                for chatroom in chatroom_list:
                    robot_chatroom_list.append(chatroom.nickname)
                    if chatroom.is_send:
                        production_chatroom_list.append({"nickname": chatroom.nickname,
                                                         "username": chatroom.username})
                data.append({"ret": ret, "name": name,
                             "group": robot_chatroom_list,
                             "production_list": production_chatroom_list})
        except Exception as e:
            logger.error(e)
            print(e)
        response_data = {"data": data}
        return HttpResponse(json.dumps(response_data))


class IsLogin(View):
    """
    接口： http://s-prod-04.quinzhu666.com:8080/robot/is_login?username=md_username
    """
    def get(self, request):
        username = request.GET.get('username', '')
        if 'username' == '':
            response_data = {"ret": str(0), "name": "未登录"}
            return HttpResponse(json.dumps(response_data))
        ret = 0
        name = ''
        try:
            qr_code_db = Qrcode.objects.filter(md_username=username, username__isnull=False).order_by('-id').first()
            wx_username = qr_code_db.username
            print(wx_username)

            # 筛选出wx用户昵称
            wxuser = WxUser.objects.filter(username=wx_username).order_by('-id').first()
            ret = wxuser.login
            name = wxuser.nickname

            print(name.encode('utf8'))
        except Exception as e:
            logger.error(e)
            print(e)

        response_data = {"ret": str(ret), "name": name}
        return HttpResponse(json.dumps(response_data))


class IsUuidLogin(View):
    """
    检测该UUID是否被扫描登陆
    http://s-prod-04.qunzhu666.com:8080/robot/is_uuid_login?uuid=gZF8miqrkksZ9mrRk7mc
    """
    def get(self, request):
        uuid = request.GET.get('uuid', '')
        if uuid == '':
            response_data = {"ret": str(0), "name": "uuid为空"}
            return HttpResponse(json.dumps(response_data))
        ret = 0
        name = ''
        try:
            # username是手机号
            qr_code_db = Qrcode.objects.filter(uuid=uuid).first()
            if qr_code_db is not None and qr_code_db.username != '':
                wx_username = qr_code_db.username
                # 筛选出wx_username
                print wx_username

                # 筛选出wx用户昵称
                user_db = WxUser.objects.filter(username=wx_username).first()
                ret = user_db.login
                name = user_db.nickname
        except Exception as e:
            logger.error(e)
            print(e)
        # name <type 'unicode'>
        response_data = {"ret": str(ret), "name": name}
        return HttpResponse(json.dumps(response_data))


class ResetHeartBeat(View):
    """
    此方法只能在重启supervisor服务时使用，系统运行时严禁使用该接口
    http://s-prod-04.qunzhu666.com:8080/robot/reset_heart_beat
    """
    def get(self, request):
        auth_users = WxUser.objects.filter(last_heart_beat__gt=timezone.now() - datetime.timedelta(minutes=300))
        if not auth_users:
            logger.info("重启心跳用户数为0")
        for auth_user in auth_users:
            logger.info("%s command 开启心跳" % auth_user.nickname)
            # 清空心跳列表
            if auth_user.username in HeartBeatManager.heartbeat_thread_dict:
                del HeartBeatManager.heartbeat_thread_dict[auth_user.username]
            HeartBeatManager.begin_heartbeat(auth_user.username)
        return HttpResponse(json.dumps({"ret": 1}))


class ResetSingleHeartBeat(View):
    """
    开启单个用户心跳
    接口： http://s-prod-04.qunzhu666.com:8080/reset_single?username=wx_id
    """
    def get(self, request):
        username = request.GET.get('username')
        if username in HeartBeatManager.heartbeat_thread_dict:
            del HeartBeatManager.heartbeat_thread_dict[username]
        HeartBeatManager.begin_heartbeat(username)
        return HttpResponse(json.dumps({"ret": 1}))


class AddSuperUser(View):
    """
    添加只有签到功能的customer_service, 即不会发单
    接口: http://s-prod-04.qunzhu666.com/add_super_user?username=wx_id
    """
    def get(self, request):
        username = request.GET.get('username')
        wx_user = WxUser.objects.get(username=username)
        if wx_user:
            wx_user.is_customer_server = True
            wx_user.save()
            return HttpResponse(json.dumps({"ret": u"add superuser successfully"}))
        else:
            return HttpResponse(json.dumps({"ret": u"add superuser failed"}))













