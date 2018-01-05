# -*- coding: utf-8 -*-

import re
import requests
import json
import time
from bs4 import BeautifulSoup

# a = """
#         6947816994@chatroom:
#         <sysmsg type="delchatroommember">
#             <delchatroommember>
#                 <plain><![CDATA[你邀请"我不是。。。"加入了群聊  ]]></plain>
#                 <text><![CDATA[你邀请"我不是。。。"加入了群聊  ]]></text>
#                 <link>
#                     <scene>invite</scene>
#                     <text><![CDATA[  撤销]]></text>
#                     <memberlist>
#                         <username><![CDATA[wangpeiqinpopwx]]></username>
#                     </memberlist>
#                 </link>
#             </delchatroommember>
#         </sysmsg>
# """
#
def trans_xml_to_dict(xml):
    """
    将微信支付交互返回的XML格式数据转化为Dict对象
    """
    soup = BeautifulSoup(xml, features='xml')
    xml = soup.find('xml')

    # 将 XML 数据转化为 Dict
    data = dict([(item.name, item.text) for item in xml.find_all()])
    return data

b = """
    <sysmsg type="delchatroommember">
        <delchatroommember>
            <plain><![CDATA["陌"通过扫描你分享的二维码加入群聊  ]]></plain>
            <text><![CDATA["陌"通过扫描你分享的二维码加入群聊  ]]></text>
            <link>
                <scene>qrcode</scene>
                <text><![CDATA[  撤销]]></text>
                <memberlist>
                    <username><![CDATA[wxid_9zoigugzqipj21]]></username>
                </memberlist>
                <qrcode><![CDATA[http://weixin.qq.com/g/A3We6mFK_UP6N37r]]></qrcode>
            </link>
        </delchatroommember>
    </sysmsg>
"""


pattern = '.*"(.*?)".*'
result = re.match(pattern, b, re.S)
if result:
    print result.group(1)

# url = "http://s-poc-02.qunzhu666.com/sign/"
# request_url = url + "oGO5ABhwpqFyNBhmuUHR"
#
# data = {'speaker_nick_name_trim': u'\u6211\u80e1\u6c49\u4e09\u53c8\u56de\u6765\u4e86',
#         'time': {'$date': 1514441664044},
#         'speaker_head_img_url': u'http://wx.qlogo.cn/mmhead/ver_1/VCeTmyaYbNIIc3JpKD9hoOLAsVK5ZpdLlTMN813ntrVx1z8C8LMuCkUu9txtzBDljIIQrl6jd7ycbsV8QXiaMDc869MtKPeUoUEDPEEhxfVc/132',
#         'speaker_nick_name_emoji_unicode': u'\u6211\u80e1\u6c49\u4e09\u53c8\u56de\u6765\u4e86',
#         'from_user_id': u'6610815091@chatroom', 'speaker_id': u'wxid_cegmcl4xhn5w22'}
# for i in range(100):
#     response = requests.post(request_url, data=json.dumps(data))
#     print response.content
#     time.sleep(0.25)


