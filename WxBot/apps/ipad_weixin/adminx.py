# -*- coding: utf-8 -*-

from ipad_weixin.models import SignInRule, WxUser, ChatRoom, PlatformInformation, Wxuser_Chatroom
import xadmin
from xadmin import views


class BaseSetting(object):
    enable_themes = True  # 主体设置
    use_bootswatch = True
xadmin.site.register(views.BaseAdminView, BaseSetting)


class GlobalSettings(object):
    site_title = "maxwell"
    site_footer = "麦克斯韦数据有限公司"

xadmin.site.register(views.CommAdminView, GlobalSettings)


class SignRuleAdmin(object):
    list_display = ['keyword', 'red_packet_id', 'created', 'chatroom']
    search_fields = ['chatroom__nickname', 'keyword', 'red_packet_id']
xadmin.site.register(SignInRule, SignRuleAdmin)


class WxUserAdmin(object):
    list_display = ['nickname', 'username', 'login', 'is_customer_server', 'user']
    list_editable = ['is_customer_server', 'login']
    search_fields = ['nickname']
    list_filter = ['login', 'is_customer_server']

xadmin.site.register(WxUser, WxUserAdmin)


class ChatroomAdmin(object):
    list_display = ['nickname', 'username', 'wxuser', 'member_nums']
    search_fields = ['nickname', 'wxuser__nickname', 'username']
    list_filter = ['nickname', 'wxuser', 'username']
xadmin.site.register(ChatRoom, ChatroomAdmin)


class WxuserChatroomAdmin(object):
    list_display = ['is_send', 'wxuser', 'chatroom']
    search_fields = ['wxuser__nickname', 'chatroom__nickname']
    list_filter = ['is_send']

xadmin.site.register(Wxuser_Chatroom, WxuserChatroomAdmin)


