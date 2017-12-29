# -*- coding: utf-8 -*-

import re
import requests
import json
import time

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
# b = """
# 6947816994@chatroom:\n<sysmsg type="delchatroommember">\n<delchatroommember>\n<plain><![CDATA[你邀请"我不是。。。"加入了群聊  ]]></plain>\n<text><![CDATA[你邀请"我不是。。。"加入了群聊  ]]></text>\n<link><scene>invite</scene>\n<text><![CDATA[  撤销]]></text>\n<memberlist>\n<username><![CDATA[wangpeiqinpopwx]]></username>\n</memberlist>\n</link>\n</delchatroommember>\n</sysmsg>
# """
#
# pattern = '.*邀请"(.*?)".*'
# result = re.match(pattern, b, re.S)
# if result:
#     print result.group(1)

url = "http://s-poc-02.qunzhu666.com/sign/"
request_url = url + "oGO5ABhwpqFyNBhmuUHR"

data = {'speaker_nick_name_trim': u'\u6211\u80e1\u6c49\u4e09\u53c8\u56de\u6765\u4e86',
        'time': {'$date': 1514441664044},
        'speaker_head_img_url': u'http://wx.qlogo.cn/mmhead/ver_1/VCeTmyaYbNIIc3JpKD9hoOLAsVK5ZpdLlTMN813ntrVx1z8C8LMuCkUu9txtzBDljIIQrl6jd7ycbsV8QXiaMDc869MtKPeUoUEDPEEhxfVc/132',
        'speaker_nick_name_emoji_unicode': u'\u6211\u80e1\u6c49\u4e09\u53c8\u56de\u6765\u4e86',
        'from_user_id': u'6610815091@chatroom', 'speaker_id': u'wxid_cegmcl4xhn5w22'}
for i in range(100):
    response = requests.post(request_url, data=json.dumps(data))
    print response.content
    time.sleep(0.25)


