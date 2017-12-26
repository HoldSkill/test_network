# _*_ coding:utf-8 _*_

import threading
import socket
import asynchat
from asynchat import fifo
import time
import inspect
from datetime import datetime, timedelta
from ipad_weixin.utils import common_utils
from ipad_weixin.utils.crud_utils import CRUDHandler
import logging
logger = logging.getLogger('weixin_bot')

'''
async_chat & asyncore.dispatcher
    https://docs.python.org/2/library/asynchat.html
    https://docs.python.org/2/library/asyncore.html
'''

#异步通信模块
class WechatClientTest(asynchat.async_chat, object):
    def __init__(self, end_point_host, end_point_port, is_print_log=False):
        # set options
        self.be_init = 0
        self.is_print_log = is_print_log
        self.__notify_list = []

        # 已发送包的参数暂存区
        self.__sent_packge_info ={}
        # 接受到包的缓冲区
        # 存放格式为(seq, data)
        self.__rec_package = fifo()
        self.__lock = threading.Lock()

        # set receive data buffer size
        self.ac_in_buffer_size = 81920
        self.set_terminator(None)
        _monitor_methods_to_be_started = [self.__asyn_rec, self.__check_timeout, self.__asyn_fetch]

        # set socket
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        errcode = _socket.connect_ex((end_point_host, end_point_port))
        if errcode == 0:
            self.__print_log("====================******socket 连接******====================")
        else:
            self.__print_log("error_code:{0}".format(errcode))
        super(WechatClientTest, self).__init__(_socket)

        if not self.connected:
            logger.error("==[Fucked up]===WechatClientModify initiating failed. ======")
            self.close_when_done()
        else:
            # initial arg
            self.buffer_output = []
            self.rec_flag = False
            self.rec_len = 0
            self.total_len = 0
            self.seq = 0
            self.be_init = 1
            self.sent = False
            # start monitor methods
            for met in _monitor_methods_to_be_started:
                t = threading.Thread(target=met)
                t.setDaemon(True)
                t.start()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_when_done()
        return


    """同步通信  以下两个方法"""
    def sync_send_and_return(self, data, time_out=1, close_socket=False):
        self.push(data)
        seq = common_utils.read_int(data, 12)
        start_time = datetime.now()
        while True:
            buffers = self.get_packaget_by_seq(seq)
            if buffers is not None:
                if close_socket:
                    self.close_when_done()
                return buffers
            time.sleep(time_out)
            if (datetime.now() - start_time).seconds >= time_out*10:
                if close_socket:
                    self.close_when_done()
                break

    def get_packaget_by_seq(self, seq):
        # self.__rec_package是由元组组成的fifo
        # self.__rec_package.list 是由元组组成的deque(), 不支持pop(key), 只有remove(value)
        # 2017.12.26 因为数据结构变了，所以这里会比较麻烦，功能正常。
        if self.__lock.acquire():
            __rec_list = self.__rec_package.list
            __seq_list = [x[0] for x in __rec_list]
            if seq in __seq_list:
                _buf = __rec_list[__seq_list.index(seq)][1]
                __rec_list.remove((seq, _buf))
                self.__lock.release()
                return _buf
            self.__lock.release()
            return None


    """ Monitor method  以下三个方法"""
    def __asyn_rec(self):
        while True:
            try:
                time.sleep(1)
                if self.connected is True:
                    self.handle_read()
                else:
                    break
            except Exception as e:
                print(e)

    def __check_timeout(self):
        while not self.sent:
            time.sleep(1)
            continue
        while True:
            for sent_packs in self.__sent_packge_info.keys():
                try:
                    if datetime.now()-self.__sent_packge_info[sent_packs]['time'] > timedelta(0,10,0):
                        nickname = self.__sent_packge_info[sent_packs]['nickname']
                        method_name = self.__sent_packge_info[sent_packs]['func']
                        logger.warning(" {0} 执行 {1} 请求超时".format(nickname, method_name))
                        self.__sent_packge_info.pop(sent_packs)
                except KeyError:
                    pass
                except Exception, e:
                    logger.error(str(e)+' : ' + e.message)
            time.sleep(1)
            if not self.connected:
                break

    def __asyn_fetch(self):
        while True:
            status, buffer = self.__rec_package.pop()
            if buffer:
                seq, data = buffer
                if seq not in self.__sent_packge_info.keys():
                    logger.warning("Received package without SentInfo:  seq {}".format(seq))
                    continue
                param_dict = self.__sent_packge_info.pop(seq)
                func_name = param_dict['func']
                crud_func = getattr(CRUDHandler, func_name, None)
                if not crud_func:
                    logger.warning("Unknown Package: {}.".format(seq))
                    continue
                crud_func(data, **param_dict)
            time.sleep(0.5)
            if not self.connected:
                break


    """接收消息"""
    def collect_incoming_data(self, data):
        if self.connected is False:
            logger.info("连接已断开...")
            return

        while len(data) != 0:
            cur_rec_len = len(data)
            # self.__print_log("接收到包长度: {0}".format(cur_rec_len))
            if cur_rec_len > 0:
                # 检测头部是否有20字节的notify包
                if common_utils.read_int(data[:20], 0) == 20:
                    tmp_data = data[:20]
                    tmp_seq = common_utils.read_int(data, 12)
                    cmd = common_utils.read_int(tmp_data, 8)
                    selector = common_utils.read_int(tmp_data, 16)

                    self.__process_notify_package(tmp_data)

                    # cmd = 24的notify包就不存了
                    if tmp_seq not in [x[0] for x in self.__rec_package.list] and cmd != 24:
                        self.__rec_package.push((tmp_seq, data[:20]))
                    data = data[20:]
                    continue

                # 检测尾部
                if common_utils.read_int(data[-20:], 0) == 20:
                    tmp_data = data[-20:]
                    tmp_seq = common_utils.read_int(tmp_data, 12)
                    cmd = common_utils.read_int(tmp_data, 8)
                    selector = common_utils.read_int(tmp_data, 16)

                    self.__process_notify_package(tmp_data)

                    # cmd = 24的notify包就不存了
                    if tmp_seq not in [x[0] for x in self.__rec_package.list] and cmd != 24:
                        self.__rec_package.push((tmp_seq, data[:20]))

                    data = data[:-20]
                    continue

                if self.rec_flag is False:
                    self.seq = common_utils.read_int(data, 12)
                    # self.__print_log("接收序号 Seq:{0}".format(self.seq))
                    # 期望包总长度
                    self.total_len = common_utils.read_int(data, 0)
                    # self.__print_log("期望包长度 :{0}".format(self.total_len))
                    if self.total_len > 100000:
                        # total_len太长不正常直接过滤...
                        return
                    self.buffer_output = []
                else:
                    pass

                # 如果 期望包总长度 大于 之前已接收包长度，说明需要粘包拆包
                if self.total_len > self.rec_len:
                    # 如果 期望包总长度 小于 当前此包长度，需要自己拆包???????这段逻辑有问题
                    if self.total_len < cur_rec_len + self.rec_len:
                        self.__print_log("This time wx sent too much:{0}".format(self.total_len))
                        data_to_process = data[:self.total_len-self.rec_len]
                        # data_to_process = data[:self.total_len-self.rec_len]是否应该这么改
                        self.rec_len = self.total_len

                    # 如果 期望包总长度 大于或等于 当前此包长度，则代表还需要粘包
                    else:
                        data_to_process = data
                        self.rec_len += cur_rec_len

                    # buffer_output就是最终的包
                    self.buffer_output += data_to_process
                else:
                    self.__print_log("我想要的包，上次就接收够了，你这次还来")
                # 这句话好像没用
                data = data[self.rec_len:]

                # 如果期望包 等于 总接收包，说明ok了，可以将其放入package中
                if self.total_len == self.rec_len:
                    if self.__lock.acquire():
                        _buffers = common_utils.byte_list_to_byte_string(self.buffer_output)
                        # seq等于0的情况需要另处理
                        if self.seq == 0:
                            self.__process_notify_package(_buffers)
                        # 当前dict没有这个seq，放入
                        elif self.seq not in [x[0] for x in self.__rec_package.list]:
                            cmd = common_utils.read_int(data, 8)
                            self.__rec_package.push((self.seq, _buffers))
                            self.seq = 0
                        # 重置参数
                        self.rec_flag = False
                        self.rec_len = 0
                        self.total_len = 0
                        self.__lock.release()
                elif self.total_len > self.rec_len:
                    # self.total_len > self.rec_len那就继续等下个包接收
                    self.rec_flag = True
                    self.__print_log("on data, total_len is {}, rec_len is {}".format(self.total_len, self.rec_len))
                    # from author:排除在接收分包时候的notify 包的干扰 将之前累加的20字节封包在减去...
                    if self.seq > 0 and cur_rec_len == 20:
                        self.rec_len -= cur_rec_len
                else:
                    self.rec_flag = False
                    # self.total_len < self.rec_len说明出现问题了
                    self.__print_log("total_len {} should >= rec_len {}".format(self.total_len, self.rec_len))
                    return


    """回调处理  以下三个方法"""
    def __process_notify_package(self, data):
        # 处理不同cmd的包
        cmd = common_utils.read_int(data, 8)
        selector = common_utils.read_int(data, 16)
        print "cmd:{0},selector:{1}".format(cmd, selector)
        if cmd == 318 and len(self.__notify_list) != 0:
            self.__notify(data)
        if cmd == 24 and len(self.__notify_list) != 0 and len(data) == 20:
            self.__notify(data)
        if cmd != 24 and cmd != 318:
            self.__print_log("未知包CMD:{0} selector:{1} 过滤:{2}".format(cmd, selector, len(data)))

    def __notify(self, data):
        for func in self.__notify_list:
            try:
                t = threading.Thread(target=func, args=(data,))
                t.setDaemon(True)
                t.start()
            except Exception as e:
                self.__print_log("exception:{0}".format(e.message))
                continue

    def register_notify(self, func):
        self.__notify_list.append(func)


    """发送消息"""
    def push(self, data):
        self.ac_out_buffer_size = len(data)
        super(WechatClientTest, self).push(data)
        self.__print_log("push data length: " + str(len(data)))

    def asyn_send(self, data, param_dict):
        # 调用asynchat.push()，并按照数据长度设定self.ac_out_buffer_size，以确保数据完整推出。
        # 推出数据的同时，赋予推送时间，并将参数字典传入
        #   param_dict中至少有3对键值，即：
        #       nickname: 微信昵称, 用以定位用户
        #       time: 发送时间
        #       func: 方法名称
        if not self.sent:
            self.sent = True
        self.push(data)
        assert type(param_dict) == dict, 'param param_dict must be a dict.'
        seq = common_utils.read_int(data, 12)
        param_dict['time'] = datetime.now()
        self.__sent_packge_info[seq]= param_dict


    """asynchat约定必须重载的方法"""
    def found_terminator(self):
        pass


    def __print_log(self, msg):
        if self.is_print_log is True:
            logger.info(msg)

    def close_when_done(self):
        # 发送确认区为空时从容关闭socket。
        while self.__sent_packge_info != {} :
            time.sleep(1)
        super(WechatClientTest, self).close_when_done()
        if self.socket is not None:
            self.socket.close()
        self.__print_log("====================******socket 关闭！******====================")


    @staticmethod
    def check_buffer_16_is_191(buffers):
        if buffers is None or ord(buffers[16]) is not 191:
            return False
        else:
            return True
