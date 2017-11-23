# coding:utf8

import os
import django
os.environ.update({"DJANGO_SETTINGS_MODULE": "fuli.settings"})
django.setup()

from django.utils.encoding import iri_to_uri

from ipad_weixin.models import Qrcode, ChatRoom, ChatroomMember, WxUser, PlatformInformation
from django.contrib.auth.models import User

import urllib
import requests
import json
import re

import logging
logger = logging.getLogger('weixin_bot')


def filter_keyword_rule(nickname, wx_id, msg_dict):
    data = get_Msgdata(msg_dict)
    if data:
        return data
    keyword = find_buy_start(msg_dict['Content'])

    if (keyword and keyword is not '') or ("我剁手都要" in msg_dict['Content']):
        if "我剁手都要" in msg_dict['Content']:
            keyword = msg_dict['Content']
        customer_service_list = WxUser.objects.filter(username=wx_id, is_customer_server=True)
        if wx_id in [wx_user.username for wx_user in customer_service_list]:
            return

        gid = ''
        at_user_id = ''
        at_user_nickname = ''
        # 情况分类1 机器人自己说找XX
        if msg_dict['FromUserName'] == wx_id and "@chatroom" in msg_dict['ToUserName']:
            gid = msg_dict['ToUserName']
            wxuser = WxUser.objects.filter(username=msg_dict["FromUserName"]).order_by('-id').first()

            at_user_nickname = '@' + wxuser.nickname
        # 情况分类2 群成员说找XX
        elif "@chatroom" in msg_dict['FromUserName'] and msg_dict['ToUserName'] == wx_id:
            gid = msg_dict['FromUserName']
            at_user_id = msg_dict['Content'].split(':')[0]
            at_user_db = ChatroomMember.objects.filter(username=at_user_id).first()
            at_user_nickname = '@' + at_user_db.nickname

        chatroom = ChatRoom.objects.get(wxuser_chatroom__is_search=True, username=gid, wxuser__username=wx_id)
        logger.info("WxUser: {0}, 群: {1}, 进入商品搜索".format(nickname, chatroom.nickname))
        if chatroom:
            try:
                # TODO: filter条件问题，是否会出现username ==null的情况
                auth_user = User.objects.filter(wxuser__username=wx_id, first_name__isnull=False,
                                                username__isnull=False).order_by('-id').first()
                md_username = auth_user.username
                platform_id = auth_user.first_name
                # TODO: 这里应该有一个服务能够接受所有平台的请求并进行相应的处理，用以判断搜索的url
                # 目前先暂时用一个特定的接口来做
                request_data = {
                    "md_username": md_username,
                    "at_user_nickname": at_user_nickname,
                    "keyword": keyword,
                    "platform_id": platform_id
                }
                # 该平台所对应处理搜索View的url
                host_url = PlatformInformation.objects.get(platform_id=platform_id, is_customer_server=False).host_url
                response = requests.post(host_url, data=json.dumps(request_data))
                response_dict = json.loads(response.content)
                data = response_dict["data"]

                from ipad_weixin.send_msg_type import sendMsg
                sendMsg(wx_id, gid, data, at_user_nickname)
            except Exception as e:
                logger.error(e)
                logger.error("WxUser: {0}, 群: {1}, 商品搜索出现异常".format(nickname, chatroom.nickname))
        else:
            logger.info("WxUser: {0}搜索群为空".format(nickname))


def find_buy_start(s):
    # 一个中文字符等于三个字节 允许有十个字符
    if len(s) < 40:
        lst = s.split("找")
        if len(lst) > 1:
            return lst[1]
        lst = s.split("买")
        if len(lst) > 1:
            return lst[1]
    return False

# 从消息中获取url以及邀请者
def get_Msgdata(msg_dict):
    if msg_dict.get('MsgType', 0) != 49:
        return ""
    title = re.findall('<title><!\[CDATA\[(.*?)\]\]></title>', msg_dict['Content'])
    try:
        if not title[0].encode('utf-8').endswith('群聊'):
            return ""
    except:
        return ""
    pattern = r'.*?<url>(.*?)</url>.*?'
    res = re.findall(pattern, msg_dict['Content'])
    if res:
        url = re.findall('CDATA\[(.*?)\]\].*', res[0])
        if url:
            return {'url': url[0], 'fromuser': msg_dict['FromUserName']}







if __name__ == "__main__":
    msg_dict = {u'Status': 3,
                u'PushContent': u'\u964c : 找跳绳',
                u'FromUserName': u'6610815091@chatroom',
                u'MsgId': 1650542751,
                u'ImgStatus': 1,
                u'ToUserName': u'wxid_ozdmesmnpy5g22',
                u'MsgSource': u'<msgsource>\n\t<silence>0</silence>\n\t<membercount>5</membercount>\n</msgsource>\n',
                u'Content': u'wxid_9zoigugzqipj21:\n\u627e\u62d6\u978b',
                u'MsgType': 1, u'ImgBuf': None,
                u'NewMsgId': 8330079787334973454,
                u'CreateTime': 1508208110
                }
    wx_id = 'wxid_ozdmesmnpy5g22'
    filter_keyword_rule(wx_id, msg_dict)

"""
u'wxid_fykxqh566gxh22:\n【我剁手都要买的宝贝（达尔优LM101游戏鼠标有线牧马人USB台式机电脑笔记本家用办公女生），快来和我一起瓜分红I包】http://a.npupu.com/h.wKS7ig 点击链接，再选择浏览器打开；或复制这条信息￥gkpP0SRzFYr￥后打开👉手淘👈'
"""