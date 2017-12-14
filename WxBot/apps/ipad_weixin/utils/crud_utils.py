# coding:utf-8

"""
收发分离后，处理返回包所需的参数均要传入
"""
import json
import time
import pickle
from ipad_weixin.settings import red
from ipad_weixin.models import WxUser, Contact, Message, Qrcode, BotParam, ChatRoom, \
    ChatroomMember, Wxuser_Chatroom
# from ipad_weixin.utils.grpc_utils import grpc_decode
from ipad_weixin.utils.oss_utils import beary_chat

import logging
logger = logging.getLogger('weixin_bot')

"""
业务逻辑处理器。
对WXBot中的方法，除get_qrcode必须同步返回外，
其余业务逻辑的操作均由收包触发
使用dispatch方法选择处理逻辑
"""
class CRUDHandler(object):
    def __init__(self):
        pass

    @classmethod
    def dispatch(cls, cmd):
        METHOD_MAP = {
            503: cls.check_qrcode_login,
            1111: cls.confirm_qrcode_login,
            205: cls.heart_beat,
            702: cls.auto_auth,
            138: cls.async_check,
            1002: cls.new_init,
            522: cls.send_text_msg,
            127: cls.send_voice_msg,
            110: cls.send_img_msg,
            9: cls.send_img_msg,
            222: cls.send_app_msg,
            551: cls.get_chatroom_detail,
            182: cls.get_contact,
            233: cls.GetA8Key
        }
        if cmd in METHOD_MAP.keys():
            return METHOD_MAP[cmd]

    # kwargs中必须有：
    # 1.req或rsp，用于向grpc请求解码  2.nickname, 用于追踪
    # todo: 要按qrcode_rsp的状态进行轮询，直到状态正确或超时为止，须设计回调机制
    @staticmethod
    def check_qrcode_login(buffers ,**kwargs):
        # resp = kwargs.get('rsp')
        # md_username = kwargs.get('md_username')
        # uuid = kwargs.get('uuid')
        #
        # resp = grpc_decode(resp, buffers)
        # payloads = resp.baseMsg.payloads
        # if 'unpack err' not in payloads:
        #     qr_code = json.loads(payloads)
        # if qr_code['Status'] is 2:
        #     try:
        #         qr_code_db, created = Qrcode.objects.get_or_create(uuid=uuid)
        #         qr_code_db.update_from_qrcode(qr_code)
        #         qr_code_db.md_username = md_username
        #         qr_code_db.save()
        #     except Exception as e:
        #         logger.error(e)
        #     # 成功登陆
        #     return qr_code
        # elif qr_code['Status'] is 0:
        #     # 未扫描等待扫描
        #     pass
        # elif qr_code['Status'] is 1:
        #     # 已扫描未确认
        #     pass
        # elif qr_code['Status'] is 4:
        #     # 已取消扫描
        #     pass
        # # 等待5s再检测
        # # time.sleep(5)
        # # 如果3分钟都没有正常返回status 2 返回False
        # # if (datetime.datetime.now() - start_time).seconds >= 60 * 3:
        # #     self.wechat_client.close_when_done()
        # return False
        pass

    # todo: 设计回调
    # todo: 该方法将调用new_init和async_check
    @staticmethod
    def confirm_qrcode_login(buffers ,**kwargs):
        pass

    # todo: 该方法将调用async_check
    @staticmethod
    def heart_beat(buffers ,**kwargs):
        v_user = kwargs.get('v_user')

    # todo: 须处理关闭socket的回调
    @staticmethod
    def auto_auth(buffers ,**kwargs):
        # resp = grpc_decode(kwargs.get('resp'), buffers)
        # nickname = kwargs.get('nickname')
        # if resp.baseMsg.ret == 0:
        #     user = resp.baseMsg.user
        #     logger.info("%s: 二次登录成功!" % nickname)
        #     red.set('v_user_'+nickname, pickle.dumps(user))
        #     return True
        # elif resp.baseMsg.ret in (-100, -2023):
        #     logger.info("%s: 二次登录失败，请重新扫码" % nickname)
        #     try:
        #         payload = resp.baseMsg.payloads
        #         start = "<Content><![CDATA["
        #         end = "]]></Content>"
        #         ret_reason = payload[payload.find(start) + len(start):payload.find(end)]
        #     except Exception as e:
        #         logger.error(e)
        #         ret_reason = "未知"
        #     logger.info("{0}: 已掉线,原因:{1}".format(nickname, ret_reason))
        #     beary_chat("{0}: 已掉线,原因:{1}".format(nickname, ret_reason))
        #     # self.wechat_client.close_when_done()
        #     return 'Logout'
        # else:
        #     logger.info("二次登陆未知返回码")
        #     ret_code = resp.baseMsg.ret
        #     beary_chat("{0}: 已掉线,未知返回码:{1}".format(nickname, ret_code))
        #     logger.info("{0}: 已掉线,未知返回码:{1}".format(nickname, ret_code))
        #     # self.wechat_client.close_when_done()
        #     return False
        pass

    @staticmethod
    def async_check(buffers ,**kwargs):
        pass

    @staticmethod
    def new_init(buffers ,**kwargs):
        pass

    @staticmethod
    def send_text_msg(buffers ,**kwargs):
        pass

    @staticmethod
    def send_voice_msg(buffers ,**kwargs):
        pass

    @staticmethod
    def send_img_msg(buffers ,**kwargs):
        nickname = kwargs.get('nickname')
        send_num = kwargs.get('send_num')
        if not buffers:
                logger.info("{} : buffers为空".format(nickname))
        elif ord(buffers[16]) != 191:
            logger.info("{}: 微信返回错误".format(nickname))
            logger.info("{0}第{1}次图片发送失败".format(nickname, send_num))
        else:
            logger.info("{0} 第 {1} 次发送图片成功！".format(nickname, send_num))

    @staticmethod
    def send_app_msg(buffers ,**kwargs):
        pass

    @staticmethod
    def get_chatroom_detail(buffers ,**kwargs):
        pass

    @staticmethod
    def get_contact(buffers ,**kwargs):
        pass

    @staticmethod
    def GetA8Key(buffers ,**kwargs):
        pass