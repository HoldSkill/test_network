# -*- coding: utf-8 -*-
from WechatProto_pb2 import WechatMsg, BaseMsg, User
from ipad_weixin.settings import CONST_PROTOCOL_DICT
from ipad_weixin.utils.common_utils import get_time_stamp,  int_list_convert_to_byte_list, get_public_ip


import logging
logger = logging.getLogger('weixin_bot')

def MsgReq(cmd, **kwargs):
    """
    :param cmd: 针对不同的cmd, 构造不同请求
    :param kwargs: 不同请求需要的参数，以key=value形式传入
    :return: 可直接发送给grpc的req对象
    """
    if cmd == 502:
        """get_qrcode"""
        assert 'deviceId' in kwargs, 'param deviceId is required'
        deviceId = kwargs.get('deviceId')
        req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=502,
                user=User(
                    sessionKey=int_list_convert_to_byte_list(CONST_PROTOCOL_DICT['random_encry_key']),
                    deviceId=deviceId
                ),
            )
        )
    elif cmd == 503:
        """check_qrcode_login"""
        assert 'long_head' in kwargs, 'param long_head is required'
        assert 'uuid' in kwargs, 'param uuid is required'
        assert 'deviceId' in kwargs, 'param deviceId is required'
        assert 'notify_key_str' in kwargs, 'param notify_key_str is required'
        long_head = kwargs.get('long_head')
        uuid = kwargs.get('uuid')
        deviceId = kwargs.get('deviceId')
        notify_key_str = kwargs.get('notify_key_str')
        req = WechatMsg(
                token=CONST_PROTOCOL_DICT['machine_code'],
                version=CONST_PROTOCOL_DICT['version'],
                timeStamp=get_time_stamp(),
                iP=get_public_ip(),
                baseMsg=BaseMsg(
                    cmd=503,
                    longHead=long_head,
                    payloads=str(uuid),
                    user=User(
                        sessionKey=int_list_convert_to_byte_list(CONST_PROTOCOL_DICT['random_encry_key']),
                        deviceId=deviceId,
                        maxSyncKey=notify_key_str
                    )
                )
            )
    elif cmd == 1111:
        """confirm_qrcode_login"""
        assert 'deviceId' in kwargs, 'param deviceId is required'
        assert 'payLoadJson' in kwargs, 'param payLoadJson is required'
        deviceId = kwargs.get('deviceId')
        payLoadJson = kwargs.get('payLoadJson')
        req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=1111,
                user=User(
                    sessionKey=int_list_convert_to_byte_list(CONST_PROTOCOL_DICT['random_encry_key']),
                    deviceId=deviceId
                ),
                payloads=payLoadJson.encode('utf-8')
            )
        )
    elif cmd == 205:
        """heart_beat"""
        assert 'v_user' in kwargs, 'param v_user is required'
        v_user = kwargs.get('v_user')
        req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=205,
                user=v_user
            )
        )
    elif cmd == 702:
        """auto_auth"""
        assert 'v_user' in kwargs, 'param v_user is required'
        assert 'pay_load' in kwargs, 'param pay_load is required'
        v_user = kwargs.get('v_user')
        pay_load = kwargs.get('pay_load')
        req = WechatMsg(
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
    elif cmd == 138:
        """async_check"""
        assert 'v_user' in kwargs, 'param v_user is required'
        v_user = kwargs.get('v_user')
        req = WechatMsg(
                token=CONST_PROTOCOL_DICT['machine_code'],
                version=CONST_PROTOCOL_DICT['version'],
                timeStamp=get_time_stamp(),
                iP=get_public_ip(),
                baseMsg=BaseMsg(
                    cmd=138,
                    user=v_user
                )
            )
    elif cmd == 1002:
        """new_init"""
        assert 'v_user' in kwargs, 'param v_user is required'
        v_user = kwargs.get('v_user')
        req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=1002,
                user=v_user
            )
        )
    elif cmd == 522:
        """send_text_msg"""
        assert 'v_user' in kwargs, 'param v_user is required'
        assert 'payLoadJson' in kwargs, 'param payLoadJson is required'
        v_user = kwargs.get('v_user')
        payLoadJson = kwargs.get('payLoadJson')
        req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=522,
                user=v_user,
                payloads=payLoadJson.encode('utf-8')
            )
        )
    elif cmd == 1000:
        """send_voice_msg"""
        assert 'v_user' in kwargs, 'param v_user is required'
        assert 'payload_json' in kwargs, 'param payload_json is required'
        v_user = kwargs.get('v_user')
        payload_json = kwargs.get('payload_json')
        req = WechatMsg(
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
    elif cmd == 110:
        """send_img_msg"""
        assert 'v_user' in kwargs, 'param v_user is required'
        assert 'pay_load_json' in kwargs, 'param pay_load_json is required'
        v_user = kwargs.get('v_user')
        pay_load_json = kwargs.get('pay_load_json')
        req = WechatMsg(
                token=CONST_PROTOCOL_DICT['machine_code'],
                version=CONST_PROTOCOL_DICT['version'],
                timeStamp=get_time_stamp(),
                iP=get_public_ip(),
                baseMsg=BaseMsg(
                    cmd=110,
                    user=v_user,
                    payloads=pay_load_json.encode('utf-8'),
                )
            )
    elif cmd == 106:
        """search_contact"""
        assert 'v_user' in kwargs, 'param v_user is required'
        assert 'payLoadJson' in kwargs, 'param payLoadJson is required'
        v_user = kwargs.get('v_user')
        payLoadJson = kwargs.get('payLoadJson')
        req = WechatMsg(
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
    elif cmd == 551:
        """get_chatroom_detail"""
        assert 'v_user' in kwargs, 'param v_user is required'
        assert 'payLoadJson' in kwargs, 'param payLoadJson is required'
        v_user = kwargs.get('v_user')
        payLoadJson = kwargs.get('payLoadJson')
        req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=551,
                user=v_user,
                payloads=payLoadJson.encode('utf-8')
            )
        )
    elif cmd == 222:
        """send_app_msg"""
        assert 'from_user' in kwargs, 'param from_user is required'
        assert 'pay_load_json' in kwargs, 'param pay_load_json is required'
        from_user = kwargs.get('from_user')
        pay_load_json = kwargs.get('pay_load_json')
        req = WechatMsg(
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
    elif cmd == 182:
        """get_contact"""
        assert 'v_user' in kwargs, 'param v_user is required'
        assert 'payLoadJson' in kwargs, 'param payLoadJson is required'
        v_user = kwargs.get('v_user')
        payLoadJson = kwargs.get('payLoadJson')
        req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=182,
                user=v_user,
                payloads=payLoadJson.encode('utf-8')
            )
        )
    elif cmd == 119:
        """create_chatroom"""
        assert 'v_user' in kwargs, 'param v_user is required'
        assert 'payload_json' in kwargs, 'param payload_json is required'
        v_user = kwargs.get('v_user')
        payload_json = kwargs.get('payload_json')
        req = WechatMsg(
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
    elif cmd == 681:
        """modify_chatroom_name"""
        assert 'v_user' in kwargs, 'param v_user is required'
        assert 'payload_json' in kwargs, 'param payload_json is required'
        v_user = kwargs.get('v_user')
        payload_json = kwargs.get('payload_json')
        req = WechatMsg(
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
    elif cmd == 610:
        """invite_chatroom"""
        assert 'v_user' in kwargs, 'param v_user is required'
        assert 'payloadJson' in kwargs, 'param payloadJson is required'
        v_user = kwargs.get('v_user')
        payloadJson = kwargs.get('payloadJson')
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
    elif cmd == 120:
        """add_chatroom_member"""
        assert 'v_user' in kwargs, 'param v_user is required'
        assert 'payloadJson' in kwargs, 'param payloadJson is required'
        v_user = kwargs.get('v_user')
        payloadJson = kwargs.get('payloadJson')
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
    elif cmd == 179:
        """delete_chatroom_member"""
        assert 'v_user' in kwargs, 'param v_user is required'
        assert 'payloadJson' in kwargs, 'param payloadJson is required'
        v_user = kwargs.get('v_user')
        payloadJson = kwargs.get('payloadJson')
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
    elif cmd == -318:
        """decode_secure_notify"""
        assert 'v_user' in kwargs, 'param v_user is required'
        assert 'data' in kwargs, 'param data is required'
        v_user = kwargs.get('v_user')
        data = kwargs.get('data')
        req = WechatMsg(
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
    elif cmd == 805:
        """get_chatroom_msg"""
        assert 'v_user' in kwargs, 'param v_user is required'
        assert 'payload_dict_json' in kwargs, 'param payload_dict_json is required'
        v_user = kwargs.get('v_user')
        payload_dict_json = kwargs.get('payload_dict_json')
        req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=805,
                user=v_user,
                payloads=payload_dict_json.encode('utf-8')
            )
        )
    elif cmd == 233:
        """GetA8Key"""
        assert 'v_user' in kwargs, 'param v_user is required'
        assert 'pay_load_json' in kwargs, 'param pay_load_json is required'
        v_user = kwargs.get('v_user')
        pay_load_json = kwargs.get('pay_load_json')
        req = WechatMsg(
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
    else:
        return
    return req