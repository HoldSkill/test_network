# -*- coding:utf-8 -*-
from collections import deque


class VoiceDeque(object):
    # 待发送区
    voice_ready = deque()
    # 已发送区
    voice_finish = deque()

    @classmethod
    def get_voice(cls):
        data = cls.voice_ready.popleft()
        cls.voice_finish.append(data)
        return data

    @classmethod
    def clear_deque(cls):
        cls.voice_ready.clear()
        cls.voice_finish.clear()
        return

    @classmethod
    def put_voice(cls, data):
        cls.voice_ready.append(data)
        return

    @classmethod
    def is_valid(cls):
        return True if cls.voice_ready else False

    @classmethod
    def clear_cache(cls):
        cls.voice_finish.clear()
        return

