# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import time
import pickle
import thread
import random
import datetime

from django.http import HttpResponse
from django.views.generic.base import View
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.utils import timezone
from django.contrib.auth.models import User

from ipad_weixin.serializer import RuleChatRoomSerializer
from ipad_weixin.weixin_bot import WXBot
from ipad_weixin.models import WxUser, ChatRoom, SignInRule, PlatformInformation, Wxuser_Chatroom, \
    ForbiddenChatRoom, Rule_Chatroom
from ipad_weixin.send_msg_type import sendMsg
from ipad_weixin.utils.oss_utils import beary_chat
from ipad_weixin.settings import red


import logging
logger = logging.getLogger('django_views')


class SendMsgView(View):
    """
    接口： http://s-prod-04.qunzhu666.com:10024/api/robot/send_msg/
    格式:
        {
            "md_username": "",
            "data": ["http:", "<appmsg...", "text", ...]
        }
    """
    @csrf_exempt
    def post(self, request):
        req_dict = json.loads(request.body)
        md_username = req_dict.get("md_username", "")
        is_search_text = req_dict.get("search_text", "")

        if not md_username:
            return HttpResponse(json.dumps({"ret": 0, "reason": "sendMsg md_username不能为空"}))

        data = req_dict.get("data", "")
        if not data:
            return HttpResponse(json.dumps({"ret": 0, "reason": "待发送数据为空"}))

        wxuser_list = WxUser.objects.filter(user__username=md_username, login=1, is_customer_server=False)
        if not wxuser_list:
            return HttpResponse(json.dumps({"ret": 0, "reason": "wxuser_list 为空"}))
        for wxuser in wxuser_list:
            if is_search_text:
                chatroom_list = ChatRoom.objects.filter(wxuser=wxuser, wxuser_chatroom__is_send=False,
                                                        wxuser_chatroom__is_search=True)
                if not chatroom_list:
                    platform_id = User.objects.get(username=md_username).first_name
                    beary_chat("平台：%s, %s 单一搜索群为空，搜索文案发送失败" % (platform_id, wxuser.nickname))
                    continue
                    # 这里如果直接返回的话，那么接下的wxuser将得不到处理
                    # return HttpResponse(json.dumps({"ret": 0, "data": "发单群为空"}))

                for chatroom in chatroom_list:
                    wx_id = wxuser.username
                    chatroom_id = chatroom.username
                    thread.start_new_thread(sendMsg, (wx_id, chatroom_id, data))
            else:
                chatroom_list = ChatRoom.objects.filter(wxuser=wxuser, wxuser_chatroom__is_send=True)
                if not chatroom_list:
                    platform_id = User.objects.get(username=md_username).first_name
                    beary_chat("平台：%s, %s 生产群为空" % (platform_id, wxuser.nickname))
                    continue
                    # 这里如果直接返回的话，那么接下的wxuser将得不到处理
                    # return HttpResponse(json.dumps({"ret": 0, "data": "发单群为空"}))

                for chatroom in chatroom_list:
                    # 一个群一个线程去处理
                    wx_id = wxuser.username
                    chatroom_id = chatroom.username
                    thread.start_new_thread(sendMsg, (wx_id, chatroom_id, data))
        connection.close()
        return HttpResponse(json.dumps({"ret": 1, "data": "处理完成"}))


class PlatformUserList(View):
    """
    接口: http://s-prod-04.qunzhu666.com:10024/api/robot/platform_user_list?platform_id=xxx
    筛选登录了该平台所有的用户，返回手机号以及对应的机器人列表
    """
    def get(self, request):
        platform_id = request.GET.get("platform_id", "")
        if not platform_id:
            return HttpResponse(json.dumps({"ret": 0, "Error": "未知平台id"}))
        login_user_db = User.objects.filter(wxuser__login=1, wxuser__is_customer_server=False, first_name=platform_id)
        if not login_user_db:
            return HttpResponse(json.dumps({"ret": 0, "Error": "筛选{}平台User为空".format(platform_id)}))

        # 这里是否应该再去遍历一层， 拿到该用户的nickname呢？

        login_user_list = []
        for login_user in login_user_db:
            username = login_user.username
            wxuser_db = WxUser.objects.filter(user__username=username, login=1, is_customer_server=False)
            wxuser_nickname_list = [wxuser.nickname for wxuser in wxuser_db]
            data = {"user": username, "wxuser_list": wxuser_nickname_list}
            login_user_list.append(data)
        """
        {
            "login_user_list":[
                    {"user": "smart", "wxuser_list": ["樂阳", "渺渺的"]}，
                    {"user": "keyerror", ......}
            ]
        }
        """
        return HttpResponse(json.dumps({"ret": 1, "login_user_list": login_user_list}))


class AddProductionChatroom(View):
    @csrf_exempt
    def post(self, request):
        """
        添加生产群
        数据类型：josn
        格式：
        {
            "wx_username": "wxid_......"
            "chatroom_list": ["chatroom.username",......]
        }
        接口: http://s-prod-04.qunzhu666.com:10024/api/robot/add_production_chatroom/
        本地: localhost:10024/robot/add_production_chatroom/
        """
        # TODO: 使用wx_id来作为筛选条件，而不是md_username
        req_dict = json.loads(request.body)
        chatroom_list = req_dict["chatroom_list"]
        wx_username = req_dict["wx_username"]
        if not chatroom_list:
            return HttpResponse(json.dumps({"ret": 0, "reason": "chatroom_list为空"}))
        for chatroom_username in chatroom_list:
            # 用户总群禁止添加
            try:
                forbidden_chatroom = ForbiddenChatRoom.objects.get(username=chatroom_username)
                if forbidden_chatroom:
                    continue
            except Exception as e:
                wxuser_chatroom = Wxuser_Chatroom.objects.get(
                    chatroom__username=chatroom_username, wxuser__username=wx_username
                )

                wxuser_chatroom.is_send = True
                wxuser_chatroom.is_search = True
                wxuser_chatroom.save()
        return HttpResponse(json.dumps({"ret": 1, "reason": "添加生产群成功"}))


class RemoveProductionChatroom(View):
    @csrf_exempt
    def post(self, request):
        """
        移除生产群
        接口: http://s-prod-04.qunzhu666.com:10024/api/robot/add_production_chatroom/
        本地: localhost:10024/robot/remove_production_chatroom/
        """
        req_dict = json.loads(request.body)
        chatroom_list = req_dict["chatroom_list"]
        wx_username = req_dict["wx_username"]
        if not chatroom_list:
            return HttpResponse(json.dumps({"ret": 0, "reason": "chatroom_list为空"}))
        for chatroom_username in chatroom_list:
            wxuser_chatroom = Wxuser_Chatroom.objects.get(
                chatroom__username=chatroom_username, wxuser__username=wx_username
            )
            wxuser_chatroom.is_send = False
            wxuser_chatroom.save()

        return HttpResponse(json.dumps({"ret": 1, "reason": "删除生产群成功"}))


class DefineSignRule(View):
    """
    为生产群定义签到红包口令
    格式：
        {
            "md_username":
            "keyword": "签到口令",
            "platform_id":
        }
    接口： http://s-prod-04.qunzhu666.com:10024/api/robot/define_sign_rule/
    本地： localhost:10024/api/robot/define_sign_rule/
    """
    @csrf_exempt
    def post(self, request):
        req_dict = json.loads(request.body)
        keyword = req_dict['keyword']
        md_username = req_dict['md_username']
        platform_id = req_dict['platform_id']

        try:
            red_packet_id = PlatformInformation.objects.get(platform_id=platform_id, is_customer_server=False).red_packet_id
            wxuser_list = WxUser.objects.filter(user__username=md_username)

            # 只有在生产群才能够添加签到规则
            chatroom_list_ = []
            for wxuser in wxuser_list:
                chatroom = ChatRoom.objects.filter(wxuser=wxuser, wxuser_chatroom__is_send=True)
                chatroom_list_ += chatroom
            chatroom_list = list(set(chatroom_list_))
        except Exception as e:
            return HttpResponse(json.dumps({"ret": 0, "reason": "未登录机器人"}))
        if not chatroom_list:
            return HttpResponse(json.dumps({"ret": 0, "reason": "生产群为空"}))
        sign_rule, created = SignInRule.objects.get_or_create(keyword=keyword)

        sign_rule_list = []
        for chatroom in chatroom_list:
            try:
                defaults = {
                    "chatroom": chatroom,
                    "sign_in_rule": sign_rule,
                    "red_packet_id": red_packet_id
                }
                sign_in_rule, created = Rule_Chatroom.objects.update_or_create(chatroom=chatroom, defaults=defaults)
                sign_rule_list.append(sign_in_rule)
            except Exception as e:
                logger.error(e)
                return HttpResponse(json.dumps({"ret": 0, "reason": "添加或更新失败"}))
        serializer = RuleChatRoomSerializer(sign_rule_list, many=True)
        return HttpResponse(json.dumps({"result": serializer.data}))

    def get(self, request):
        md_username = request.GET.get("md_username", "")
        if not md_username:
            return HttpResponse(json.dumps({"ret": 0, "reason": "username为空"}), status=400)
        sign_in_rule = SignInRule.objects.filter(chatroom__wxuser__user__username=md_username)
        sign_in_rule_db = Rule_Chatroom.objects.filter(chatroom__wxuser__user__username=md_username)
        serializer = RuleChatRoomSerializer(sign_in_rule_db, many=True)
        return HttpResponse(json.dumps({"result": serializer.data}))


class UpdateOrDeleteSignRule(View):
    """
    接口： /api/robot/chatroom_rule/

    """
    @csrf_exempt
    def post(self, request):
        req_dict = json.loads(request.body)
        md_username = req_dict['md_username']
        platform_id = req_dict['platform_id']
        keyword = req_dict.get("keyword", "")
        chatroom_username = req_dict.get("chatroom_username", "")

        if not md_username:
            return HttpResponse(json.dumps({"ret": 0, "reason": "username为空"}), status=400)

        if keyword and chatroom_username:
            # 创建或更新某个群的签到口令
            try:
                sign_rule, created = SignInRule.objects.get_or_create(keyword=keyword)
                red_packet_id = PlatformInformation.objects.get(platform_id=platform_id).red_packet_id
                defaults = {
                    "sign_in_rule": sign_rule,
                    "chatroom": ChatRoom.objects.get(username=chatroom_username),
                    "red_packet_id": red_packet_id
                }
                rule_chatroom, created = Rule_Chatroom.objects.update_or_create(chatroom__username=chatroom_username,
                                                                   defaults=defaults)
            except Exception as e:
                logger.error(e)
                return HttpResponse(json.dumps({"ret": 0, "reason": "chatroom_username不合法"}), status=400)
        elif chatroom_username:
            # 删除某个群的签到口令
            rule_chatroom = Rule_Chatroom.objects.filter(chatroom__username=chatroom_username).delete()
        sign_in_rule_db = Rule_Chatroom.objects.filter(chatroom__wxuser__user__username=md_username)
        serializer = RuleChatRoomSerializer(sign_in_rule_db, many=True)
        return HttpResponse(json.dumps({"result": serializer.data}))


class SendGroupMessageVIew(View):
    """
    接口： s-prod-04.qunzhu666.com/api/robot/send_group_msg/
    向所有已登录mmt平台用户的所有生产群中发送消息， 群发消息中不应含有任何关于pid等信息
    """
    @csrf_exempt
    def post(self, request):
        req_dict = json.loads(request.body)
        platform_id = req_dict['platform_id']
        data = req_dict['data']
        wxuser_list = WxUser.objects.filter(login=1, is_customer_server=False, user__first_name=platform_id)
        if not wxuser_list:
            return HttpResponse(json.dumps({"ret": 0, "resaon": "筛选平台login WxUser为空"}))
        for wxuser in wxuser_list:
            chatroom_list = ChatRoom.objects.filter(wxuser=wxuser, wxuser_chatroom__is_send=True)
            if not chatroom_list:
                continue
            for chatroom in chatroom_list:
                wx_id = wxuser.username
                chatroom_id = chatroom.username
                thread.start_new_thread(sendMsg, (wx_id, chatroom_id, data))
                # TODO: 这里必须延时至少1s，所有的线程才会启动并且执行相应的代码
                time.sleep(1)
        connection.close()
        return HttpResponse(json.dumps({"ret": 1, "data": "处理完成"}))


class SendMMTMessageView(View):
    def get(self, request):
        md_username = request.GET.get('md_username')
        wxuser = WxUser.objects.filter(user__username=md_username).first()

        if wxuser:
            chatroom_list = ChatRoom.objects.filter(wxuser__username=wxuser.username, nickname__contains=u'MMT一起赚-用户总群')
            if not chatroom_list:
                return HttpResponse(json.dumps({"ret": 0, "reason": "用户不在用户总群中！"}))
            else:
                l = random.randint(0, len(chatroom_list)-1)
                chatroom = chatroom_list[l]
                text = (u'我有新的订单啦～',)
                wx_id = wxuser.username
                sendMsg(wx_id, chatroom.username, text)
                return HttpResponse(json.dumps({"ret": 1, "data": "发送订单信息完成"}))
        return HttpResponse(json.dumps({"ret": 0, "data": "用户无效哦"}))


class GetRoomQrcode(View):
    def post(self, request):
        req_dict = json.loads(request.body)
        wx_id = req_dict['wx_id']
        chatroom_id = req_dict['chatroom_id']
        v_user_pickle = red.get('v_user_' + wx_id)
        v_user = pickle.loads(v_user_pickle)
        if v_user:
            chatroom = ChatRoom.objects.filter(username=chatroom_id, wxuser__username=wx_id).first()
            if not chatroom:
                return HttpResponse(json.dumps({"ret": 0, "reason": "用户不在该群中，请检查参数！"}))
            else:
                wxbot = WXBot()
                oss_path = wxbot.get_room_qrcode(v_user, chatroom_id)
                if not oss_path:
                    return HttpResponse(json.dumps({"ret": 0, "reason": "机器人小小未登录"}))
                response_data = {"qrcode_url": oss_path, "chatroom_name": chatroom.nickname, "ret": 1}
                return HttpResponse(json.dumps(response_data), content_type="application/json")
        return HttpResponse(json.dumps({"ret": 0, "data": "用户无效哦"}))

















