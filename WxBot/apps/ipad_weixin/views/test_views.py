# -*- coding: utf-8 -*-
import json
from memory_profiler import profile
from django.views.generic.base import View
from django.http import HttpResponse
from ipad_weixin.send_msg_type import sendMsg
from django.views.decorators.csrf import csrf_exempt
import thread
import time


wx_id = "wxid_cegmcl4xhn5w22"
chatroom_id = "6610815091@chatroom"
data = ["http://md-oss.di25.cn/288ed4e4-e179-11e7-b4f6-1c1b0d3e23eb.jpeg?x-oss-process=image/quality,q_65",
        "http://md-oss.di25.cn/288ed4e4-e179-11e7-b4f6-1c1b0d3e23eb.jpeg?x-oss-process=image/quality,q_65",
        "http://md-oss.di25.cn/288ed4e4-e179-11e7-b4f6-1c1b0d3e23eb.jpeg?x-oss-process=image/quality,q_65"]


class TestSendGroupMsgView(View):
    @csrf_exempt
    def post(self, request):
        req_dict = json.loads(request.body)
        data = req_dict["data"]
        for i in range(1, 1000):
            thread.start_new_thread(sendMsg, (wx_id, chatroom_id, data))

        return HttpResponse(json.dumps({"ret": 1}))

