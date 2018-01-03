# -*- coding: utf-8 -*-
from rest_framework import serializers
from ipad_weixin.models import Rule_Chatroom, ChatRoom, SignInRule


class ChatroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ("nickname", "username")


class SignInRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignInRule
        fields = ("keyword", )


class RuleChatRoomSerializer(serializers.ModelSerializer):
    chatroom = ChatroomSerializer()
    sign_in_rule = SignInRuleSerializer()

    class Meta:
        model = Rule_Chatroom
        fields = ("created", "updated", "chatroom", "sign_in_rule")