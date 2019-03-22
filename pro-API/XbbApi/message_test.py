# encoding = utf-8
# Author：晴空
import requests
import re
import hashlib
import time
import arrow
from assertpy import soft_assertions
from assertpy import assert_that
from pymongo import MongoClient
import simplejson as json

# 连接mongodb, 使用Django库
mongodb_conn = MongoClient('127.0.0.1', 27017).Managementcenter25

result= "D:\\apitest\\result.txt"
# 测试环境Web域名
web_host = 'http://192.168.10.169:5555'
web_login_headers = {"sign": "1", "Content-Type": "application/json"}
web_session = requests.session()

# 本地测试地址
app_host = 'http://192.168.10.169:5555'
app_header = {"sign": "1", "Content-Type": "application/json"}
app_session = requests.session()

# 接口用例中用到的时间格式
current_minute = arrow.now().format('YYYY-MM-DD HH:mm')
next_hour = arrow.now().shift(hours=1).format('YYYY-MM-DD HH:mm')
today = arrow.now().format('YYYY-MM-DD')
tomorrow = arrow.now().shift(days=1).format('YYYY-MM-DD')
unix_format_now = arrow.now().timestamp

# 查找测试用例中需替换内容时所用的正则表达式
re_str = '[()a-zA-Z\u4e00-\u9fa5_]{1,}@[0-9a-zA-Z_]{1,}'
# 预编译正则表达式]
pattern = re.compile(re_str)


# 生成请求发送时的sign_code值，移动端DingTalk只需要请求参数即可，Web端接口需要请求参数和xbb-access-token
def create_sign_code(request_parameters):
    parameters = str(str(request_parameters)).encode('utf-8')
    return hashlib.sha256(parameters).hexdigest()


# 获得接口用例信息
def get_case_data(case_name):
    data_set = mongodb_conn["api_case"].find({"case_name": case_name}, {"_id": 0})
    for data in data_set:
        return data


# 获得接口URL地址
def get_api_url(api_id):
    api_data = mongodb_conn["api_data"].find({"id": api_id}, {"_id": 0})
    for data in api_data:
        return data["url"]


# 接口用例参数依赖处理
def replace_relate_param(case_name):
    # 根据case_name获得用例数据
    case_data = get_case_data(case_name)
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
                # 单接口的测试用例，使用其他用例中的数据替换参数
                # 被依赖的测试用例数据
                be_related_case_data = get_case_data(relate_case_name)
                # 用实际被依赖的值替换掉参数
                actual_be_related_value = be_related_case_data['saved_value']
                case_param = str(case_param).replace(str(matcher), str(actual_be_related_value))
    if assert_that(case_name).contains('get_workReport_saveConfig_on_web'):
        case_message = str(case_param).encode('utf-8')
    else:
        case_message = json.loads(str(case_param).encode('utf-8'))
    return case_message


# 处理Web请求头部信息
def handle_web_request_head_referer():
    request_header = web_login_headers
    return request_header


# 封装Web后台请求报文
def integrate_web_request_content(case_name):
    request_content = replace_relate_param(case_name)
    return request_content


# 处理APP请求头部信息
def handle_app_request_head_referer():
    # 请求头
    request_header = app_header
    return request_header


# 封装移动端DingTalk请求报文
def integrate_app_request_content(case_name):
    # 测试用例请求参数中的param部分
    request_content = replace_relate_param(case_name)
    return request_content


# 保存实际结果
def update_actual_result(case_name, actual_result):
    mongodb_conn["api_case"].update_one({"case_name": case_name}, {"$set": {"actual_result": actual_result}})


# 断言实际结果包含预期结果
def assert_result(case_name):
    case_data = get_case_data(case_name)
    actual_result = case_data['actual_result']
    expected_result = case_data['expected_result']
    # 判断是否需要断言
    if len(expected_result) == 0:
        pass
    else:
        with soft_assertions():
            assert_that(actual_result).contains_entry(expected_result)


# 发送Web后台请求
def exec_web_request(case_name):
    # 根据用例名称获得用例数据
    case_data = get_case_data(case_name)
    # 获得接口的URL地址
    api_url = get_api_url(case_data['api_id'])
    request_url = str(web_host) + str(api_url)
    print()
    print("接口url:" + request_url)
    # 处理请求头
    request_header = handle_web_request_head_referer()
    # 处理请求的Body部分
    request_content = integrate_web_request_content(case_name)
    print("请求参数:" + str(request_content))
    request_result = web_session.post(headers=request_header, data=request_content, url=request_url)
    try:
        assert_that(request_result.status_code).is_equal_to(200)
        # SaaS Pro里面所有方法均被一个大的try/catch包括，若捕获到异常则code=100063
        # 验收API接口时要求1：http响应状态码=200 2：响应报文的code!100063
        assert_that(request_result.json()['code']).is_not_equal_to(100063)
    except Exception as exception_info:
        raise exception_info
        # 写入result文件
    with open(result, mode='a+', encoding='utf-8') as str_transfer_to_list:
        str_transfer_to_list.write(str("用例名称: " + str(case_name) + "\n"))
        str_transfer_to_list.write(str("接口URL: " + str(api_url) + "\n"))
        str_transfer_to_list.write(str("请求参数: " + str(request_content) + "\n\n\n"))
    # # 更新实际结果
    # actual_result = json.loads(str(request_result.text))
    # update_actual_result(case_name, actual_result)
    # 保存接口调用需要注意时间间隔是1s
    is_sleep = case_data['is_sleep']
    if str(1) == is_sleep:
        time.sleep(1)
    else:
        pass


# 发送移动端DingTalk请求
def exec_app_request(case_name):
    # 测试用例数据
    case_data = get_case_data(case_name)
    # 测试用例请求的API-URL
    api_url = get_api_url(case_data['api_id'])
    request_url = str(app_host) + str(api_url)
    # 请求报文的header部分
    request_header = handle_app_request_head_referer()
    # 请求报文的body部分
    request_content = integrate_app_request_content(case_name)
    # 发送请求后的实际结果
    request_result = app_session.post(headers=request_header, data=request_content, url=request_url)
    try:
        assert_that(request_result.status_code).is_equal_to(200)
        assert_that(request_result.json()['code']).is_not_equal_to(100063)
    except Exception as exception_info:
        raise exception_info
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
    # 单接口用例执行
    # 获得api_id,根据api_id名称判断移动端/Web后台
    api_id = case_data['api_id']
    if str(str(api_id).split('_')[-1]).lower() == 'web':
        exec_web_request(case_name)
    elif str(str(api_id).split('_')[-1]).lower() == 'app':
        exec_app_request(case_name)
    else:
        pass









