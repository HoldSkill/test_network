from ipad_weixin.models import SignInRule, WxUser, ChatRoom
import xadmin


class SignRuleAdmin(object):
    list_display = ['keyword', 'red_packet_id', 'created', 'chatroom']

xadmin.site.register(SignInRule, SignRuleAdmin)


class WxUserAdmin(object):
    list_display = ['nickname', 'username', 'login', 'is_customer_server', 'user']
    list_editable = ['is_customer_server', 'login']
    search_fields = ['nickname']

xadmin.site.register(WxUser, WxUserAdmin)


class ChatroomAdmin(object):
    list_display = ['nickname', 'username', 'wx_user']
    search_fields = ['nickname']
# , 'username', 'wx_user'
xadmin.site.register(ChatRoom, ChatroomAdmin)