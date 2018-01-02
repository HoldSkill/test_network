# -*- coding: utf-8 -*-
import json
import thread
import time
import threading

from django.views.generic.base import View
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from ipad_weixin.send_msg_type import sendMsg
from ipad_weixin.models import WxUser, ChatRoom

import logging
logger = logging.getLogger('django_views')



wx_id = "wxid_cegmcl4xhn5w22"
chatroom_id = ["5761280027@chatroom", "6947816994@chatroom"]
data = ["http://md-oss.di25.cn/03a7d2d6-e5fa-11e7-9455-1c1b0d3e23eb.jpeg?x-oss-process=image/quality,Q_80",
        "http://md-oss.di25.cn/03a7d2d7-e5fa-11e7-9455-1c1b0d3e23eb.jpeg?x-oss-process=image/quality,Q_80",
        "http://md-oss.di25.cn/03a7d2d8-e5fa-11e7-9455-1c1b0d3e23eb.jpeg?x-oss-process=image/quality,Q_80",
        "http://md-oss.di25.cn/03a7d2d9-e5fa-11e7-9455-1c1b0d3e23eb.jpeg?x-oss-process=image/quality,Q_80",
        "http://md-oss.di25.cn/03a7d2da-e5fa-11e7-9455-1c1b0d3e23eb.jpeg?x-oss-process=image/quality,Q_80",
        ]

import thread

class TestSendGroupMsgView(View):
    @csrf_exempt
    def post(self, request):
        req_dict = json.loads(request.body)
        data = req_dict["data"]
        for chatroom in chatroom_id:
            # thread.start_new_thread(sendMsg, (wx_id, chatroom, data))
            time.sleep(10)
            logger.info("超时测试")

            # t = threading.Thread(target=sendMsg, args=(wx_id, chatroom, data))
            # t.start()
        return HttpResponse(json.dumps({"ret": 1}))




        # for i in range(1, 10):
        #     logger.warning("开启第{}个线程".format(i))
        #     t = threading.Thread(target=sendMsg, args=(wx_id, chatroom_id, data))
        #     t.start()
        #     # TODO：主线程需要阻塞，全部的线程才会开始发送，不然只会有少量的线程运行，其余线程在启动后就不知道去哪儿了
        #     time.sleep(1)
        # # sendMsg(wx_id, chatroom_id, data)
        # return HttpResponse(json.dumps({"ret": 1}))


class TestSendGroupMessageVIew(View):
    """
    接口： s-prod-04.qunzhu666.com/api/robot/test_send_group_msg/
    群发数据测试接口
    """
    @csrf_exempt
    def post(self, request):
        req_dict = json.loads(request.body)
        platform_id = req_dict['platform_id']
        data = req_dict['data']
        wxuser = WxUser.objects.get(username="wxid_3drnq3ee20fg22", user__first_name=platform_id)
        if not wxuser:
            return HttpResponse(json.dumps({"ret": 0, "resaon": "筛选平台login WxUser为空"}))
        chatroom_list = ChatRoom.objects.filter(wxuser=wxuser, wxuser_chatroom__is_send=True)
        if not chatroom_list:
            return HttpResponse(json.dumps({"ret": 0, "data": "生产群为空"}))
        for chatroom in chatroom_list:
            wx_id = wxuser.username
            chatroom_id = chatroom.username
            thread.start_new_thread(sendMsg, (wx_id, chatroom_id, data))
            time.sleep(10)
        return HttpResponse(json.dumps({"ret": 1, "data": "处理完成"}))