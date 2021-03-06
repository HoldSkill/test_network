"""WxBot URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from ipad_weixin.views.base_views import GetQrcode, HostList, IsUuidLogin, \
     AddSuperUser, ResetSingleHeartBeat, ResetHeartBeat, StopHeartBeat, test
from ipad_weixin.views.function_views import SendMsgView, PlatformUserList, AddProductionChatroom, \
    RemoveProductionChatroom, DefineSignRule, SendGroupMessageVIew, SendMMTMessageView, GetRoomQrcode, \
    UpdateOrDeleteSignRule
import xadmin

from ipad_weixin.views.test_views import TestSendGroupMsgView, TestSendGroupMessageVIew



robot_urls = [
    url(r'getqrcode', GetQrcode.as_view()),
    url(r'host_list', HostList.as_view()),
    url(r'is_uuid_login', IsUuidLogin.as_view()),
    url(r'add_super_user', AddSuperUser.as_view()),

    url(r'ed0050a7a7c9/reset_heart_beat', ResetHeartBeat.as_view()),
    url(r'reset_single', ResetSingleHeartBeat.as_view()),

    url(r'define_sign_rule', DefineSignRule.as_view()),
    url(r'chatroom_rule', UpdateOrDeleteSignRule.as_view()),

    url(r'send_msg', SendMsgView.as_view()),
    url(r'platform_user_list', PlatformUserList.as_view()),
    url(r'add_production_chatroom', AddProductionChatroom.as_view()),
    url(r'remove_production_chatroom', RemoveProductionChatroom.as_view()),
    # url(r'test', test.as_view()),
    url(r'send_group_msg', SendGroupMessageVIew.as_view()),
    url(r'send_mmt_msg', SendMMTMessageView.as_view()),
    url(r'get_chatroom_qrcode', GetRoomQrcode.as_view()),
    url(r'stop_heart_beat', StopHeartBeat.as_view())
]

xadmin_urls = [
    url(r'maxwell_admin/', xadmin.site.urls)
]

test_urls = [
    url(r'send_group_msg', TestSendGroupMessageVIew.as_view()),
    url(r'test_group_msg', TestSendGroupMsgView.as_view())
]


urlpatterns = [
    url(r'^91191b7a3172/', include(xadmin_urls)),
    url(r'api/robot/', include(robot_urls)),

    # test
    url(r'test', include(test_urls))
]

# + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

