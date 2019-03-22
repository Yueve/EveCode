import simplejson as json
import re

# 用例数据
case_data = {
    "case_name": "",
    "api_id": "",
    "request_param": "",
    "request_header": "",
    "key_need_to_save": "",
    "saved_value": "",
    "is_sleep": 1,
    "expected_result": {},
    "actual_result": ""
}

# 请求参数中的value有5中类型
str_none = ''

match = "'"
create_case_pattern = re.compile(match)
# 编译正则表达式模式，返回一个对象。
api_file = "D:\\apitest\\auto_case_demo.json"
auto_case = "D:\\apitest\\auto_case.txt"


def create_case():
    with open("D:\\apitest\\auto_case_demo.json",mode='r+', encoding='utf-8' ) as data:
        for line in data:
            init_data = json.loads(line)
            api_id = init_data['id']
            case_data['api_id'] = api_id
            init_param = dict(init_data['param'])
            # 遍历请求参数
            for param_key in init_param.keys():
                list_type = []
                temp_param = dict.copy(init_param)

                # 规则1：构造key缺失的用例
                temp_param[str_none] = temp_param.pop(param_key)
                matchers = create_case_pattern.findall(str(temp_param))
                for matcher in matchers:
                    temp_param = str(temp_param).replace(str(matcher), str('\"'))
                case_data['request_param'] = temp_param

                lose_key_case_name = str(api_id) + "的key-" + param_key + "缺失"
                case_data['case_name'] = lose_key_case_name

                # 写入自动化生成用例的文件中
                with open(auto_case, mode='a+', encoding='utf-8') as lose_key:
                    lose_key.write(str(case_data) + ",\n")

                # 规则2：构造value缺失的用例
                temp_param = dict.copy(init_param)
                temp_param[param_key] = str_none
                matchers = create_case_pattern.findall(str(temp_param))
                for matcher in matchers:
                    temp_param = str(temp_param).replace(str(matcher), str('\"'))
                case_data['request_param'] = temp_param

                lose_value_case_name = str(api_id) + "中" + param_key + "的值缺失"
                case_data['case_name'] = lose_value_case_name

                # 写入自动化用例文件
                with open(auto_case, mode='a+', encoding='utf-8') as lose_value:
                    lose_value.write(str(case_data) + ",\n")

                # 规则3：构造参数格式异常的用例
                # 将str转换为list
                temp_param = dict.copy(init_param)
                if isinstance(temp_param[param_key], str):
                    # 规则3-1 若value类型是str，则改变value类型为dict,list,int,bool
                    # Python方案只将str转变为list和dict, Java方案中将实现全部转换
                    list_type.insert(0, temp_param[param_key])
                    temp_param[param_key] = list_type
                    matchers = create_case_pattern.findall(str(temp_param))
                    for matcher in matchers:
                        temp_param = str(temp_param).replace(str(matcher), str('\"'))
                    case_data['request_param'] = temp_param
                    value_type_transfer_to_list = str(api_id) + "中" + param_key + "的字符串类型value值转变为list格式"
                    case_data['case_name'] = value_type_transfer_to_list

                    # 写入自动化用例文件
                    with open(auto_case, mode='a+', encoding='utf-8') as str_transfer_to_list:
                        str_transfer_to_list.write(str(case_data) + ",\n")

                # 规则4：将dict转换为list
                temp_param = dict.copy(init_param)
                if isinstance(temp_param[param_key], dict):
                    list_type = []
                    list_type.insert(0, temp_param[param_key])
                    temp_param[param_key] = list_type
                    matchers = create_case_pattern.findall(str(temp_param))
                    for matcher in matchers:
                        temp_param = str(temp_param).replace(str(matcher), str('\"'))
                    case_data['request_param'] = temp_param

                    value_type_transfer_to_list = str(api_id) + "中" + param_key + "的json类型value值转变为list格式"
                    case_data['case_name'] = value_type_transfer_to_list

                    # 写入自动化用例文件
                    with open(auto_case, mode='a+', encoding='utf-8') as dict_transfer_to_list:
                        dict_transfer_to_list.write(str(case_data) + ",\n")

                # 规则5：将int转换为list
                temp_param = dict.copy(init_param)
                if isinstance(temp_param[param_key], int):
                    list_type = []
                    list_type.insert(0, temp_param[param_key])
                    temp_param[param_key] = list_type
                    matchers = create_case_pattern.findall(str(temp_param))
                    for matcher in matchers:
                        temp_param = str(temp_param).replace(str(matcher), str('\"'))
                    case_data['request_param'] = temp_param

                    value_type_transfer_to_list = str(api_id) + "中" + param_key + "的数字类型value值转变为list格式"
                    case_data['case_name'] = value_type_transfer_to_list

                    # 写入自动化用例文件
                    with open(auto_case, mode='a+', encoding='utf-8') as int_transfer_to_list:
                        int_transfer_to_list.write(str(case_data) + ",\n")


create_case()