# -*- coding: utf-8 -*-
import time
import json
import requests

import logging
logger = logging.getLogger("weixin_bot")

# 在每天的 8:00, 14:00, 20:00向群组发送搜索文案
# 较为精确的时间采用crontab完成

# 获取登录MMT的所有username列表
server_host = "http://s-prod-04.qunzhu666.com:10024/"
local_host = "http://127.0.0.1:10024/"

url = server_host + "api/robot/platform_user_list?platform_id=make_money_together"
send_msg_url = server_host + "api/robot/send_msg/"
text = "Hello，告诉大家一个很神奇的事情，在群里直接发送“找XXX（例如：找手机）”，我就会给你所有你想要的优惠券噢～"

# TODO: 需要写一个crontab粗来
def main():
    response = requests.get(url)
    req_dict = json.loads(response.content)
    login_user_list = req_dict.get("login_user_list", "")
    if not login_user_list:
        logger.info("login_user_list为空")
    for user_object in login_user_list:
        user = user_object["user"]
        data = {
            "md_username": user,
            "data": [text],
            "search_text": "search_text"
        }
        send_msg_response = requests.post(send_msg_url, data=json.dumps(data))

if __name__ == '__main__':
    main()