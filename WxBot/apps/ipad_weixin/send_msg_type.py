# -*- coding: utf-8 -*-
import cPickle as pickle
import random
import time
from ipad_weixin.weixin_bot import WXBot
from ipad_weixin import weixin_bot
from ipad_weixin.models import Qrcode, WxUser, ChatRoom, SignInRule, PushRecord


def sendMsg(wx_id, chatroom_id, data, at_user_id=''):
    v_user_pickle = weixin_bot.red.get('v_user_' + wx_id)
    v_user = pickle.loads(v_user_pickle)
    wx_bot = WXBot()

    # 添加随机延时
    random_seed = random.randint(0, 5)
    time.sleep(random_seed)
    for item in data:
        if item.startswith("http"):
            result = wx_bot.send_img_msg(chatroom_id, v_user, item)
            if not result:
                break
        elif item.startswith("<appmsg"):
            wx_bot.send_app_msg(v_user, chatroom_id, item)
        else:
            if '\n' in item or '\r' in item:
                item = item.replace('\r', '\\r').replace('\n', '\\n')
            wx_bot.send_text_msg(chatroom_id, item, v_user, at_user_id)


