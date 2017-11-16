# 接口文档

芙蓉兴盛： 
    platform_id: frxs
怡亚通：
    platform_id: star_chain
## 基本接口

    1. getqrcode
        获取二维码
        方法： POST
        参数： 
            {
                "md_username": "136xxx"
                "platform_id":
            }
        url: http://s-prod-04.qunzhu666.com:10024/robot/getqrcode/
    2. host_list
        获取群列表的接口以及参数未变，但返回值发生改变
        url: http://s-prod-04.qunzhu666.com:10024/robot/host_list?username=136xxx
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
                "chatroom_list": ["chatroom.username",......]
                注： chatroom.username == "xxx@chatroom"
            }
        url: http://s-prod-04.qunzhu666.com:10024/robot/add_production_chatroom/
    3. 移除生产群组：
        方法： POST
        参数：
            {
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
    5. 获取登录了该平台所有机器人的列表
    url: http://s-prod-04.qunzhu666.com:10024/robot/platform_user_list?platform_id=xxx
    返回值: 
        {
            "login_user_list":[
                    {"user": "smart", "wxuser_list": ["樂阳", "渺渺的"]}，
                    {"user": "keyerror", ......}
            ]
        }

## 功能接口

    1. 向该平台所有已登录用户的生产群发送消息：
        url: http://s-prod-04.qunzhu666.com:10024/robot/send_msg/
        方法: POST
        参数： 
            {
                "md_username": "136xxx",
                "data": ["http://xxx", "https://xxx", "text", "http://xxx"]
            }
    2. 后台url地址
    
    
## 11.16 修改内容

    1.host_list 返回值改变，每个{}添加了wx_username字段，该字段将用于添加、删除群
        {
            "data":[
                {
                    "production_list":[
                        Object{...},
                        Object{...}
                    ],
                    "wx_username":"wxid_cegmcl4xhn5w22",
                    "group":Array[6],
                    "name":"樂阳",
                    "ret":1
                },
                {
                    "production_list":[
                        Object{...}
                    ],
                    "wx_username":"wxid_fh235f4nylp22",
                    "group":Array[3],
                    "name":"MMT一起赚客服（故障申报）、小小",
                    "ret":0
                }
            ]
        }
        
        
    2. add_production_chatroom以及remove_production_chatroom
        原有的post请求数据：
            {
                "chatroom_list": ["55122@chatroom", "3363@chatroom],
                "md_username": "用户手机号"
            }
        修改为:
            {
                "chatroom_list": [],
                "wx_username": "微信id"
            }
        remove_production_chatroom 同上。





























