# -*- coding: utf-8 -*-

import re

a = """
        6947816994@chatroom:
        <sysmsg type="delchatroommember">
            <delchatroommember>
                <plain><![CDATA[你邀请"我不是。。。"加入了群聊  ]]></plain>
                <text><![CDATA[你邀请"我不是。。。"加入了群聊  ]]></text>
                <link>
                    <scene>invite</scene>
                    <text><![CDATA[  撤销]]></text>
                    <memberlist>
                        <username><![CDATA[wangpeiqinpopwx]]></username>
                    </memberlist>
                </link>
            </delchatroommember>
        </sysmsg>
"""

b = """
6947816994@chatroom:\n<sysmsg type="delchatroommember">\n<delchatroommember>\n<plain><![CDATA[你邀请"我不是。。。"加入了群聊  ]]></plain>\n<text><![CDATA[你邀请"我不是。。。"加入了群聊  ]]></text>\n<link><scene>invite</scene>\n<text><![CDATA[  撤销]]></text>\n<memberlist>\n<username><![CDATA[wangpeiqinpopwx]]></username>\n</memberlist>\n</link>\n</delchatroommember>\n</sysmsg>
"""

pattern = '.*邀请"(.*?)".*'
result = re.match(pattern, b, re.S)
if result:
    print result.group(1)


