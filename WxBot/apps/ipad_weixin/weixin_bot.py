# -*- coding: utf-8 -*-

import sys
defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)

import os

import sys
b_path = os.path.abspath("..")
# b_path = '/home/may/work/taobaoke_weixinbot/WxBot'
sys.path.append(b_path)

import base64
import json
import pickle
import threading
import time
import urllib2
import datetime
import requests
import re
from PIL import Image
from io import BytesIO

import django
os.environ.update({"DJANGO_SETTINGS_MODULE": "WxBot.settings"})
django.setup()

import settings
from WechatProto_pb2 import WechatMsg, BaseMsg, User
from settings import CONST_PROTOCOL_DICT
from settings import red

from grpc_module import grpc_client

from ipad_weixin.utils import common_utils
from ipad_weixin.tcp_module import WechatClient
from ipad_weixin.tcp_module.Wechat_client_modify import WechatClientTest
from ipad_weixin.utils import grpc_utils
from ipad_weixin.utils import oss_utils
from ipad_weixin.utils.common_utils import get_time_stamp, read_int, int_list_convert_to_byte_list, char_to_str, \
    check_buffer_16_is_191, get_public_ip, check_grpc_response, get_md5
from ipad_weixin.utils.wechatmsg_utils import MsgReq
from ipad_weixin.utils.crud_utils import CRUDHandler
from ipad_weixin.rule import action_rule

from django.contrib.auth.models import User as AuthUser
from django.db import connection
from ipad_weixin.models import WxUser, Contact, Message, Qrcode, BotParam, Img, ChatRoom, \
    ChatroomMember, Wxuser_Chatroom

from ipad_weixin.voice_deque import VoiceDeque

import logging
logger = logging.getLogger('weixin_bot')


class WXBot(object):
    def __init__(self):
        self.long_host = settings.LONG_SERVER
        self.short_host = settings.SHORT_SERVER
        # self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)
        self.wechat_client = None
        # 随机MD5
        self.deviceId = get_md5(str(time.time()))
        self.newinitflag = True
        # 是否在同步中
        self.__is_async_check = False
        self._lock = threading.Lock()

        # 图片重试次数
        self.__retry_num = 1
        self._auto_retry = 0
        self.nickname = None
        # self.inviting = False
        # self.start_time = datetime.datetime.now()

    def set_user_context(self, wx_username):
        # TODO：self.wx_username 不该在这初始化，待修改
        """为什么不应该在这里初始化？"""
        # 数据库中查询
        self.wx_username = wx_username
        bot_param = BotParam.objects.filter(username=wx_username).first()
        if bot_param:
            self.long_host = bot_param.long_host
            self.short_host = bot_param.short_host
        self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)

    def set_user_login(self, wx_username):
        self.wx_username = wx_username
        user_db = WxUser.objects.filter(username=self.wx_username).first()

        if user_db:
            self.nickname = user_db.nickname
            user_db.login = 1
            user_db.save()
            logger.info("%s: 重置用户login成功" % self.nickname)
            return True
        else:
            logger.info("%s: 重置用户login失败，wx_username不存在" % self.wx_username)
            return False

    def open_notify_callback(self):
        # 注册回调
        self.wechat_client.register_notify(self.process_notify_package)

    def process_notify_package(self, data):
        # 接收到notify包时的回调处理
        cmd = common_utils.read_int(data, 8)
        logger.info("%s: 接收到cmd为%s的notify消息" % (self.nickname, cmd))
        if cmd == 318:
            print "cmd 318"
            # 这里decode出来的都是微信的官网的html，所以没必要print出来了
            # v_user = pickle.loads(red.get('v_user_' + self.wx_username))
            # if v_user is not None:
            #     threading.Thread(target=self.decode_cmd_318, args=(v_user, data,)).start()

        if data is not None and len(data) >= 4:
            selector = common_utils.read_int(data, 16)
            if selector > 0:
                logger.info("{0}: selector:{1} 即将进行线程同步".format(self.nickname, selector))
                # print "selector:{0} start sync thread".format(selector)
                if selector >= 1000000000:
                    if self.wechat_client.connected:
                        self.wechat_client.close_when_done()
                        self._auto_retry += 1
                        red.set('v_user_heart_' + self.wx_username, 0)
                        logger.info("{}: selector异常，值为{}，可能用户执行下线，尝试二次登录".format(self.nickname, selector))

                # TODO：在 set_user_context 中定义的wx_username, 这么写不好, 待修改
                elif self.wx_username is not None and self.wx_username != "":
                    if self._lock.acquire():
                        # 确保只有一个线程在执行async_check，否则会接受多次相同的消息
                        if not self.__is_async_check:
                            self.__is_async_check = True
                            self._lock.release()
                        else:
                            logger.info("%s: ----------已有线程执行async_check，跳过async_check---------" % self.nickname)
                            # print "*********skip async check*********"
                            self._lock.release()
                            return

                    # 拉取消息之前先查询是否是登陆状态
                    # 因为用户ipad登陆的同时登陆其他平台，socket仍然会收到notify包

                    user_db = WxUser.objects.filter(username=self.wx_username).first()
                    is_login = user_db.login
                    v_user = pickle.loads(red.get('v_user_' + self.wx_username))

                    if is_login:
                        # bot = WXBot()

                        # bot_param = BotParam.objects.filter(username=v_user.userame).first()
                        # if bot_param:
                        #     bot.long_host = bot_param.long_host
                        #     bot.wechat_client = WechatClient.WechatClient(bot.long_host, 80, True)
                        # starttime = datetime.datetime.now()

                        res = self.async_check(v_user)
                        # self.start_time = datetime.datetime.now()

                        if res is False:
                            logger.info("%s: 线程执行同步失败" % v_user.nickname)
                        elif res is 'ERROR' and self._auto_retry == 29:
                            self._auto_retry += 1
                            logger.info("%s: 即将退出机器人" % v_user.nickname)
                            red.set('v_user_heart_' + self.wx_username, 0)
                            # self.wechat_client.close_when_done()
                            # self.logout_bot(v_user)
                        elif res is 'ERROR' and self._auto_retry >= 0:
                            logger.info("%s: 线程同步返回微信错误，尝试重启心跳" % v_user.nickname)
                            oss_utils.beary_chat("{}: 线程同步返回微信错误，尝试重启心跳".format(v_user.nickname))
                            self._auto_retry += 1
                            red.set('v_user_heart_' + self.wx_username, 0)
                            # self.wechat_client.close_when_done()
                        else:
                            logger.info("%s: 线程执行同步成功" % v_user.nickname)
                        # bot.wechat_client.close_when_done()
                    else:
                        logger.info("%s login为0！" % v_user.nickname)
                    self.__is_async_check = False
            else:
                logger.info("%s: selector小于等于0，未执行线程同步" % self.nickname)
        else:
            logger.info("%s: 未收到有效数据，未执行线程同步" % self.nickname)

    def logout_bot(self, v_user):
        # 退出机器人，并非退出微信登陆
        user_db = WxUser.objects.filter(username=v_user.userame).first()
        user_db.login = 0
        user_db.save()
        logger.info("%s: 退出机器人，当前login为%s" % (user_db.nickname, user_db.login))

    """ use MsgReq & CRUD
    GOOD"""
    def get_qrcode(self, md_username):
        """获取qrcode"""
        self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)
        # self.wechat_client = WechatClientTest(self.long_host, 80, True)
        self.deviceId = get_md5(md_username)

        qrcode_req = MsgReq(502, deviceId=self.deviceId)

        qrcode_rsp = grpc_client.send(qrcode_req)
        check_grpc_response(qrcode_rsp.baseMsg.ret)
        (grpc_buffers, seq) = grpc_utils.get_seq_buffer(qrcode_rsp)

        if not grpc_buffers:
            logger.info("%s: grpc返回错误" % md_username)
            return

        data = self.wechat_client.sync_send_and_return(grpc_buffers)

        qrcode_req.baseMsg.cmd = -502
        qrcode_req.baseMsg.payloads = char_to_str(data)
        qrcode_rsp = grpc_client.send(qrcode_req)

        buffers = qrcode_rsp.baseMsg.payloads
        # 保存二维码图片
        qr_code = json.loads(buffers)
        imgData = base64.b64decode(qr_code['ImgBuf'])
        uuid = qr_code['Uuid']

        # 地址规则
        # http://md-bot-service.oss-cn-shenzhen.aliyuncs.com/wxpad/uuid.png
        # http://md-bot-service.oss-cn-shenzhen.aliyuncs.com/wxpad/Q6l7utrwLk2SQWl0WRwJ.png
        # 上传二维码图片到图床中 id为uuid
        try:
            oss_path = oss_utils.put_object_to_oss("wxpad/" + uuid + ".png", imgData)
            logger.info("oss_path is: {}".format(oss_path))
            return oss_path, qrcode_rsp, self.deviceId, uuid
        except Exception as e:
            logger.error(e)
            return
        finally:
            CRUDHandler.get_qrcode.execute(buffers=qr_code, md_username=md_username)

    """use MsgReq"""
    def check_qrcode_login(self, qrcode_rsp, device_id, md_username):
        """
        检测扫描是否登陆
        :param qr_code:
        :return:
        """
        buffers = qrcode_rsp.baseMsg.payloads
        qr_code = json.loads(buffers)
        uuid = qr_code['Uuid']
        notify_key_str = base64.b64decode(qr_code['NotifyKey'].encode('utf-8'))
        long_head = qrcode_rsp.baseMsg.longHead
        start_time = datetime.datetime.now()
        self.deviceId = device_id

        while qr_code['Status'] is not 2:
            # 构造扫描确认请求
            # check_qrcode_grpc_req = WechatMsg(
            #     token=CONST_PROTOCOL_DICT['machine_code'],
            #     version=CONST_PROTOCOL_DICT['version'],
            #     timeStamp=get_time_stamp(),
            #     iP=get_public_ip(),
            #     baseMsg=BaseMsg(
            #         cmd=503,
            #         longHead=long_head,
            #         payloads=str(uuid),
            #         user=User(
            #             sessionKey=int_list_convert_to_byte_list(CONST_PROTOCOL_DICT['random_encry_key']),
            #             deviceId=self.deviceId,
            #             maxSyncKey=notify_key_str
            #         )
            #     )
            # )
            check_qrcode_grpc_req = MsgReq(503, long_head=long_head, uuid=uuid, deviceId=self.deviceId, notify_key_str=notify_key_str)

            checkqrcode_grpc_rsp = grpc_client.send(check_qrcode_grpc_req)
            (grpc_buffers, seq) = grpc_utils.get_seq_buffer(checkqrcode_grpc_rsp)
            if not grpc_buffers:
                logger.info("grpc返回错误")
                return False

            buffers = self.wechat_client.sync_send_and_return(grpc_buffers)

            if not buffers:
                logger.info("check_qrcode_login buffers为空")
                return False

            if ord(buffers[16]) != 191:
                logger.info("微信返回错误")
                return False

            checkqrcode_grpc_rsp.baseMsg.cmd = -503
            checkqrcode_grpc_rsp.baseMsg.payloads = char_to_str(buffers)
            checkqrcode_grpc_rsp_2 = grpc_client.send(checkqrcode_grpc_rsp)
            payloads = checkqrcode_grpc_rsp_2.baseMsg.payloads

            if 'unpack err' not in payloads:
                qr_code = json.loads(payloads)

            if qr_code['Status'] is 2:
                try:
                    qr_code_db, created = Qrcode.objects.get_or_create(uuid=uuid)
                    qr_code_db.update_from_qrcode(qr_code)
                    qr_code_db.md_username = md_username
                    qr_code_db.save()
                except Exception as e:
                    logger.error(e)
                # 成功登陆
                return qr_code
            elif qr_code['Status'] is 0:
                # 未扫描等待扫描
                pass
            elif qr_code['Status'] is 1:
                # 已扫描未确认
                pass
            elif qr_code['Status'] is 4:
                # 已取消扫描
                pass
            # 等待5s再检测

            time.sleep(5)
            # 如果3分钟都没有正常返回status 2 返回False
            if (datetime.datetime.now() - start_time).seconds >= 60 * 3:
                self.wechat_client.close_when_done()
                return False

    """use MsgReq"""
    def confirm_qrcode_login(self, qr_code, md_username, keep_heart_beat):
        # 重置longHost

        # 微信确认登陆模块

        UUid = common_utils.random_uuid(md_username)
        DeviceType = common_utils.random_devicetpye(md_username)
        print UUid
        print DeviceType
        payLoadJson = "{\"Username\":\"" + qr_code['Username'] + "\",\"PassWord\":\"" + qr_code[
            'Password'] + "\",\"UUid\":\"" + UUid + "\",\"DeviceType\":\"" + DeviceType + "\"}"

        qrcode_login_req = MsgReq(1111, deviceId=self.deviceId, payLoadJson=payLoadJson)

        qrcode_login_rsp = grpc_client.send(qrcode_login_req)
        (grpc_buffers, seq) = grpc_utils.get_seq_buffer(qrcode_login_rsp)

        if not grpc_buffers:
            logger.info('%s: grpc返回错误' % qr_code['Nickname'])
            return False

        buffers = self.wechat_client.sync_send_and_return(grpc_buffers)
        if not buffers:
            logger.info("%s: buffers为空" % qr_code['Nickname'])
            return False

        if ord(buffers[16]) != 191:
            logger.info("%s: 微信返回错误" % qr_code['Nickname'])
            return False

        qrcode_login_rsp.baseMsg.cmd = -1001
        qrcode_login_rsp.baseMsg.payloads = char_to_str(buffers)
        qrcode_login_rsp = grpc_client.send(qrcode_login_rsp)
        bot_param_db = BotParam.objects.filter(username=qr_code['Username']).first()
        if bot_param_db is None:
            BotParam.save_bot_param(
                qr_code['Username'], self.deviceId,
                qrcode_login_rsp.baseMsg.longHost,
                qrcode_login_rsp.baseMsg.shortHost
            )
        else:
            BotParam.update_bot_param(
                bot_param_db, qr_code['Username'], self.deviceId,
                qrcode_login_rsp.baseMsg.longHost,
                qrcode_login_rsp.baseMsg.shortHost
            )

        if qrcode_login_rsp.baseMsg.ret == -301:
            # 返回-301代表重定向
            self.long_host = qrcode_login_rsp.baseMsg.longHost
            self.short_host = qrcode_login_rsp.baseMsg.shortHost
            self.wechat_client.close_when_done()
            self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)
            return -301
        elif qrcode_login_rsp.baseMsg.ret == 0:
            # 返回0代表登陆成功
            logger.info('%s 登录成功' % qr_code['Nickname'])
            oss_utils.beary_chat("%s 扫码完成，开启心跳中--%s" % (qr_code['Nickname'], time.asctime(time.localtime(time.time()))))

            # 将User赋值 //sahuxin
            v_user = qrcode_login_rsp.baseMsg.user

            try:
                wxuser, created = WxUser.objects.get_or_create(uin=v_user.uin)
                wxuser.update_wxuser_from_userobject(v_user)
                wxuser.uuid = UUid
                wxuser.device_type = DeviceType
                wxuser.save()
            except Exception as e:
                logger.error(e)

            red.set('v_user_' + str(v_user.userame), pickle.dumps(v_user))
            return True
        else:
            logger.info("qrcode_login_rsp.baseMsg.ret is {}".format(qrcode_login_rsp.baseMsg.ret))
            logger.info("{0}登录失败，原因是：{1}".format(qr_code['Nickname'], qrcode_login_rsp.baseMsg.payloads))
            self.wechat_client.close_when_done()
            return False

    def heart_beat(self, v_user):
        """
        30到60s的定时心跳包
        主要用来维持socket的链接状态
        :param v_user:
        :return:
        """
        sync_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=205,
                user=v_user
            )
        )
        sync_rsp = grpc_client.send(sync_req)
        (grpc_buffers, seq) = grpc_utils.get_seq_buffer(sync_rsp)

        if not grpc_buffers:
            logger.info('%s: grpc返回错误' % v_user.nickname)
            # self.wechat_client.close_when_done()
            return False

        buffers = self.wechat_client.sync_send_and_return(grpc_buffers)
        # print "heartbeat selector is", read_int(buffers, 16)
        if not buffers:
            logger.info("%s: buffers为空" % v_user.nickname)
            return False
        # while not buffers:
        #     buffers = self.wechat_client.get_packaget_by_seq(seq)

        if ord(buffers[16]) is not 191:
            selector = read_int(buffers, 16)
            if selector > 0:
                logger.info("%s: 心跳中准备同步", v_user.nickname)
                if self._lock.acquire():
                    # 确保只有一个线程在执行async_check，否则会接受多次相同的消息
                    if not self.__is_async_check:
                        self.__is_async_check = True
                        self._lock.release()
                    else:
                        logger.info("----------已有线程执行async_check，跳过async_check---------")
                        # print "*********skip async check*********"
                        self._lock.release()
                        return False
                if self.async_check(v_user) is False:
                    self.__is_async_check = False
                    return False
                self.__is_async_check = False
                return True

        return True

    def auto_auth(self, v_user, uuid, device_type, new_socket=True):
        """
        二次登陆
        只要redis里头存有正确的v_user 那么就能通过此方法再次登陆
        :param v_user:
        :param uuid:
        :param device_type:
        :param new_socket:
        :return:
        """

        pay_load = "{\"UUid\":\"" + uuid + "\",\"DeviceType\":\"" + device_type + "\"}"
        # pay_load['DeviceName'] = "Ipad客户端"
        # pay_load['ProtocolVer'] = 5
        auto_auth_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=702,
                user=v_user,
                payloads=pay_load.encode('utf-8')
            )
        )
        # for i in range(10):
        auto_auth_rsp = grpc_client.send(auto_auth_req)
        (grpc_buffers, seq) = grpc_utils.get_seq_buffer(auto_auth_rsp)

        if not grpc_buffers:
            logger.info("%s: grpc返回出错" % v_user.nickname)
            # self.wechat_client.close_when_done()
            return False

        buffers = self.wechat_client.sync_send_and_return(grpc_buffers, time_out=3, close_socket=new_socket)

        if not buffers:
            logger.info("%s: buffers为空" % v_user.nickname)
            return False

        # while not buffers:
        #     buffers = self.wechat_client.get_packaget_by_seq(seq)
        # 如果能正常返回auto_auth_rsp_2.baseMsg.ret，可把下面这段191的判断注释掉

        # if not self.wechat_client.check_buffer_16_is_191(buffers):
        if ord(buffers[16]) != 191:
            logger.info("%s: 微信返回出错" % v_user.nickname)
            # self.wechat_client.close_when_done()
            return False

        auto_auth_rsp.baseMsg.cmd = -702
        auto_auth_rsp.baseMsg.payloads = buffers
        auto_auth_rsp_2 = grpc_client.send(auto_auth_rsp)
        if auto_auth_rsp_2.baseMsg.ret == 0:
            user = auto_auth_rsp_2.baseMsg.user
            logger.info("%s: 二次登录成功!" % v_user.nickname)
            v_user_pickle = pickle.dumps(user)
            red.set('v_user_' + v_user.userame, v_user_pickle)
            return True
        elif auto_auth_rsp_2.baseMsg.ret == -100 or auto_auth_rsp_2.baseMsg.ret == -2023:
            logger.info("%s: 二次登录失败，请重新扫码" % v_user.nickname)

            ret_reason = ''
            try:
                payload = auto_auth_rsp_2.baseMsg.payloads
                start = "<Content><![CDATA["
                end = "]]></Content>"
                ret_reason = payload[payload.find(start) + len(start):payload.find(end)]
            except Exception as e:
                logger.error(e)
                ret_reason = "未知"

            logger.info("{0}: 已掉线,原因:{1}".format(v_user.nickname, ret_reason))
            oss_utils.beary_chat("{0}: 已掉线,原因:{1}".format(v_user.nickname, ret_reason))
            self.wechat_client.close_when_done()
            return 'Logout'
        else:
            logger.info("二次登陆未知返回码")
            ret_code = auto_auth_rsp_2.baseMsg.ret
            oss_utils.beary_chat("{0}: 已掉线,未知返回码:{1}".format(v_user.nickname, ret_code))
            logger.info("{0}: 已掉线,未知返回码:{1}".format(v_user.nickname, ret_code))
            self.wechat_client.close_when_done()
            return False

    """use MsgReq & CRUD"""
    def async_check(self, v_user, new_socket=True):
        """
        同步消息
        从微信服务器拉取新消息
        :param v_user:
        :param new_socket:
        :return:
        """
        self.start_time = datetime.datetime.now()
        while True:
            # sync_req = WechatMsg(
            #     token=CONST_PROTOCOL_DICT['machine_code'],
            #     version=CONST_PROTOCOL_DICT['version'],
            #     timeStamp=get_time_stamp(),
            #     iP=get_public_ip(),
            #     baseMsg=BaseMsg(
            #         cmd=138,
            #         user=v_user
            #     )
            # )
            sync_req = MsgReq(138, v_user=v_user)

            sync_rsp = grpc_client.send(sync_req)
            (grpc_buffers, seq) = grpc_utils.get_seq_buffer(sync_rsp)
            if not grpc_buffers:
                logger.info("%s: gprc返回错误" % v_user.nickname)
                return False

            buffers = self.wechat_client.sync_send_and_return(grpc_buffers, time_out=2 )

            if not buffers:
                logger.info("%s: buffers为空" % v_user.nickname)
                return False

            # 尝试重新登录
            if ord(buffers[16]) != 191:
                try:
                    ret = read_int(buffers, 18)
                    if ret == -13:
                        logger.info("%s: Session Time out 离线或用户取消登陆 执行二次登录" % v_user.nickname)
                        wx_user = WxUser.objects.get(username=v_user.userame)
                        UUid = wx_user.uuid
                        DeviceType = wx_user.device_type
                        print UUid
                        print DeviceType
                        if self.auto_auth(v_user, UUid, DeviceType, new_socket=new_socket) is True:
                            return True
                        else:
                            logger.info("%s: 执行二次登录失败， 即将退出机器人" % v_user.nickname)
                            oss_utils.beary_chat("%s: 执行二次登录失败， 即将退出机器人" % v_user.nickname)
                            self.wechat_client.close_when_done()
                            self.logout_bot(v_user)
                            return False
                    else:
                        logger.info("%s: 微信返回错误，即将退出机器人" % v_user.nickname)
                        oss_utils.beary_chat("%s: 微信返回错误，即将退出机器人" % v_user.nickname)
                        self.wechat_client.close_when_done()
                        self.logout_bot(v_user)
                        return 'ERROR'
                except Exception as e:
                    logging.error(e)
                    return
            # 正常处理消息
            else:
                logger.info("%s: 同步资料中" % v_user.nickname)
                sync_rsp.baseMsg.cmd = -138
                sync_rsp.baseMsg.payloads = char_to_str(buffers)
                sync_rsp = grpc_client.send(sync_rsp)
                # 刷新用户信息
                v_user = sync_rsp.baseMsg.user

                v_user_pickle = pickle.dumps(v_user)
                red.set('v_user_' + v_user.userame, v_user_pickle)

                msg_list = json.loads(sync_rsp.baseMsg.payloads)
                if msg_list is not None:
                    for msg_dict in msg_list:
                        # 如果群进行改名，会进到这个循环，导致contact中存储了群的信息
                        # 更新联系人
                        if msg_dict['MsgType'] == 2 and '@chatroom' not in msg_dict['UserName']:

                            CRUDHandler.async_check.handle_contact(msg_dict, v_user=v_user)

                        # 更新群相关内容
                        elif msg_dict.get('Status') is not None:
                            # 判断是否签到消息
                            try:
                                # 消息
                                data = action_rule.filter_keyword_rule(v_user.nickname, v_user.userame, msg_dict)
                                if data:
                                    data['v_user'] = v_user
                                    data['username'] = v_user.userame
                                    self.confirm_chatroom_invitation(v_user, data)
                                from rule.sign_in_rule import filter_sign_in_keyword
                                filter_sign_in_keyword(v_user.userame, msg_dict)
                            except Exception as e:
                                logger.error(e)

                            # 如果有好友发送消息，则进行存储

                            # 拉取群信息
                            # chatroom_name = ''
                            # chatroom_owner = ''
                            #
                            # if '@chatroom' in msg_dict['FromUserName']:
                            #     chatroom_name = msg_dict['FromUserName']
                            #     chatroom_owner = msg_dict['ToUserName']
                            #
                            # if '@chatroom' in msg_dict['ToUserName']:
                            #     chatroom_name = msg_dict['ToUserName']
                            chatroom_name, chatroom_owner = CRUDHandler.async_check.get_chatroom_name_and_owner(msg_dict)

                            if chatroom_name:
                                try:
                                    chatroom, created = ChatRoom.objects.get_or_create(username=chatroom_name)
                                    if chatroom_owner:
                                        chatroom.chat_room_owner = chatroom_owner
                                        chatroom.save()

                                    # 触发规则是什么？
                                    # 群与wxuser没有建立联系，群昵称为空，群成员为空
                                    if not ChatRoom.objects.filter(wxuser__username=v_user.userame, username=chatroom_name) \
                                            or not chatroom.nickname or not chatroom.chatroommember_set.all():
                                        self.get_contact(v_user, chatroom_name.encode('utf-8'))
                                    else:
                                        # 该群存在, 则可能是更改群名称、拉/踢人等。
                                        if msg_dict['Status'] == 4:
                                            self.update_chatroom_members(chatroom_name, v_user)
                                            # TODO: 目前存在某些问题，待解决。
                                            if u"邀请" in msg_dict['Content'] and \
                                                    Wxuser_Chatroom.objects.get(chatroom=chatroom, wxuser__username=v_user.userame).is_send:
                                                self.send_invited_message(msg_dict, v_user)
                                except Exception as e:
                                    logger.error(e)
                                finally:
                                    connection.close()
                            # try:
                            #     message, created = Message.objects.get_or_create(msg_id=msg_dict['MsgId'])
                            #     message.update_from_msg_dict(msg_dict)
                            #     message.save()
                            # except Exception as e:
                            #     logger.error(e)

                            CRUDHandler.async_check.handle_msg(msg_dict)
                        else:
                            print(msg_dict)
                else:
                    logger.info("%s: 同步资料完成" % v_user.nickname)
                    return True

    def send_invited_message(self, msg_dict, v_user):
        pattern = '.*邀请"(.*?)".*'
        content = msg_dict['Content'].encode("utf-8")
        nicakname_str = re.match(pattern, content, re.S)
        if nicakname_str:
            invited_nickname = nicakname_str.group(1)
            chatroom_member = ChatroomMember.objects.filter(nickname=invited_nickname).first()
            invited_member_id = chatroom_member.username

            message = "@" + invited_nickname + "\\n 嘿嘿，欢迎你的加入~[机智][机智]"
            self.send_text_msg(msg_dict['FromUserName'], message, v_user, at_user_id=invited_member_id)
            connection.close()

    def new_init(self, v_user, md_username, platform_id):
        """
        登陆初始化
        拉取通讯录联系人
        :param v_user:
        :return:
        """
        new_init_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=1002,
                user=v_user
            )
        )
        new_init_rsp = grpc_client.send(new_init_req)
        (grpc_buffers, seq) = grpc_utils.get_seq_buffer(new_init_rsp)

        if not grpc_buffers:
            logger.info("%s: grpc返回错误" % v_user.nickname)
            # self.wechat_client.close_when_done()
            return False

        buffers = self.wechat_client.sync_send_and_return(grpc_buffers, time_out=3)

        if not buffers:
            logger.info("%s: buffers为空" % v_user.nickname)
            return False

        # while not buffers:
        #     buffers = self.wechat_client.get_packaget_by_seq(seq)

        if ord(buffers[16]) != 191:
            logger.info("%s: 微信返回错误" % v_user.nickname)
            # self.wechat_client.close_when_done()
            return False

        new_init_rsp.baseMsg.cmd = -1002
        new_init_rsp.baseMsg.payloads = char_to_str(buffers)
        new_init_rsp = grpc_client.send(new_init_rsp)
        # 打印出同步消息的结构体
        # msg_list = json.loads(new_init_rsp.baseMsg.payloads)

        # wx_user = WxUser.objects.get(username=v_user.userame)

        v_user = new_init_rsp.baseMsg.user
        v_user_pickle = pickle.dumps(v_user)
        red.set('v_user_' + v_user.userame, v_user_pickle)
        if new_init_rsp.baseMsg.ret == 8888:
            try:
                # 初始化起始位置都是0
                # if self.contact_init(v_user, 0, 0):
                wxuser = WxUser.objects.get(username=v_user.userame)
                """
                这里的逻辑就只有这么简单吗？
                假设 136xxx 登录了star_chain，使用 樂阳 登录ipad， 会产生哪些附加产品？
                    auth_user表创建username=136xxx, first_name=platform_id, 并且添加WxUser的ManyToManyRelationship
                那么，136xxx如果想要登录 mmt 系统，并且用 mimi 登录ipad进行发单呢？
                    此时136xxx的first_name为 mmt， 原有的微信机器人会变为在 mmt 进行发单
                """
                user, created = AuthUser.objects.get_or_create(username=md_username)
                user.first_name = platform_id
                user.save()

                wxuser.user.add(user)
                wxuser.save()
                logger.info("%s 初始化成功！" % v_user.nickname)

            except Exception as e:
                logger.error(e)
                sys.exit(1)

            self.newinitflag = False
            # self.wechat_client.close_when_done()
            return True
        else:
            # self.wechat_client.close_when_done()
            self.new_init(v_user, md_username, platform_id)

    def contact_init(self, v_user, cur_wx_seq, cur_chatroom_seq):
        continue_flag = 1
        wx_id_list = []
        while continue_flag != 0:
            payLoadJson = json.dumps({"CurrentWxcontactSeq": cur_wx_seq,
                                      "CurrentChatRoomContactSeq": cur_chatroom_seq})
            init_contact_req = WechatMsg(
                token=CONST_PROTOCOL_DICT['machine_code'],
                version=CONST_PROTOCOL_DICT['version'],
                timeStamp=get_time_stamp(),
                iP=get_public_ip(),
                baseMsg=BaseMsg(
                    cmd=851,
                    user=v_user,
                    payloads=payLoadJson.encode('utf-8')
                )
            )
            init_contact_rsp = grpc_client.send(init_contact_req)
            body = init_contact_rsp.baseMsg.payloads
            buffers = requests.post("http://" + self.short_host + init_contact_rsp.baseMsg.cmdUrl, data=body).content
            if ord(buffers[0]) != 191:
                logger.info("%s: 微信返回错误" % v_user.nickname)
                return False
            init_contact_rsp.baseMsg.cmd = -851
            init_contact_rsp.baseMsg.payloads = buffers
            init_contact_rsp = grpc_client.send(init_contact_rsp)
            contact = json.loads(init_contact_rsp.baseMsg.payloads)

            try:
                temp = [user["Username"] for user in contact['UsernameLists']]
                wx_id_list.extend(temp)
            except BaseException:
                pass

            continue_flag = contact['ContinueFlag']
            cur_wx_seq = contact['CurrentWxcontactSeq']
            cur_chatroom_seq = contact['CurrentChatRoomContactSeq']

        # 一次只拉取25个用户的信息，待测试
        # print len(wx_id_list)
        for i in range(0, len(wx_id_list), 20):
            end = min(20, len(wx_id_list) - i)
            # print i, i+end-1
            if self.wechat_client.connected:
                self.get_contact(v_user, wx_id_list[i:i + end])
        logger.info("%s: 获取联系人完成！" % v_user.userame)
        return True

    def send_text_msg(self, user_name, content, v_user, at_user_id=''):
        """
        参考btn_SendMsg_Click
        :param user_name:
        :param content:
        :param at_user_list:
        :param v_user:
        :return:
        """

        bot_param = BotParam.objects.filter(username=v_user.userame).first()
        if bot_param:
            self.long_host = bot_param.long_host
            self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)
        payLoadJson = "{\"ToUserName\":\"" + user_name + "\",\"Content\":\"" + content + "\",\"Type\":0,\"MsgSource\":\"" + at_user_id + "\"}".encode('utf-8')
        # send_text_req = WechatMsg(
        #     token=CONST_PROTOCOL_DICT['machine_code'],
        #     version=CONST_PROTOCOL_DICT['version'],
        #     timeStamp=get_time_stamp(),
        #     iP=get_public_ip(),
        #     baseMsg=BaseMsg(
        #         cmd=522,
        #         user=v_user,
        #         payloads=payLoadJson.encode('utf-8')
        #     )
        # )
        send_text_req = MsgReq(522, v_user=v_user, payLoadJson=payLoadJson)
        send_text_rsp = grpc_client.send(send_text_req)

        (grpc_buffers, seq) = grpc_utils.get_seq_buffer(send_text_rsp)
        if not grpc_buffers:
            logger.info("%s: grpc返回错误" % v_user.nickname)

        buffers = self.wechat_client.sync_send_and_return(grpc_buffers)

        if not buffers:
            logger.info("%s: buffers为空" % v_user.nickname)
            self.wechat_client.close_when_done()
            return False
        if ord(buffers[16]) != 191:
            logger.info("%s: 微信返回错误" % v_user.nickname)
        else:
            logger.info('{0} 向 {1} 发送文字信息:成功'.format(v_user.nickname, user_name, content))
        self.wechat_client.close_when_done()
        connection.close()
        # return True

    def send_voice_msg(self, v_user, to_user_name, data=None):
        """
        发送语音 btn_SendVoice_Click
        :param v_user:
        :param url:
        :return:
        """

        bot_param = BotParam.objects.filter(username=v_user.userame).first()
        if bot_param:
            self.long_host = bot_param.long_host
            self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)
        if VoiceDeque.is_valid():
            data = base64.b64decode(VoiceDeque.get_voice())
        else:
            voice_path = '/home/may/Downloads/msg.amr'
            with open(voice_path, 'rb') as voice_file:
                data = voice_file.read()
        payload = {
            'ToUserName': to_user_name,
            'Offset': 0,
            'Length': len(data),
            'EndFlag': 1,
            'VoiceLength': 1000,
            'Data': base64.b64encode(data),
            'VoiceFormat': 4  # 4是silk
        }
        payload_json = json.dumps(payload)
        # payload_json = requests.post(url='http://192.168.0.173:9999/get-json',data={"to_user_name":to_user_name, "file_path":'ttt.amr'}).content
        send_voice_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=127,
                user=v_user,
                payloads=payload_json
            )
        )
        send_voice_rsp = grpc_client.send(send_voice_req)
        (grpc_buffers, seq) = grpc_utils.get_seq_buffer(send_voice_rsp)

        if not grpc_buffers:
            logger.info("%s: grpc返回错误" % v_user.nickname)

        buffers = self.wechat_client.sync_send_and_return(grpc_buffers)

        if not buffers:
            logger.info("%s: buffers为空" % v_user.nickname)
            self.wechat_client.close_when_done()
            return

        if ord(buffers[16]) != 191:
            logger.info("%s: 微信返回错误" % v_user.nickname)

        else:
            logger.info('{0} 向 {1} 发送语音:成功'.format(v_user.nickname, to_user_name))

        self.wechat_client.close_when_done()
        return

    """use MsgReq & Modify & CRUD
    GOOD"""
    def send_img_msg(self, user_name, v_user, url):
        """
        btn_SendMsgimg_Click
        :param user_name:
        :param v_user:
        :return:
        """
        bot_param = BotParam.objects.filter(username=v_user.userame).first()
        if bot_param:
            self.long_host = bot_param.long_host
            self.wechat_client = WechatClientTest(self.long_host, 80, True)
            if not self.wechat_client.be_init:
                return False
        connection.close()
        try:
            data = urllib2.urlopen(url).read()
        except BaseException:
            self.wechat_client.close_when_done()
            return False

        import random
        random_str = str(random.randint(0, 999))
        data = data + random_str

        # 图片压缩
        max_length = 250000
        if len(data) > max_length:
            img = Image.open(BytesIO(data))
            img_buffer = BytesIO()
            quality_rate = 60
            if "jpeg" in url or "jpg" in url:
                img.save(img_buffer, 'JPEG', quality=quality_rate)
            elif "png" in url:
                img.save(img_buffer, 'PNG', quality=quality_rate)
            data = img_buffer.getvalue()

        # 如果压缩后的图片仍然非常大，超过25次，则放弃改图片的发送
        if len(data) / 16553 > 25:
            self.wechat_client.close_when_done()
            return False

        # 起始位置
        start_pos = 0
        # 数据分块长度
        data_len = 16553
        # 总长度
        data_total_length = len(data)

        total_send_nums = -(-data_total_length / data_len)
        send_num = 1

        logger.info('preparing sent img to {0}, length {1}'.format(user_name, data_total_length))

        # 客户图像id
        client_img_id = v_user.userame + "_" + str(get_time_stamp())
        while start_pos != data_total_length:
            # 每次最多只传65535
            count = 0
            if data_total_length - start_pos > data_len:
                count = data_len
            else:
                count = data_total_length - start_pos
            upload_data = base64.b64encode(data[start_pos:start_pos + count])

            payLoadJson = {
                'ClientImgId': client_img_id.encode('utf-8'),
                'ToUserName': user_name.encode('utf-8'),
                'StartPos': start_pos,
                'TotalLen': data_total_length,
                'DataLen': len(data[start_pos:start_pos + count]),
                'Data': upload_data
            }
            pay_load_json = json.dumps(payLoadJson)

            img_msg_req = MsgReq(110, v_user=v_user, pay_load_json=pay_load_json)

            img_msg_rsp = grpc_client.send(img_msg_req)
            (grpc_buffers, seq) = grpc_utils.get_seq_buffer(img_msg_rsp)

            if not grpc_buffers:
                logger.info("%s: grpc返回错误" % v_user.nickname)

            # 传入func_name供回调
            func_name = sys._getframe().f_code.co_name
            self.wechat_client.asyn_send(grpc_buffers, {"nickname": v_user.nickname, "send_num": send_num, 'func': func_name})
            logger.info(
                '{0} 向 {1} 发送图片, 第 {3} 次, 共 {2} 次.'.format(v_user.nickname, user_name, total_send_nums, send_num))


            start_pos = start_pos + count
            send_num += 1
            time.sleep(1)
        self.wechat_client.close_when_done()
        connection.close()
        return True

    def retry_send_img(self, img_msg_req):
        img_msg_rsp = grpc_client.send(img_msg_req)
        (buffers, seq) = grpc_utils.get_seq_buffer(img_msg_rsp)
        buffers = self.wechat_client.sync_send_and_return(buffers, time_out=3)
        check_num = check_buffer_16_is_191(buffers)
        if check_num == 2:
            print('重发成功')
            return True
        else:
            print('重发失败')
            return False

    def search_contact(self, user_name, v_user):
        payLoadJson = "{\"Username\":\"" + user_name + "\"}"
        search_contact_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=106,
                user=v_user,
                payloads=payLoadJson.encode('utf-8')
            )
        )
        search_contact_rsp = grpc_client.send(search_contact_req)
        (grpc_buffers, seq) = grpc_utils.get_seq_buffer(search_contact_rsp)

        if not grpc_buffers:
            logger.info("%s gRPC buffers is None" % v_user.nickname)
        buffers = self.wechat_client.sync_send_and_return(grpc_buffers)

        check_num = check_buffer_16_is_191(buffers)
        if check_num == 0:
            logger.info('%s 查找联系人: buffer 为 None' % v_user.nickname)
        if check_num == 1:
            logger.info('%s 查找联系人: 得到错误的微信返回' % v_user.nickname)
        if check_num == 2:
            logger.info('%s 查找联系人: 成功' % v_user.nickname)

        search_contact_rsp.baseMsg.cmd = -106
        search_contact_rsp.baseMsg.payloads = char_to_str(buffers)
        payloads = grpc_client.send(search_contact_rsp)
        print(payloads)

    def update_chatroom_members(self, chatroom_name, v_user):
        chatroom = ChatRoom.objects.get(username=chatroom_name)
        group_members_details = self.get_chatroom_detail(v_user, chatroom_name)
        # 如果机器人被移出群聊，则将对应的关系删除
        if not group_members_details:
            wx_user = WxUser.objects.get(username=v_user.userame)
            try:
                user_chatroom = Wxuser_Chatroom.objects.get(chatroom=chatroom, wxuser=wx_user)
                Wxuser_Chatroom.delete(user_chatroom)
            except BaseException:
                pass
            return

        new_members_list = [member['Username'] for member in group_members_details]
        members_db = ChatroomMember.objects.filter(chatroom__username=chatroom_name)
        old_members_list = [member.username for member in members_db]

        # 踢人
        delete_members = set(old_members_list) - set(new_members_list)
        if delete_members:
            for delete_member in delete_members:
                delete_member_db = ChatroomMember.objects.get(username=delete_member,
                                                              chatroom__username=chatroom_name)
                delete_member_db.chatroom.remove(chatroom)
                delete_member_db.save()
            # 然后更新群成员的数量
            chatroom.member_nums = len(new_members_list)
            chatroom.save()

        # 拉人
        add_members = set(new_members_list) - set(old_members_list)
        if add_members:
            # 这里之所以用2层for循环嵌套是因为add_member仅仅是一个username,需要在group_members_details找到与之对应的dict，并进行更新
            for add_member in add_members:
                for group_member in group_members_details:
                    if add_member == group_member['Username']:
                        members_db, created = ChatroomMember.objects.get_or_create(username=group_member['Username'])
                        members_db.update_from_members_dict(group_member)
                        members_db.save()

                        members_db.chatroom.add(chatroom)
                        members_db.save()
                chatroom.member_nums = len(new_members_list)
                chatroom.save()

        else:
            # 修改群名称
            self.get_contact(v_user, chatroom_name.encode('utf-8'))
        connection.close()

    def get_chatroom_detail(self, v_user, room_id):
        """
        获取群的信息
        :param room_id:
        :param v_user:
        :return:
        """
        bot_param = BotParam.objects.filter(username=v_user.userame).first()
        if bot_param:
            self.short_host = bot_param.short_host
        payLoadJson = "{\"Chatroom\":\"" + room_id + "\"}".encode('utf-8')

        get_room_detail_req = MsgReq(551, v_user=v_user, payLoadJson=payLoadJson)

        get_room_detail_rsp = grpc_client.send(get_room_detail_req)

        body = get_room_detail_rsp.baseMsg.payloads

        buffers = requests.post("http://" + self.short_host + get_room_detail_rsp.baseMsg.cmdUrl, body)

        get_room_detail_rsp.baseMsg.cmd = -551
        get_room_detail_rsp.baseMsg.payloads = buffers.content
        get_room_detail_rsp = grpc_client.send(get_room_detail_rsp)
        buffers = get_room_detail_rsp.baseMsg.payloads
        buffers_dict = json.loads(buffers)

        member_details = buffers_dict["MemberDetails"]

        return member_details

    def send_app_msg(self, from_user, to_user, content):
        bot_param = BotParam.objects.filter(username=from_user.userame).first()
        if bot_param:
            self.long_host = bot_param.long_host
            self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)

        payLoadJson = {
            'ToUserName': to_user.encode('utf-8'),
            'AppId': "",
            'Type': 5,
            'Content': content
        }
        pay_load_json = json.dumps(payLoadJson)

        app_msg_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=222,
                user=from_user,
                payloads=pay_load_json.encode('utf-8'),
            )
        )
        app_msg_rsp = grpc_client.send(app_msg_req)

        (grpc_buffers, seq) = grpc_utils.get_seq_buffer(app_msg_rsp)
        if not grpc_buffers:
            logger.info("%s: grpc返回错误" % from_user.nickname)
            # self.wechat_client.close_when_done()
            return False

        buffers = self.wechat_client.sync_send_and_return(grpc_buffers)

        if not buffers:
            logger.info("%s: buffers为空" % from_user.nickname)
            return False

        if ord(buffers[16]) != 191:
            logger.info("%s: 微信返回错误" % from_user.nickname)
            return False

        else:
            logger.info('{0} 向 {1} 发送小程序:成功'.format(from_user.nickname, to_user))

        self.wechat_client.close_when_done()
        return True

    def get_contact(self, v_user, wx_id_list):
        """
        除了初始化，只有当出现更新的时候才会调用这个函数
        经过测试，wx一次最大接收20个wx_id
        :param wx_id_list:
            当获取单个联系人消息时，直接传入联系人wx_id即可
            想要获取群组的整体信息，传入群的id即可，xxxxx@chatroom
        :param v_user:
        :return:
        """
        wx_id_list = ','.join(wx_id_list) if not isinstance(wx_id_list, str) else wx_id_list
        payLoadJson = "{\"UserNameList\":\"" + wx_id_list + "\"}"

        contacts_req = MsgReq(182, v_user=v_user, payLoadJson=payLoadJson)

        get_contacts_rsp = grpc_client.send(contacts_req)
        (grpc_buffers, seq) = grpc_utils.get_seq_buffer(get_contacts_rsp)
        if not grpc_buffers:
            logger.info("%s: grpc返回错误" % v_user.nickname)
            self.wechat_client.close_when_done()
            return False

        buffers = self.wechat_client.sync_send_and_return(grpc_buffers)

        if not buffers:
            logger.info("%s: buffers为空" % v_user.nickname)
            return False

        if ord(buffers[16]) != 191:
            logger.info("%s: 微信返回错误" % v_user.nickname)
            self.wechat_client.close_when_done()
            return False

        get_contacts_rsp.baseMsg.cmd = -182
        get_contacts_rsp.baseMsg.payloads = buffers
        get_contacts_rsp = grpc_client.send(get_contacts_rsp)
        buffers = get_contacts_rsp.baseMsg.payloads
        json_buffers = json.loads(buffers.encode('utf-8'))
        wx_user = WxUser.objects.get(username=v_user.userame)
        for contact_data in json_buffers:
            try:
                if '@chatroom' in contact_data['UserName']:
                    chatroom, created = ChatRoom.objects.get_or_create(username=contact_data['UserName'])
                    chatroom.update_from_msg_dict(contact_data)
                    chatroom.save()
                    # print "更新群", contact_data['NickName']

                    Wxuser_Chatroom.objects.get_or_create(chatroom=chatroom, wxuser=wx_user)

                    chatroom_members_details = self.get_chatroom_detail(v_user, contact_data['UserName'])
                    if not chatroom_members_details:
                        try:
                            user_chatroom = Wxuser_Chatroom.objects.get(chatroom=chatroom, wxuser=wx_user)
                            Wxuser_Chatroom.delete(user_chatroom)
                        except BaseException:
                            pass
                        return

                    for members_dict in chatroom_members_details:
                        chatroom_member, created = ChatroomMember.objects.get_or_create(username=members_dict["Username"])
                        chatroom_member.update_from_members_dict(members_dict)
                        chatroom_member.save()

                        chatroom_member.chatroom.add(chatroom.id)
                        chatroom_member.save()

                else:
                    if not contact_data.get('Ticket', 1):
                        contact, created = Contact.objects.get_or_create(username=contact_data['UserName'])
                        contact.update_from_mydict(contact_data)
                        contact.save()

                        contact.wx_user.add(wx_user.id)
                        contact.save()
                        # print "更新", contact_data['NickName']
                    else:
                        # 可能用户开启了好友验证，可以将该用户删除
                        stranger = Contact.objects.filter(username=contact_data['UserName']).first()
                        if stranger:
                            # 删除好友关系
                            wx_user.contact_set.remove(stranger)
                            stranger.delete()
                        #     print "删除", contact_data['NickName']
                        # print "ticket not 0!", contact_data['NickName']
                        pass
                connection.close()
            except Exception as e:
                logger.error(e)
                connection.close()
        logger.info('%s 获取联系人成功' % v_user.nickname)
        return True

    def create_chatroom(self, v_user, wx_id_list):
        """
        建群        private void btn_CreateChatRoom_Click(object sender, EventArgs e)
        :param v_user:
        :param wx_id_list:
        :return:
        """
        bot_param = BotParam.objects.filter(username=v_user.userame).first()
        if bot_param:
            self.long_host = bot_param.long_host
            self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)
        wx_id_list = ','.join(wx_id_list)
        # payload_json = "{\"Membernames\":\"hiddensorrow\", \"jzwbh99\"}"
        payload_json = "{\"Membernames\":\"" + wx_id_list + "\"}"
        create_chatroom_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=119,
                user=v_user,
                payloads=payload_json.encode('utf-8')
            )
        )
        create_chatroom_rsp = grpc_client.send(create_chatroom_req)
        (grpc_buffers, seq) = grpc_utils.get_seq_buffer(create_chatroom_rsp)
        if not grpc_buffers:
            logger.info("%s: grpc返回错误" % v_user.nickname)
            self.wechat_client.close_when_done()
            return False

        buffers = self.wechat_client.sync_send_and_return(grpc_buffers)

        if not buffers:
            logger.info("%s: buffers为空" % v_user.nickname)
            self.wechat_client.close_when_done()
            return False

        if ord(buffers[16]) != 191:
            logger.info("%s: 微信返回错误" % v_user.nickname)
            self.wechat_client.close_when_done()
            return False

        create_chatroom_rsp.baseMsg.cmd = -119
        create_chatroom_rsp.baseMsg.payloads = buffers
        create_chatroom_rsp = grpc_client.send(create_chatroom_rsp)
        chatroom_detail = json.loads(create_chatroom_rsp.baseMsg.payloads)
        chatroom_id = chatroom_detail['Roomeid']
        self.wechat_client.close_when_done()
        return chatroom_id

    def modify_chatroom_name(self, v_user, chatroom_id, room_name):
        bot_param = BotParam.objects.filter(username=v_user.userame).first()
        if bot_param:
            self.short_host = bot_param.short_host
        payload_json = "{\"Cmdid\":27,\"ChatRoom\":\"" + chatroom_id + "\",\"Roomname\":\"" + room_name + "\"}"
        modify_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=681,
                user=v_user,
                payloads=payload_json.encode('utf-8')
            )
        )
        modify_rsp = grpc_client.send(modify_req)
        (buffers, seq) = grpc_utils.get_seq_buffer(modify_rsp)
        buffers = requests.post("http://" + self.short_host + modify_rsp.baseMsg.cmdUrl, data=buffers)
        self.wechat_client.close_when_done()
        return check_buffer_16_is_191(buffers)

    def invite_chatroom(self, v_user, chatroom_id, wx_id):
        """
        邀请进群:
        向指定用户发送群名片进行邀请
        :param v_user:
        :param chatroom_id:
        :param wx_id:
        :return:
        """
        bot_param = BotParam.objects.filter(username=v_user.userame).first()
        if bot_param:
            self.short_host = bot_param.short_host
        payloadJson = "{\"ChatRoom\":\"" + chatroom_id + "\",\"Username\":\"" + wx_id + "\"}"
        req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=610,
                user=v_user,
                payloads=payloadJson.encode('utf-8')
            )
        )
        rsp = grpc_client.send(req)
        (buffers, seq) = grpc_utils.get_seq_buffer(rsp)
        buffers = requests.post("http://" + self.short_host + rsp.baseMsg.cmdUrl, data=buffers)

        # 似乎每次登陆后的返回都不一样
        if not ord(buffers.text[0]) == 191:
            logger.info("invite_chatroom_member 返回码{0}".format(ord(buffers.text[0])))
        return True

    def add_chatroom_member(self, v_user, chatroom_id, wx_id):
        """
        添加微信群成员为好友 btn_AddChatRoomMember_Click
        :param v_user:
        :param wxid:
        :return:
    """
        bot_param = BotParam.objects.filter(username=v_user.userame).first()
        if bot_param:
            self.long_host = bot_param.long_host
            self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)
        payloadJson = "{\"Roomeid\":\"" + chatroom_id + "\",\"Membernames\":\"" + wx_id + "\"}"
        req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=120,
                user=v_user,
                payloads=payloadJson.encode('utf-8')
            )
        )

        rsp = grpc_client.send(req)
        (buffers, seq) = grpc_utils.get_seq_buffer(rsp)
        buffers = self.wechat_client.sync_send_and_return(buffers)
        check_buffer_16_is_191(buffers)
        rsp.baseMsg.cmd = -120
        rsp.baseMsg.payloads = char_to_str(buffers)
        payloads = grpc_client.send(rsp)

    def delete_chatroom_member(self, v_user, chatroom_id, wx_id):
        """
        踢出微信群 btn_DelChatRoomUser_Click
        :param v_user:
        :param wxid:
        :return:
        """
        bot_param = BotParam.objects.filter(username=v_user.userame).first()
        if bot_param:
            self.short_host = bot_param.short_host

        payloadJson = "{\"ChatRoom\":\"" + chatroom_id + "\",\"Username\":\"" + wx_id + "\"}"
        req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=179,
                user=v_user,
                payloads=payloadJson.encode('utf-8')
            )
        )

        rsp = grpc_client.send(req)
        (buffers, seq) = grpc_utils.get_seq_buffer(rsp)
        buffers = requests.post("http://" + self.short_host + rsp.baseMsg.cmdUrl, buffers)
        # 检测buffers[0] == 191
        if not ord(buffers.text.encode('utf-8')[0]):
            print "delete_chatroom_member 未知包"
            return False
        else:
            return True

    def decode_cmd_318(self, v_user, data):
        bot_param = BotParam.objects.filter(username=v_user.userame).first()
        if bot_param:
            self.short_host = bot_param.short_host
            self.long_host = bot_param.long_host
            self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)

        # send notify_req
        notify_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=-318,
                user=v_user,
                payloads=data
            )
        )
        notify_rsp = grpc_client.send(notify_req)
        body = notify_rsp.baseMsg.payloads.encode('utf-8')
        add_msg_digest = json.loads(body)
        print add_msg_digest
        payload_dict = {
            "ChatroomId": add_msg_digest['ChatRoomId'],
            "MsgSeq": add_msg_digest['NewMsgSeq']
        }
        payload_dict_json = json.dumps(payload_dict)

        # get chatroom req
        get_chatroom_msg_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=805,
                user=v_user,
                payloads=payload_dict_json.encode('utf-8')
            )
        )
        get_chatroom_msg_rsp = grpc_client.send(get_chatroom_msg_req)
        body = get_chatroom_msg_rsp.baseMsg.payloads
        upload_url = get_chatroom_msg_rsp.baseMsg.cmdUrl
        buffers = requests.post("http://" + self.short_host + upload_url, data=body)
        print buffers.text

        if buffers is None or buffers.text.encode('utf-8')[0] == 191:
            # TODO:hextostr
            print ("unknown package:{0}".format(buffers))
            return False

        # send grpc and decode again
        get_chatroom_msg_rsp.baseMsg.cmd = -805
        get_chatroom_msg_rsp.baseMsg.payloads = buffers.text.encode('utf-8')
        get_chatroom_msg_rsp = grpc_client.send(get_chatroom_msg_rsp)
        buffers = get_chatroom_msg_rsp.baseMsg.payloads
        print buffers
        return True

    def check_and_confirm_and_load(self, qrcode_rsp, device_id, md_username, platform_id):
        qr_code = self.check_qrcode_login(qrcode_rsp, device_id, md_username)
        starttime = datetime.datetime.now()
        if qr_code is not False:
            if self.confirm_qrcode_login(qr_code, md_username, keep_heart_beat=False) == -301:
                oss_utils.beary_chat("%s 进入check_and_confirm_and_load -301" % md_username)
                if self.confirm_qrcode_login(qr_code, md_username, keep_heart_beat=False):
                    v_user_pickle = red.get('v_user_' + str(qr_code['Username']))
                    v_user = pickle.loads(v_user_pickle)
                    self.new_init(v_user, md_username, platform_id)
                    if not self.newinitflag:
                        v_user = pickle.loads(red.get('v_user_' + str(qr_code['Username'])))
                        while not self.async_check(v_user):
                            if (datetime.datetime.now() - starttime).seconds >= 100:
                                return False
                            time.sleep(3)

                        heart_status = red.get('v_user_heart_' + str(qr_code['Username']))
                        """
                        heart_status: 0  用户下线
                                      1  用户在线
                                      2  用户心跳终止等待重启
                                      3  用户心跳终止不等待重启
                        """
                        if heart_status:
                            if int(heart_status) is not 1:
                                red.set('v_user_heart_' + str(qr_code['Username']), 0)
                                from ipad_weixin.heartbeat_manager import HeartBeatManager
                                HeartBeatManager.begin_heartbeat(v_user.userame, md_username)
                            else:
                                logger.info("%s: 心跳已经存在" % md_username)
                                oss_utils.beary_chat("%s: 心跳已经存在，无需启动心跳" % md_username)

                        else:
                            red.set('v_user_heart_' + str(qr_code['Username']), 0)
                            from ipad_weixin.heartbeat_manager import HeartBeatManager
                            HeartBeatManager.begin_heartbeat(v_user.userame, md_username)
                        return True
                else:
                    logger.info("GG 重新登录吧大兄弟")

            if self.confirm_qrcode_login(qr_code, md_username, keep_heart_beat=False):
                oss_utils.beary_chat("%s 未进入check_and_confirm_and_load -301" % md_username)
                v_user_pickle = red.get('v_user_' + str(qr_code['Username']))
                v_user = pickle.loads(v_user_pickle)
                self.new_init(v_user, md_username, platform_id)
                if not self.newinitflag:
                    v_user = pickle.loads(red.get('v_user_' + str(qr_code['Username'])))
                    while not self.async_check(v_user):
                        if (datetime.datetime.now() - starttime).seconds >= 100:
                            return False
                        time.sleep(3)

                    heart_status = red.get('v_user_heart_' + str(qr_code['Username']))
                    if heart_status:
                        if int(heart_status) is not 1:
                            red.set('v_user_heart_' + str(qr_code['Username']), 0)
                            from ipad_weixin.heartbeat_manager import HeartBeatManager
                            HeartBeatManager.begin_heartbeat(v_user.userame, md_username)
                        else:
                            logger.info("%s: 心跳已经存在" % md_username)
                            oss_utils.beary_chat("%s: 心跳已经存在，无需启动心跳" % md_username)

                    else:
                        red.set('v_user_heart_' + str(qr_code['Username']), 0)
                        from ipad_weixin.heartbeat_manager import HeartBeatManager
                        HeartBeatManager.begin_heartbeat(v_user.userame, md_username)
                    return True

    # 向生成的新地址发送空post请求，会有adapters错误，暂时忽略
    def confirm_chatroom_invitation(self, v_user, data):
        buffers = self.GetA8Key(v_user, data)
        if isinstance(buffers, str):
            # print buffers
            try:
                # 替换url中的unicode字符
                url = buffers.split('\"')[3].replace('\\u0026', '&')
            except BaseException:
                return

            if url:
                print url
                try:
                    requests.post(url)
                except BaseException:
                    pass
                logger.info("%s: 邀请进群成功！" % v_user.nickname)

    def GetA8Key(self, v_user, data):
        bot_param = BotParam.objects.filter(username=v_user.userame).first()
        if bot_param:
            self.long_host = bot_param.long_host
            self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)

        payLoadJson = {
            'ReqUrl': data['url'],
            'Scene': 2,
            'ToUserName': data['fromuser']
        }
        pay_load_json = json.dumps(payLoadJson)

        getA8key_msg_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=233,
                user=v_user,
                payloads=pay_load_json.encode('utf-8'),
            )
        )
        getA8key_msg_rsp = grpc_client.send(getA8key_msg_req)

        (grpc_buffers, seq) = grpc_utils.get_seq_buffer(getA8key_msg_rsp)
        if not grpc_buffers:
            logger.info("%s: grpc返回错误" % v_user.nickname)
            self.wechat_client.close_when_done()
            return False

        buffers = self.wechat_client.sync_send_and_return(grpc_buffers)

        if not buffers:
            logger.info("%s: buffers为空" % v_user.nickname)
            self.wechat_client.close_when_done()
            return False

        if ord(buffers[16]) != 191:
            logger.info("%s: 微信返回错误" % v_user.nickname)
            self.wechat_client.close_when_done()
            return False

        getA8key_msg_rsp.baseMsg.cmd = -233
        getA8key_msg_rsp.baseMsg.payloads = buffers
        getA8key_msg_rsp = grpc_client.send(getA8key_msg_rsp)
        buffers = getA8key_msg_rsp.baseMsg.payloads
        self.wechat_client.close_when_done()
        return buffers

    def get_room_qrcode(self, v_user, chatroom_id):
        bot_param = BotParam.objects.filter(username=v_user.userame).first()
        if bot_param:
            self.long_host = bot_param.long_host
            self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)
        payloadJson = json.dumps({"Username": chatroom_id})
        getwxqrcode_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=168,
                user=v_user,
                payloads=payloadJson.encode('utf-8'),
                ))
        getwxqrcode_rep = grpc_client.send(getwxqrcode_req)
        (grpc_buffers, seq) = grpc_utils.get_seq_buffer(getwxqrcode_rep)

        if not grpc_buffers:
            logger.info("%s: grpc返回错误" % v_user.nickname)
            self.wechat_client.close_when_done()
            return False

        buffers = self.wechat_client.sync_send_and_return(grpc_buffers)

        if not buffers:
            logger.info("%s: buffers为空" % v_user.nickname)
            self.wechat_client.close_when_done()
            return False

        if ord(buffers[16]) != 191:
            logger.info("%s: 微信返回错误" % v_user.nickname)
            self.wechat_client.close_when_done()
            return False
        getwxqrcode_rep.baseMsg.cmd = -168
        getwxqrcode_rep.baseMsg.payloads = buffers
        getwxqrcode_rep = grpc_client.send(getwxqrcode_rep)
        buffers = getwxqrcode_rep.baseMsg.payloads
        qr_code = json.loads(buffers)
        imgData = base64.b64decode(qr_code['QrcodeBuf'])
        try:
            oss_path = oss_utils.put_object_to_oss("wxpad/" + base64.b32encode(chatroom_id) + ".png", imgData)
            logger.info("oss_path is: {}".format(oss_path))
            # print("oss_path is: {}".format(oss_path))
        except Exception as e:
            logger.error(e)
            # print('upload oss error by uuid:{}'.format(uuid))
            return
        self.wechat_client.close_when_done()
        return oss_path

    def download_voice(self, v_user, data):
        data = {'msgid': 1646033292, 'length': 23682, 'clientmsgid': '49d78b71ea4377121494e8adcccd8e05wxid_3drnq3ee20fg2268_1511944205'}
        bot_param = BotParam.objects.filter(username=v_user.userame).first()
        if bot_param:
            self.long_host = bot_param.long_host
            self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)
        voicedata = ''
        startpos, blocklen, datalength = 0, 15536, int(data['length'])

        while startpos != datalength:
            count = blocklen if datalength - startpos > blocklen else datalength - startpos
            payloadJson = json.dumps({'MsgId': data['msgid'], 'StartPos': startpos,\
                                      'Datalen': count, 'ClientMsgId': data['clientmsgid']})
            voiceReq = WechatMsg(
                token=CONST_PROTOCOL_DICT['machine_code'],
                version=CONST_PROTOCOL_DICT['version'],
                timeStamp=get_time_stamp(),
                iP=get_public_ip(),
                baseMsg=BaseMsg(
                    cmd=128,
                    user=v_user,
                    payloads=payloadJson.encode('utf-8'),
                    ))
            import binascii
            print binascii.b2a_hex(v_user.sessionKey)
            voiceRsp = grpc_client.send(voiceReq)
            (grpc_buffers, seq) = grpc_utils.get_seq_buffer(voiceRsp)

            if not grpc_buffers:
                logger.info("%s: grpc返回错误" % v_user.nickname)
                self.wechat_client.close_when_done()
                return False
            buffers = self.wechat_client.sync_send_and_return(grpc_buffers)

            if not buffers:
                logger.info("%s: buffers为空" % v_user.nickname)
                self.wechat_client.close_when_done()
                return False

            if ord(buffers[16]) != 191:
                logger.info("%s: 微信返回错误" % v_user.nickname)
                self.wechat_client.close_when_done()
                return False
            voiceRsp.baseMsg.cmd = -128
            voiceRsp.baseMsg.payloads = buffers
            voiceRsp = grpc_client.send(voiceRsp)
            voicedata += voiceRsp.baseMsg.payloads
            startpos += len(voicedata)

        with open('%s-voice.silk' % v_user.userame, 'wb') as f:
            f.write(voicedata)

        logging.info("%s: 语音下载完毕！" % v_user.nickname)
        self.wechat_client.close_when_done()
        return True


if __name__ == "__main__":

    wx_bot = WXBot()

    while True:
        try:
            # wx_user = "wxid_ceapoyxs555k22"
            # wx_user = "wxid_fh235f4nylp22"  # 小小
            # wx_user = "wxid_kj1papird5kn22"
            # wx_user = "wxid_3cimlsancyfg22"  # 点金
            # wx_user = "wxid_cegmcl4xhn5w22" #楽阳
            # wxid_sygscg13nr0g21
            # wx_user = "wxid_5wrnusfmt26932"
            # wxid_mynvgzqgnb5x22
            # wx_user = "wxid_sygscg13nr0g21"
            wx_user = 'manmanshiguang002'
            print "**************************"
            print "enter cmd :{}".format(wx_user)
            print "**************************"
            cmd = input()
            if cmd == 0:
                # wx_user = 'wxid_cegmcl4xhn5w22'

                wx_bot.set_user_context(wx_user)

                v_user_pickle = red.get('v_user_' + wx_user)
                v_user = pickle.loads(v_user_pickle)
                UUid = u"667D18B1-BCE3-4AA2-8ED1-1FDC19446567"
                DeviceType = u"<k21>TP_lINKS_5G</k21><k22>中国移动</k22><k24>c1:cd:2d:1c:5b:11</k24>"
                wx_bot.auto_auth(v_user, UUid, DeviceType, True)

            elif cmd == 1:
                # wxid_ceapoyxs555k22
                v_user_pickle = red.get('v_user_' + wx_user)
                # v_user_pickle = red.get('v_user_' + 'wxid_3cimlsancyfg22')
                v_user = pickle.loads(v_user_pickle)
                wx_bot.set_user_context(wx_user)
                # wx_bot.send_text_msg('fat-phone', '112233', v_user)
                wx_bot.send_text_msg('wxid_9zoigugzqipj21', 'hello~', v_user)

            elif cmd == 2:
                v_user_pickle = red.get('v_user_' + wx_user)
                v_user = pickle.loads(v_user_pickle)
                # 给谁发，谁发的，图片url
                wx_bot.send_img_msg('wxid_9zoigugzqipj21', v_user,
                                    "http://md-oss.di25.cn/7730f412-d4e3-11e7-b4a3-1c1b0d3e23eb.jpeg")

            elif cmd == 3:
                v_user_pickle = red.get('v_user_' + wx_user)
                v_user = pickle.loads(v_user_pickle)
                wx_bot.set_user_context(wx_user)
                wx_bot.async_check(v_user, True)

            elif cmd == 4:
                v_user_pickle = red.get('v_user_' + wx_user)
                v_user = pickle.loads(v_user_pickle)
                from heartbeat_manager import HeartBeatManager
                HeartBeatManager.begin_heartbeat(v_user.userame)
                # break

            elif cmd == 5:
                # wx_bot.login('15158197021')
                wx_bot.login('maytest')
                # wx_bot.login('15900000010')

            elif cmd == 6:
                v_user = pickle.loads(red.get('v_user_' + wx_user))
                wx_bot.get_chatroom_detail(v_user, '6610815091@chatroom')
                print "socket status:{0}".format(wx_bot.wechat_client.connected)

            elif cmd == 7:
                v_user = pickle.loads(red.get('v_user_' + wx_user))
                UUid = u"667D18B1-BCE3-4AA2-8ED1-1FDC19446567"
                DeviceType = u"<k21>TP_lINKS_5G</k21><k22>中国移动</k22><k24>c1:cd:2d:1c:5b:11</k24>"
                wx_bot.auto_auth(v_user, UUid, DeviceType, new_socket=True)

            elif cmd == 8:
                v_user = pickle.loads(red.get('v_user_' + wx_user))
                wx_bot.get_contact(v_user, '6947816994@chatroom')
            elif cmd == 9:
                v_user = pickle.loads(red.get('v_user_' + wx_user))
                wx_bot.send_app_msg(v_user, 'wxid_9zoigugzqipj21', '<appmsg appid="" sdkver="0"><title>Python2生命期</title><des>升级Python3保平安</des><action></action><type>33</type><showtype>0</showtype><soundtype>0</soundtype><mediatagname></mediatagname><messageext></messageext><messageaction></messageaction><content></content><contentattr>0</contentattr><url>https://mp.weixin.qq.com/mp/waerrpage?appid=wxedac7bb2a64c41f7&amp;type=upgrade&amp;upgradetype=3#wechat_redirect</url><lowurl></lowurl><dataurl></dataurl><lowdataurl></lowdataurl><appattach><totallen>0</totallen><attachid></attachid><emoticonmd5></emoticonmd5><fileext></fileext><cdnthumburl>304f02010004483046020100020406070d8b02033d14b9020464fd03b7020459e42bdd0421777869645f3364726e713365653230666732323237335f313530383132353636310204010800030201000400</cdnthumburl><cdnthumbmd5>b9b12405481c2d5273cf1e850aa1d4f6</cdnthumbmd5><cdnthumblength>206292</cdnthumblength><cdnthumbwidth>750</cdnthumbwidth><cdnthumbheight>1206</cdnthumbheight><cdnthumbaeskey>d40cb038f4f8400594cc78dc01913844</cdnthumbaeskey><aeskey>d40cb038f4f8400594cc78dc01913844</aeskey><encryver>0</encryver></appattach><extinfo></extinfo><sourceusername>gh_95486d903be5@app</sourceusername><sourcedisplayname>Python之禅</sourcedisplayname><thumburl></thumburl><md5></md5><statextstr></statextstr><weappinfo><username><![CDATA[gh_95486d903be5@app]]></username><appid><![CDATA[wxedac7bb2a64c41f7]]></appid><type>2</type><version>6</version><weappiconurl><![CDATA[http://mmbiz.qpic.cn/mmbiz_png/XzlqmpwbLjfFGD6TciaRy2IibOwyFBvQicRSjEeybKuzggG2wFXKMAbM2r54CvnpfKUp2tJMeHojqeoetQdYhdmZw/0?wx_fmt=png]]></weappiconurl><pagepath><![CDATA[pages/index/index.html]]></pagepath><shareId><![CDATA[0_wxedac7bb2a64c41f7_101125515_1508125660_0]]></shareId></weappinfo></appmsg>')
            elif cmd == 10:
                v_user = pickle.loads(red.get('v_user_' + wx_user))
                wx_bot.send_voice_msg(v_user, '6610815091@chatroom')

        except Exception as e:
            logger.error(e)
            print e.message
