# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import datetime
import pickle
import time
import random

from django.http import HttpResponse
from django.views.generic.base import View
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from ipad_weixin.weixin_bot import WXBot
from ipad_weixin.models import Qrcode, WxUser, ChatRoom, SignInRule, PlatformInformation, Wxuser_Chatroom
from ipad_weixin.heartbeat_manager import HeartBeatManager
from ipad_weixin.settings import red
from ipad_weixin.utils import oss_utils

import logging
logger = logging.getLogger('django_views')


class GetQrcode(View):
    """
    接口： http://s-prod-04.quinzhu666.com：10024/robot/getqrcode/
    格式：
        {
            "md_username": "smart",
            "platform_id": ""
        }
    """
    @csrf_exempt
    def post(self, request):
        req_dict = json.loads(request.body)
        md_username = req_dict.get('md_username', '')
        platform_id = req_dict.get('platform_id', '')

        if not md_username:
            return HttpResponse(json.dumps({"ret": 0, "reason": "username不允许为空"}))

        if not platform_id:
            return HttpResponse(json.dumps({"ret": 0, "reason": "platform_id为空"}))
        if not PlatformInformation.objects.filter(platform_id=platform_id):
            return HttpResponse(json.dumps({"ret": 0, "reason": "未知平台"}))

        wx_bot = WXBot()
        (oss_path, qrcode_rsp, deviceId, uuid) = wx_bot.get_qrcode(md_username)

        import thread
        thread.start_new_thread(wx_bot.check_and_confirm_and_load, (qrcode_rsp, deviceId, md_username, platform_id))

        response_data = {"qrcode_url": oss_path, "uuid": uuid}
        return HttpResponse(json.dumps(response_data), content_type="application/json")


class HostList(View):
    """
    返回用户所有的群组以及生产群
    接口： http://s-prod-04.quinzhu666.com:10024/robot/host_list?md_username=
    """
    def get(self, request):
        username = request.GET.get('md_username', '')
        if not username:
            return HttpResponse(json.dumps({"ret": 0, "reason": "username不允许为空"}))
        data = []
        try:
            wxusers = WxUser.objects.filter(user__username=username).all()
            for wxuser in wxusers:
                robot_chatroom_list = []
                production_chatroom_list = []
                ret = wxuser.login
                name = wxuser.nickname
                wx_username = wxuser.username
                chatroom_list = ChatRoom.objects.filter(wxuser__username=wxuser.username)
                for chatroom in chatroom_list:
                    robot_chatroom_list.append({"nickname": chatroom.nickname,
                                                "username": chatroom.username})
                    wxuser_chatroom = Wxuser_Chatroom.objects.get(wxuser=wxuser, chatroom=chatroom)
                    if wxuser_chatroom.is_send:
                        production_chatroom_list.append({"nickname": chatroom.nickname,
                                                         "username": chatroom.username})
                data.append({"ret": ret, "name": name,
                             "wx_username": wx_username,
                             "group": robot_chatroom_list,
                             "production_list": production_chatroom_list})
        except Exception as e:
            logger.error(e)
            print(e)
        response_data = {"data": data}
        return HttpResponse(json.dumps(response_data))


class IsUuidLogin(View):
    """
    检测该UUID是否被扫描登陆
    http://s-prod-04.qunzhu666.com:10024/robot/is_uuid_login?uuid=
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
    http://s-prod-04.qunzhu666.com:10024/robot/ed0050a7a7c9/reset_heart_beat
    """
    def get(self, request):
        auth_users = WxUser.objects.filter(last_heart_beat__gt=timezone.now() - datetime.timedelta(minutes=300))
        if not auth_users:
            logger.info("重启心跳用户数为0")
        for auth_user in auth_users:
            random_num = random.randint(0, 5)
            time.sleep(random_num)
            logger.info("%s command 开启心跳" % auth_user.nickname)
            # 清空心跳列表
            if auth_user.username in HeartBeatManager.heartbeat_thread_dict:
                del HeartBeatManager.heartbeat_thread_dict[auth_user.username]
            HeartBeatManager.begin_heartbeat(auth_user.username)
        return HttpResponse(json.dumps({"ret": 1}))


class ResetSingleHeartBeat(View):
    """
    开启单个用户心跳
    接口： http://s-prod-04.qunzhu666.com:10024/reset_single?wx_id=wx_id
    """
    def get(self, request):
        username = request.GET.get('wx_id', "")
        if not username:
            return HttpResponse(json.dumps({"ret": 0, "reason": "wx_id不能为空"}))

        v_user_pickle = red.get('v_user_' + username)
        v_user = pickle.loads(v_user_pickle)
        if v_user:
            wx_bot = WXBot()
            wx_bot.logout_bot(v_user)
            heart_status = red.get('v_user_heart_' + username)
            if heart_status:
                if int(heart_status) == 1:
                    red.set('v_user_heart_' + username, 2)
                    logger.info("%s: 准备终止用户心跳，需要大概30s" % username)
                    oss_utils.beary_chat("%s: 准备终止用户心跳，需要大概30s..." % username)
                    time.sleep(30)

            red.set('v_user_heart_' + username, 0)
        if username in HeartBeatManager.heartbeat_thread_dict:
            del HeartBeatManager.heartbeat_thread_dict[username]
        HeartBeatManager.begin_heartbeat(username)
        return HttpResponse(json.dumps({"ret": 1}))

# use just for test
class test(View):
    def get(self, request):
        username = request.GET.get('wx_id', "")
        if not username:
            return HttpResponse(json.dumps({"ret": 0, "reason": "wx_id不能为空"}))
        v_user_pickle = red.get('v_user_' + username)
        v_user = pickle.loads(v_user_pickle)
        if v_user:
            wx_bot = WXBot()
            # wx_bot.send_text_msg('6610815091@chatroom', 'hello, hello, hello', v_user)
            wx_bot.send_voice_msg(v_user, '6610815091@chatroom')
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













