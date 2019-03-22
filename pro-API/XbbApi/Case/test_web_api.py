from BasicFun import basic
import pytest
from pymongo import MongoClient

mongodb_conn = MongoClient('127.0.0.1', 27017).Form_list0322


def get_all_case_name():
    name_list = []
    all_case_name_data = mongodb_conn["api_case"].find({}, {"_id":0, "case_name":"1"})
    for name in all_case_name_data:
        name_list.append(name['case_name'])
    return name_list


name_list = get_all_case_name()


@pytest.mark.parametrize('case_name', name_list)
def test_run_all_case(case_name):
    basic.exe_case(case_name)


if __name__ == "__main__":
    pytest.main()
