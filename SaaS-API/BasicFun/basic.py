# encoding = UTF-8
# Author：晴空
import logging
import requests
import re
import hashlib
import time
import simplejson as json
import arrow
from assertpy import soft_assertions
from assertpy import assert_that
from pymongo import MongoClient

# 连接mongodb, 使用Django库
mongodb_conn = MongoClient('127.0.0.1', 27017).Django

# 测试环境DingTalk域名
app_host = 'https://testdingtalkapi3.xbongbong.com'
# 登录DingTalk时的URL
app_login_url = '/index.htm?corpid=ding18b527cbc48f835535c2f4657eb6378f&appid=2033&dd_nav_bgcolor=ffff943e'
# 登录DingTalk时的请求头
app_header = {
    "Host": "testdingtalkapi3.xbongbong.com",
    "Accept": "text/html,application/xhtml xml,application/xml;q=0.9,*/*;q=0.8",
    "DingTalk-Flag": "1",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15F79 AliApp(DingTalk/4.5.3) com.laiwang.DingTalk/10190495 Channel/201200 language/zh-Hans-CN",
    "Accept-Language": "zh-cn",
    "Accept-Encoding": "br, gzip, deflate",
    "Connection": "keep-alive"
}

# 移动端session, session初始化操作先写这里，后续移到__init__中
app_session = requests.session()
app_session.get(url=app_host + app_login_url, headers=app_header)
# 移动端登录时cookie信息
app_cookie = app_session.cookies


# 测试环境Web域名
web_host = 'https://testdingtalk3.xbongbong.com'
# 登录Web时请求的URL, 每次操作钉钉重新登录时会变化,切记
web_login_url = '/user/autoLogin.do?t=eqraQNCqDIBpOkkj+/JM1MRtVLJwtGbMq9zuyE4hiasfW7v7zsD7NSDomnAcrjYQ8pAX8ouxp6I=&nonce=yru4kv'
# 请求头中的referer信息, 随登录时url变化而变动
web_header_referer = 'https://testdingtalkapi3.xbongbong.com//dingtalk/sns/userinfo.html?code=3f7dcc92a0343416b50cec3e02eb345a&state=STATE'
# 测试环境请求header
# 注意：Referer部分每次更新环境后会变化 抓包后替换改部分
web_login_headers = {"Host": "testdingtalk3.xbongbong.com", "Connection": "keep-alive","Upgrade-Insecure-Requests": "1",
                     "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36",
                     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                     "Referer": web_header_referer,"Accept-Encoding": "gzip, deflate, br","Accept-Language": "zh-CN,zh;q=0.8"}

# Web后台session初始化
web_session = requests.session()
web_session.get(url=web_host + web_login_url, headers=web_login_headers, allow_redirects=False)
# 扫码登录时的cookie信息
web_cookie = web_session.cookies
# 登录cookie中的xbbAccessToken值,登录后所有请求都会用到这个值
web_access_token = web_cookie['xbbAccessToken']
# 登录cookie中的JSESSIONID, 后续所有请求中均用到
web_session_id = web_cookie['JSESSIONID']

# 接口用例中用到的时间格式
# 当前分钟
current_minute = arrow.now().format('YYYY-MM-DD HH:mm')
# 下一小时
next_hour = arrow.now().shift(hours=1).format('YYYY-MM-DD HH:mm')
# 当天
today = arrow.now().format('YYYY-MM-DD')
# 明天
tomorrow = arrow.now().shift(days=1).format('YYYY-MM-DD')
# Unix时间戳
unix_format_now = arrow.now().timestamp

# 查找测试用例中需替换内容时所用的正则表达式
# re_str = '[a-zA-Z0-9_]{1,}@[a-zA-Z_]{1,}'
re_str = '[()a-zA-Z\u4e00-\u9fa5_]{1,}@[0-9a-zA-Z_]{1,}'
# 预编译正则表达式
pattern = re.compile(re_str)


'''
    生成请求发送时的sign_code值
    移动端DingTalk只需要请求参数即可
    Web端接口需要请求参数和xbb-access-token
'''


def create_sign_code(request_parameters, *args):
    if len(args) > 0:
        parameters = str(str(request_parameters) + str(args[0])).encode('utf-8')
    else:
        parameters = str(request_parameters).encode('utf-8')
    return hashlib.sha256(parameters).hexdigest()


# 断言实际结果包含预期结果
def assert_result(case_name, *args):
    # 判断是否传入step_name
    if len(args) > 0:
        case_data = get_case_data(case_name, args[0])
    else:
        case_data = get_case_data(case_name)
    actual_result = case_data['actual_result']
    expected_result = case_data['expected_result']
    # 判断是否需要断言
    if len(expected_result) == 0:
        pass
    else:
        with soft_assertions():
            assert_that(actual_result).contains_entry(expected_result)


# 获得接口用例信息
def get_case_data(case_name, *args):
    # 实际参数的个数(除case_name外)
    param_length = len(args)
    # 两个及以上个参数，使用case_name和step_name查询用例中测试步骤的数据
    if 0 < int(param_length):
        data_set = mongodb_conn["api_case"].find({"case_name": case_name, "step_name": str(args[0])}, {"_id": 0})
    # 仅一个参数，使用case_name查询用例数据
    else:
        data_set = mongodb_conn["api_case"].find({"case_name": case_name}, {"_id": 0})
    for data in data_set:
        return data


# 获得接口URL地址
def get_api_url(api_id):
    api_data = mongodb_conn["api_data"].find({"id": api_id}, {"_id": 0})
    for data in api_data:
        return data["url"]


# 获得多接口业务流用例中的所有测试步骤
def get_steps_in_multiple_api_case(case_name):
    # 业务流接口用例步骤总数
    case_step_count = mongodb_conn["api_case"].find({"case_name": case_name}, {"step_name": 1, "_id": 0}).count()
    # 接口用例的步骤名称
    case_steps = mongodb_conn["api_case"].find({"case_name": case_name}, {"step_name": 1, "_id": 0})
    # 列表存放用例中所有步骤名称
    step_name_list = []
    if case_step_count == 0:
        pass
    else:
        for step in case_steps:
            step_name_list.append(step["step_name"])
    return sorted(step_name_list)


# 接口用例参数依赖处理
def replace_relate_param(case_name, *args):
    # 单接口，根据case_name获得用例数据
    if len(args) == 0:
        case_data = get_case_data(case_name)
    # 多接口，根据case_name和step_name获得测试步骤的数据
    else:
        case_data = get_case_data(case_name, str(args[0]))
    # 用例中的请求参数
    case_param = case_data['request_param']

    # 正则查找匹配项
    matchers = pattern.findall(str(case_param))
    # 判断请求参数中是否有依赖其他用例的数据
    if 0 == len(matchers):
        pass
    else:
        for matcher in matchers:
            relate_case_name = matcher.split('@')[0]
            # 替换请求参数中使用的时间
            if relate_case_name == 'time':
                be_related_time = matcher.split('@')[1]
                if be_related_time == 'current_minute':
                    case_param = str(case_param).replace(str(matcher), str(current_minute))
                elif be_related_time == 'unix_format_now':
                    case_param = str(case_param).replace(str(matcher), str(unix_format_now))
                elif be_related_time == 'next_hour':
                    case_param = str(case_param).replace(str(matcher), str(next_hour))
                elif be_related_time == 'today':
                    case_param = str(case_param).replace(str(matcher), str(today))
                elif be_related_time == 'tomorrow':
                    case_param = str(case_param).replace(str(matcher), str(tomorrow))
                else:
                    pass
            # 用实际值替换依赖其他用例的数据
            else:
                # 多个接口的业务用例，用测试步骤中的数据替换参数
                if case_data.__contains__('step_name'):
                    # 被依赖的测试步骤名
                    be_related_step_name = matcher.split('@')[1]
                    # 被依赖的步骤数据
                    be_related_step_data = get_case_data(relate_case_name, be_related_step_name)
                    # 用实际被依赖的值saved_value替换掉参数
                    actual_be_related_value = be_related_step_data['saved_value']
                    case_param = str(case_param).replace(str(matcher), str(actual_be_related_value))
                # 单接口的测试用例，使用其他用例中的数据替换参数
                else:
                    # 被依赖的测试用例数据
                    be_related_case_data = get_case_data(relate_case_name)
                    # 用实际被依赖的值替换掉参数
                    actual_be_related_value = be_related_case_data['saved_value']
                    case_param = str(case_param).replace(str(matcher), str(actual_be_related_value))
    return case_param


# 处理APP请求头部信息
def handle_app_request_head_referer(case_name, *args)   :
    if len(args) == 0:
        # 测试用例内容
        case_content = get_case_data(case_name)
    else:
        case_content = get_case_data(case_name, args[0])
    # 请求头
    request_header = app_header
    # 请求头中的referer信息
    request_header_referer = case_content['request_header']
    header_matchers = pattern.findall(str(request_header_referer))
    # 替换请求头中的referer信息
    if request_header_referer == '':
        pass
    else:
        if 0 == len(header_matchers):
            pass
        else:
            for matcher in header_matchers:
                relate_case_name = matcher.split('@')[0]
                be_related_case_data = get_case_data(relate_case_name)
                actual_be_related_value = be_related_case_data['saved_value']
                request_header_referer = str(request_header_referer).replace(str(matcher), str(actual_be_related_value))
                request_header['Referer'] = request_header_referer
    return request_header


# 处理Web请求头部信息
def handle_web_request_head_referer(case_name, *args):
    if len(args) == 0:
        case_content = get_case_data(case_name)
    else:
        case_content = get_case_data(case_name, args[0])
    request_header = web_login_headers
    request_header_referer = case_content['request_header']
    header_matchers = pattern.findall(str(request_header_referer))
    if request_header_referer == '':
        pass
    else:
        if 0 == len(header_matchers):
            pass
        else:
            for matcher in header_matchers:
                relate_case_name = matcher.split('@')[0]
                be_related_case_data = get_case_data(relate_case_name)
                actual_be_related_value = be_related_case_data['saved_value']
                request_header_referer = str(request_header_referer).replace(str(matcher), str(actual_be_related_value))
                request_header['Referer'] = request_header_referer
    return request_header


# 封装移动端DingTalk请求报文
def integrate_app_request_content(case_name, *args):
    if len(args) == 0:
        # 测试用例请求参数中的param部分
        case_param = replace_relate_param(case_name)
        # 生成sign_code 移动端只需要param部分即可
        case_sign_code = create_sign_code(case_param)
    else:
        case_param = replace_relate_param(case_name, args[0])
        case_sign_code = create_sign_code(case_param, args[0])
    # 组装请求 移动端请求参数分4部分：params-sign_code-platform-frontDev
    request_content = {"params": case_param, "sign": case_sign_code,
                       "platform": "dingtalk", "frontDev": "0"}
    return request_content


# 封装Web后台请求报文
def integrate_web_request_content(case_name, *args):
    if len(args) == 0:
        case_param = replace_relate_param(case_name)
        case_sign_code = create_sign_code(case_param, web_access_token)
    else:
        case_param = replace_relate_param(case_name, args[0])
        case_sign_code = create_sign_code(case_param, web_access_token)
    request_content = {"params": case_param, "sign": case_sign_code, "platform": "web",
                       "frontDev": "0", "JSESSIONID": web_session_id}
    return request_content


# 保存单接口被依赖的值
def update_relate_key_value(case_name, value_need_to_save, *args):
    if len(args) == 0:
        mongodb_conn["api_case"].update_one({"case_name": case_name},
                                            {"$set": {"saved_value": value_need_to_save}})
    else:
        mongodb_conn["api_case"].update({"case_name": case_name, "step_name": args[0]},
                                        {"$set": {"saved_value": value_need_to_save}})


# 保存实际结果
def update_actual_result(case_name, actual_result, *args):
    if len(args) == 0:
        mongodb_conn["api_case"].update_one({"case_name": case_name}, {"$set": {"actual_result": actual_result}})
    else:
        mongodb_conn["api_case"].update_one({"case_name": case_name, "step_name": args[0]},
                                            {"$set": {"actual_result": actual_result}})


# 发送移动端DingTalk请求
def exec_app_request(case_name, *args):
    if len(args) == 0:
        # 测试用例数据
        case_data = get_case_data(case_name)
        # 测试用例请求的API-URL
        api_url = get_api_url(case_data['api_id'])
        request_url = str(app_host) + str(api_url)
        # 请求报文的header部分
        request_header = handle_app_request_head_referer(case_name)
        # 请求报文的body部分
        request_content = integrate_app_request_content(case_name)
        # 发送请求后的实际结果
        request_result = app_session.post(headers=request_header, data=request_content, url=request_url,
                                          cookies=app_cookie)
        # 发送请求后返回报文的body部分
        actual_result = json.loads(str(request_result.text))
        # 更新实际结果,保存在Mongo中
        update_actual_result(case_name, actual_result)

        # 判断是否需要保存当前请求返回报文中的id相关数据
        key_need_to_save = case_data['key_need_to_save']
        if key_need_to_save == '':
            pass
        else:
            saved_value = actual_result[key_need_to_save]
            update_relate_key_value(case_name, saved_value)
    else:
        # 测试用例数据
        case_data = get_case_data(case_name, args[0])
        # 测试用例请求的API-URL
        api_url = get_api_url(case_data['api_id'])
        request_url = app_host + api_url
        # 请求报文的header部分
        request_header = handle_app_request_head_referer(case_name, args[0])
        # 请求报文的body部分
        request_content = integrate_app_request_content(case_name, args[0])
        # 发送请求后的实际结果
        request_result = app_session.post(headers=request_header, data=request_content, url=request_url,
                                          cookies=app_cookie)
        # 发送请求后返回报文的body部分
        actual_result = json.loads(str(request_result.text))
        # 更新实际结果,保存在MongoDB中
        update_actual_result(case_name, actual_result, args[0])

        # 判断是否需要保存当前请求返回报文中的id相关数据
        key_need_to_save = case_data['key_need_to_save']
        if key_need_to_save == '':
            pass
        else:
            saved_value = actual_result[key_need_to_save]
            update_relate_key_value(case_name, saved_value, args[0])

    # 保存接口调用需要注意时间间隔是1s
    is_sleep = case_data['is_sleep']
    if str(1) == is_sleep:
        time.sleep(1)
    else:
        pass


# 发送Web后台请求
def exec_web_request(case_name, *args):
    # 单接口用例
    if len(args) == 0:
        # 根据用例名称获得用例数据
        case_data = get_case_data(case_name)
        # 获得接口的URL地址
        api_url = get_api_url(case_data['api_id'])
        request_url = str(web_host) + str(api_url)
        # 处理请求头
        request_header = handle_web_request_head_referer(case_name)
        # 处理请求的Body部分
        request_content = integrate_web_request_content(case_name)
        # 发送请求
        request_result = web_session.post(headers=request_header, data=request_content, url=request_url,
                                          cookies=web_cookie)
        # 更新实际结果
        actual_result = json.loads(str(request_result.text))
        update_actual_result(case_name, actual_result)
        # 保存被依赖的值
        key_need_to_save = case_data['key_need_to_save']
        if key_need_to_save == '':
            pass
        else:
            saved_value = actual_result[key_need_to_save]
            update_relate_key_value(case_name, saved_value)
    # 业务流用例, 执行用例中指定的步骤
    else:
        case_data = get_case_data(case_name, args[0])
        api_url = get_api_url(case_data['api_id'])
        request_url = web_host + api_url
        request_header = handle_web_request_head_referer(case_name, args[0])
        request_content = integrate_web_request_content(case_name, args[0])
        request_result = web_session.post(headers=request_header, data=request_content, url=request_url,
                                          cookies=web_cookie)

        actual_result = json.loads(str(request_result.text))
        update_actual_result(case_name, actual_result, args[0])

        key_need_to_save = case_data['key_need_to_save']
        if key_need_to_save == '':
            pass
        else:
            saved_value = actual_result[key_need_to_save]
            update_relate_key_value(case_name, saved_value, args[0])

    # 保存接口调用需要注意时间间隔是1s
    is_sleep = case_data['is_sleep']
    if str(1) == is_sleep:
        time.sleep(1)
    else:
        pass


# 封装所有用例执行
def exe_case(case_name):
    # 获得case数据, 判断是否有step_name
    case_data = get_case_data(case_name)
    # 判断用例中是否包含键step_name
    if case_data.__contains__('step_name'):
        # 根据用例名获得用例中所有测试步骤名称
        case_step_name_list = get_steps_in_multiple_api_case(case_name)
        # 遍历并执行用例中的步骤
        for step_name in case_step_name_list:
            # 用例步骤数据
            step_data = get_case_data(case_name, step_name)
            # 用例步骤中的api_id
            step_api_id = step_data['api_id']
            # 判断用例步骤是Web后台/移动端DingTalk并执行
            if str(str(step_api_id).split('_')[-1]).lower() == 'web':
                exec_web_request(case_name, step_name)
            elif str(str(step_api_id).split('_')[-1]).lower() == 'app':
                exec_app_request(case_name, step_name)
            else:
                pass
    # 单接口用例执行
    else:
        # 获得api_id,根据api_id名称判断移动端/Web后台
        api_id = case_data['api_id']
        if str(str(api_id).split('_')[-1]).lower() == 'web':
            exec_web_request(case_name)
        elif str(str(api_id).split('_')[-1]).lower() == 'app':
            exec_app_request(case_name)
        else:
            pass
