# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import datetime
from django.http import HttpResponse
from django.views.generic.base import View
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth.models import User

from ipad_weixin.weixin_bot import WXBot
from ipad_weixin.models import Qrcode, WxUser, ChatRoom, SignInRule, PushRecord
from ipad_weixin.heartbeat_manager import HeartBeatManager
from ipad_weixin.send_msg_type import sendMsg

import thread

import logging
logger = logging.getLogger('django_views')


class SendMsgView(View):
    @csrf_exempt
    def post(self, request):
        req_dict = json.loads(request.body)
        md_username = req_dict.get("md_username", "")

        data = req_dict.get("data", "")

        wxuser_list = WxUser.objects.filter(user__username=md_username, login=1, is_customer_server=False)
        for wxuser in wxuser_list:
            chatroom_list = ChatRoom.objects.filter(wx_user=wxuser, is_send=True)
            if not chatroom_list:
                return HttpResponse(json.dumps({"ret": 0, "data": "发单群为空"}))

            for chatroom in chatroom_list:
                # 一个群一个线程去处理
                wx_id = wxuser.username
                chatroom_id = chatroom.username
                thread.start_new_thread(sendMsg, (wx_id, chatroom_id, data))

        return HttpResponse(json.dumps({"ret": 1, "data": "处理完成"}))


class PlatformUserList(View):
    def get(self, request):
        platform_id = request.GET.get("platform_id", "")
        if not platform_id:
            return HttpResponse(json.dumps({"ret": 0, "Error": "未知平台id"}))
        login_user_db = User.objects.filter(wxuser__login=1, wxuser__is_customer_server=False, first_name=platform_id)
        if not login_user_db:
            return HttpResponse(json.dumps({"ret": 0, "Error": "筛选{}平台User为空".format(platform_id)}))
        login_user_list = list(set(login_user.username for login_user in login_user_db))
        return HttpResponse(json.dumps({"ret": 1, "login_user_list": login_user_list}))


class AddProductionChatroom(View):
    @csrf_exempt
    def post(self, request):
        """
        数据类型：josn
        格式：
        {
            "md_username":
            "chatroom": ["chatroom.username",......]
        }
        """
        req_dict = json.loads(request.body)
        chatroom_list = req_dict["chatroom_list"]
        if not chatroom_list:
            return HttpResponse(json.dumps({"ret": 0, "reason": "chatroom_list为空"}))
        for chatroom_username in chatroom_list:
            chatroom_db = ChatRoom.objects.get(username=chatroom_username)
            chatroom_db.is_send = True
            chatroom_db.save()
        return HttpResponse(json.dumps({"ret": 1, "reason": "添加生产群成功"}))


class RemoveProductionChatroom(View):
    @csrf_exempt
    def post(self, request):
        req_dict = json.loads(request.body)
        chatroom_list = req_dict["chatroom_list"]
        if not chatroom_list:
            return HttpResponse(json.dumps({"ret": 0, "reason": "chatroom_list为空"}))
        for chatroom_username in chatroom_list:
            chatroom_db = ChatRoom.objects.get(username=chatroom_username)
            chatroom_db.is_send = False
            chatroom_db.save()
        return HttpResponse(json.dumps({"ret": 1, "reason": "删除生产群成功"}))



class DefineSignRule(View):
    """
    接口： http://s-prod-04.qunzhu666.com:8080/define_sign_rule
    """
    @csrf_exempt
    def post(self, request):
        req_dict = json.loads(request.body)
        keyword = req_dict['keyword']
        md_username = req_dict['md_username']
        # 目前web接口只提供 “福利社” 的红包id
        red_packet_id = 'J43lMyyodSXCal0QMer7'
        wx_user = WxUser.objects.filter(user__username=md_username).first()
        chatroom_list = ChatRoom.objects.filter(wx_user__username=wx_user.username, username__icontains=u"果粉街")
        if not chatroom_list:
            return HttpResponse(json.dumps({"ret": 0, "reason": "发单群为空"}))
        sign_rule = SignInRule()
        sign_rule.keyword = keyword
        sign_rule.red_packet_id = red_packet_id
        sign_rule.save()

        for chatroom in chatroom_list:
            sign_rule.chatroom.add(chatroom.id)
            sign_rule.save()

        return HttpResponse(json.dumps({"ret": 1, "reason": "添加红包口令成功"}))
