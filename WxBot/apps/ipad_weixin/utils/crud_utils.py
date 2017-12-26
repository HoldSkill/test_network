# coding:utf-8

"""
收发分离后，处理返回包所需的参数均要传入
"""
import json
import time
import pickle
from ipad_weixin.settings import red
from django.db import connection
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

    # @classmethod
    # def dispatch(cls, cmd):
    #     METHOD_MAP = {
    #         503: cls.check_qrcode_login,
    #         1111: cls.confirm_qrcode_login,
    #         205: cls.heart_beat,
    #         702: cls.auto_auth,
    #         138: cls.async_check,
    #         1002: cls.new_init,
    #         522: cls.send_text_msg,
    #         127: cls.send_voice_msg,
    #         110: cls.send_img_msg,
    #         9: cls.send_img_msg,
    #         222: cls.send_app_msg,
    #         551: cls.get_chatroom_detail,
    #         182: cls.get_contact,
    #         233: cls.GetA8Key
    #     }
    #     if cmd in METHOD_MAP.keys():
    #         return METHOD_MAP[cmd]

    # done
    class get_qrcode:
        @staticmethod
        def execute(buffers ,**kwargs):
            md_username = kwargs.get('md_username')
            try:
                Qrcode.save_qr_code(buffers, md_username)
            except Exception as e:
                logger.error(e)
            finally:
                connection.close()

    @staticmethod
    def check_qrcode_login(buffers ,**kwargs):
        pass

    @staticmethod
    def confirm_qrcode_login(buffers ,**kwargs):
        pass

    @staticmethod
    def heart_beat(buffers ,**kwargs):
        pass

    @staticmethod
    def auto_auth(buffers ,**kwargs):
        pass

    class async_check:

        @staticmethod
        def handle_contact(buffers ,**kwargs):
            msg_dict = buffers
            v_user = kwargs.get('v_user')
            try:
                contact, created = Contact.objects.get_or_create(username=msg_dict['UserName'])
                contact.save()
                if created:
                    wx_user = WxUser.objects.get(username=v_user.userame)
                    contact.wx_user.add(wx_user.id)
                    contact.update_from_mydict(msg_dict)
                    contact.save()
            except Exception as e:
                logger.error(e)
            finally:
                connection.close()

        @staticmethod
        def handle_msg(buffers ,**kwargs):
            msg_dict = buffers
            try:
                message, created = Message.objects.get_or_create(msg_id=msg_dict['MsgId'])
                message.update_from_msg_dict(msg_dict)
                message.save()
            except Exception as e:
                logger.error(e)
            finally:
                connection.close()

        @staticmethod
        def get_chatroom_name_and_owner(buffers, **kwargs):
            msg_dict = buffers

            chatroom_name = ''
            chatroom_owner = ''
            if '@chatroom' in msg_dict['FromUserName']:
                chatroom_name = msg_dict['FromUserName']
                chatroom_owner = msg_dict['ToUserName']
            if '@chatroom' in msg_dict['ToUserName']:
                chatroom_name = msg_dict['ToUserName']

            return (chatroom_name, chatroom_owner)

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
            logger.info("{0}: 微信返回错误, 第{1}次图片发送失败".format(nickname, send_num))
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