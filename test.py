import time

def test_create(a):
    time.sleep(1)
    print(a.submit_a_charging_request(2, 100, "T"))
    a.PRINT()
    time.sleep(1)
    print(a.submit_a_charging_request(6, 100, "F"))
    a.PRINT()
    time.sleep(1)
    print(a.start_charge(6))
    print(a.submit_a_charging_request(7, 100, "T"))
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

    print(a.check_pile_report(1))


