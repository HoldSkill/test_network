# 接口文档

## 基本接口

    1. getqrcode
        方法： POST
        参数： 
            {
                "md_username": "136xxx"
                "platform_id":
            }
        url: http://s-prod-04.qunzhu666.com:10024/robot/getqrcode/
    2. host_list
        获取群列表的接口以及参数未变，但返回值发生改变
        {
            "data":[
                {
                    "production_list":[  # production_list 为生产群
                        {
                            "username":"6610815091@chatroom",
                            "nickname":"测试福利社"
                        }
                    ],
                    "group":[    # group为用户所有的群组
                        {
                            "username":"6947816994@chatroom",
                            "nickname":"福利社XXXX"
                        },
                        {
                            "username":"6610815091@chatroom",
                            "nickname":"测试福利社"
                        },
                    ],
                    "name":"樂阳",
                    "ret":0
                }
            ]
        }
    2. 添加生产群组
        方法： POST
        参数：
            {
                "md_username": "136xxx"
                "chatroom_list": ["chatroom.username",......]
                注： chatroom.username == "xxx@chatroom"
            }
        url: http://s-prod-04.qunzhu666.com:10024/robot/add_production_chatroom/
    3. 移除生产群组：
        方法： POST
        参数：
            {
                "md_username": "136xxx"
                "chatroom_list": ["chatroom.username",......]
                注： chatroom.username == "xxx@chatroom"
            }
        url: http://s-prod-04.qunzhu666.com:10024/robot/remove_production_chatroom/
    4. 添加签到口令
        方法： POST
        参数：
            {
                "md_username": 
                "keyword": "签到口令",
                "platform_id": 
            }
        url: http://s-prod-04.qunzhu666.com:10024/robot/define_sign_rule/

## 功能接口

    1. 向该平台所有已登录用户的生产群发送消息：
        url: http://s-prod-04.qunzhu666.com:10024/robot.send_msg/
        方法: POST
        参数： 
            {
                "md_username": "136xxx",
                "data": ["http://xxx", "https://xxx", "text", "http://xxx"]
            }
    2. 后台url地址
        url: http://s-prod-04.qunzhu666.com:10024/maxwell/admin