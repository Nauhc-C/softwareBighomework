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