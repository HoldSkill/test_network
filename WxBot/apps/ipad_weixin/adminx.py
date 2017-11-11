# -*- coding: utf-8 -*-

from ipad_weixin.models import SignInRule, WxUser, ChatRoom, PlatformInformation
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
    search_fields = ['chatroom__nickname']
xadmin.site.register(SignInRule, SignRuleAdmin)


class WxUserAdmin(object):
    list_display = ['nickname', 'username', 'login', 'is_customer_server', 'user']
    list_editable = ['is_customer_server', 'login']
    search_fields = ['nickname']

xadmin.site.register(WxUser, WxUserAdmin)


class ChatroomAdmin(object):
    list_display = ['nickname', 'username', 'wx_user', 'is_send', 'member_nums']
    search_fields = ['nickname', 'wx_user__nickname']
    list_filter = ['nickname', 'wx_user', 'username']
xadmin.site.register(ChatRoom, ChatroomAdmin)


class PlatformInformationAdmin(object):
    list_display = ['platform_id', 'host_url', 'red_packet_id']
    list_editable = ['platform_id', 'host_url', 'red_packet_id']