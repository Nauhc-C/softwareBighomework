import time

def test_create(a):
    time.sleep(1)
    print(a.submit_a_charging_request("2", 100, "T"))
    a.PRINT()
    time.sleep(1)
    print(a.submit_a_charging_request("12332", 100, "F"))
    a.PRINT()
    time.sleep(1)
    print(a.start_charge(6))
    print(a.submit_a_charging_request("asdasd", 100, "T"))
    a.PRINT()
    time.sleep(1)
    print(a.submit_a_charging_request(1, 100, "F"))
    a.PRINT()
    time.sleep(1)
    print(a.submit_a_charging_request(4, 100, "T"))
    time.sleep(1)
    print(a.submit_a_charging_request(11, 100, "T"))
    time.sleep(1)
    print(a.submit_a_charging_request(13, 100, "T"))
    time.sleep(1)
    print(a.submit_a_charging_request(17, 100, "T"))
    time.sleep(1)
    print(a.submit_a_charging_request(19, 100, "T"))
    print(a.waiting_area)

    #print(a.check_pile_report(1))

def test_over(a):
    a.submit_a_charging_request("A", 0.016, "T")
    time.sleep(3)
    a.start_charge("A")
    time.sleep(10)
    print(a.if_car_in_charging("A"))
    print(a.view_billing("A"))

def test_cancel(a):
    a.submit_a_charging_request("A", 0.016, "T")
    time.sleep(3)
    a.end_charge("A")
    a.start_charge("A")
    time.sleep(3)

    time.sleep(10)

def test_pile_open_or_close(a):
    time.sleep(2)
    a.close_pile(2)
    time.sleep(2)
    a.close_pile(2)
    time.sleep(2)
    a.open_pile(2)
    time.sleep(2)

# 测试充电桩数量的
def test_pile_num(a):
    time.sleep(2)
    print(a.retPipeAmount())



def test_pile_broke(a):
    time.sleep(2)
    a.set_pile_error(2)
    time.sleep(2)
    a.set_pile_not_error(2)
    time.sleep(2)


def test_mofity_fee(a):
    time.sleep(3)
    a.submit_a_charging_request("A", 0.5, "T")
    time.sleep(2)
    a.start_charge("A")
    time.sleep(3)
    print(a.view_billing("A"))
    a.setPrice(1000000,2000000,3000000)
    time.sleep(3)
    print(a.view_billing("A"))
# 测试同时给和一段时间内的值
def test_big(a):
    time.sleep(1)
    a.submit_a_charging_request("A", 0.016, "T")
    time.sleep(0.02)
    a.submit_a_charging_request("123", 0.016, "T")
    time.sleep(3)
    a.start_charge("A")
    a.start_charge("123")
    time.sleep(3)
    time.sleep(2)
    print(a.queryReport(2, 2, 9))

def test_last_year(a):
    a.submit_a_charging_request("V1",0.040,"T")
    time.sleep(5)
    a.start_charge("V1")
    a.submit_a_charging_request("V2",0.030,"T")
    time.sleep(5)
    a.start_charge("V2")
    a.submit_a_charging_request("V3", 0.100, "F")
    time.sleep(5)
    a.start_charge("V3")
    a.submit_a_charging_request("V4", 0.120, "F")
    time.sleep(5)
    a.end_charge("V2")
    time.sleep(5)
    a.start_charge("V4")
    a.submit_a_charging_request("V5", 0.020, "T")
    time.sleep(5)
    a.start_charge("V5")
    a.submit_a_charging_request("V6", 0.020, "T")
    time.sleep(5)
    a.start_charge("V6")
    a.submit_a_charging_request("V7", 0.0110, "F")
    time.sleep(5)
    a.start_charge("V7")
    a.submit_a_charging_request("V8", 0.020, "T")
    time.sleep(5)
    a.start_charge("V8")