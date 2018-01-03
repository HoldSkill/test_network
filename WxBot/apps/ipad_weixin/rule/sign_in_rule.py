# coding:utf8

import os
import django
os.environ.update({"DJANGO_SETTINGS_MODULE": "WxBot.settings"})
django.setup()

from django.db import connection
from ipad_weixin.models import ChatRoom, SignInRule, ChatroomMember, Rule_Chatroom
import time
import re
from ipad_weixin.send_msg_type import sendMsg
import requests
import json
import threading

import logging
logger = logging.getLogger("weixin_bot")


def filter_sign_in_keyword(wx_id, msg_dict):
    # 首先判断content中是否包含红包口令
    if ':' in msg_dict['Content']:
        content = msg_dict['Content'].split(':')[1].strip()
    else:
        content = msg_dict['Content']

    signin_db = SignInRule.objects.all()
    keywords = [signin.keyword for signin in signin_db]

    speaker_id = ''
    chatroom = ''
    from_user_id = ''
    # 粗略判断
    if content in keywords:
        # 机器人自己在群里说话
        if '@chatroom' in msg_dict['ToUserName']:
            speaker_id = msg_dict['FromUserName']  # 微信ID
            from_user_id = msg_dict['ToUserName']  # 群ID
            chatroom = ChatRoom.objects.get(username=msg_dict['ToUserName'])
        # 群成员签到
        if '@chatroom' in msg_dict['FromUserName']:
            chatroom = ChatRoom.objects.get(username=msg_dict['FromUserName'])
            speaker_id = msg_dict['Content'].split(':')[0]
            from_user_id = msg_dict['FromUserName']
        logger.info("WxUser: {0}, 群 {1} 进入签到".format(wx_id, chatroom.nickname))
        # 判断该群的签到规则是否为keyword
        try:
            rule_chatroom = Rule_Chatroom.objects.filter(sign_in_rule__keyword=content, chatroom=chatroom).first()
            # sign_rule_db = SignInRule.objects.filter(keyword=content, chatroom=chatroom).first()

            if rule_chatroom:
                speaker = ChatroomMember.objects.filter(username=speaker_id).first()
                speaker_name = speaker.nickname
                data = {
                    "speaker_nick_name_trim": get_nick_name_trim(speaker_name),
                    "time": {"$date": int(round(time.time() * 1000))},
                    "speaker_head_img_url": speaker.small_head_img_url,
                    "speaker_nick_name_emoji_unicode": get_nick_name_emoji_unicode(speaker_name),
                    "from_user_id": from_user_id,
                    "speaker_id": speaker_id
                }

                # url = 'http://s-poc-02.qunzhu666.com/365/api/clockin/'
                url = 'http://s-poc-02.qunzhu666.com/sign/'
                request_url = url + rule_chatroom.red_packet_id
                json_data = json.dumps(data)
                response = requests.post(request_url, data=json_data)
                if not response.content:
                    return
                body = json.loads(response.content)

                reaction_list = body['reaction_list']
                for reaction in reaction_list:
                    if reaction['type'] == 'text':
                        text = reaction['content']
                        send_text = "@" + speaker_name + '\\n' + text

                        # 发送文字消息
                        text_thread = threading.Thread(target=sendMsg, args=(wx_id, from_user_id, [send_text], speaker_id))
                        text_thread.setDaemon(True)
                        text_thread.start()

                    elif reaction['type'] == 'img':

                        img_url = reaction['content']
                        if img_url:
                            # 发送图片信息
                            img_thread = threading.Thread(target=sendMsg, args=[wx_id, from_user_id, [img_url]])
                            img_thread.setDaemon(True)
                            img_thread.start()
        except Exception as e:
            logger.error(e)
            logger.error("WxUser: {0}, 群 {1} 签到发生异常, 原因: {2}".format(wx_id, chatroom.nickname, e.message))
        finally:
            connection.close()

    else:
        pass


def get_nick_name_emoji_unicode(nick_name):
    return convert_emoji_from_html_to_unicode(nick_name)

def get_nick_name_trim(nick_name):
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u'\u2600-\u26FF\u2700-\u27BF'
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', get_nick_name_emoji_unicode(nick_name))


def convert_emoji_from_html_to_unicode(s):
    """
    将网页的emoji编码转化为unicode
    """
    pattern = '<span class="emoji emoji(.{4,5})"></span>'
    rst = re.search(pattern, s)
    if rst is None:  # No emoji found.
        return s
    emoji_id = rst.group(1)
    emoji_unicode = ('\U' + '0' * (8 - len(emoji_id)) + emoji_id).decode('raw-unicode-escape')
    return re.sub(pattern, emoji_unicode, s)

if __name__ == '__main__':
    wx_id = "wxid_cegmcl4xhn5w22"
    # 机器人自己在群里说话
    msg_dict = {
        u'Status': 3,
        u'PushContent': u'',
        u'FromUserName': u'wxid_cegmcl4xhn5w22',
        u'MsgId': 1650554654,
        u'ImgStatus': 1,
        u'ToUserName': u'6610815091@chatroom',
        u'MsgSource': u'',
        u'Content': u'签到测试',
        u'MsgType': 1,
        u'ImgBuf': None,
        u'NewMsgId': 1582711830148784131,
        u'CreateTime': 1508809888
    }

    filter_sign_in_keyword(wx_id, msg_dict)



