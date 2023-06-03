from enum import Enum
import threading
import time
import test
import _datetime
import hashlib
from pile import *
from order import *
from sqlalchemy import *
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

### 注意所有变量都为下划线命名, 所有api都是驼峰命名
engine = create_engine('sqlite:///instance/user')
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


class Order(Base):
    __tablename__ = "order"
    bill_id = Column(String(50), primary_key=True, nullable=False)
    car_id = Column(String(20))
    pile_id = Column(Integer)
    charge_amount = Column(Float)
    charge_duration = Column(Float)
    total_charge_fee = Column(Float, default=0)
    total_service_fee = Column(Float, default=0)
    total_fee = Column(Float, default=0)
    pay_state = Column(Integer, default=0)
    start_time = Column(DateTime, nullable=False, default=_datetime.datetime.now())
    end_time = Column(DateTime, default=None)
    bill_date = Column(Date, nullable=False, default=_datetime.date.today())


    def __init__(self, car_id, charge_amount, pile_id):
        self.car_id = car_id
        self.charge_amount = charge_amount
        self.pile_id = pile_id
        m = hashlib.md5()
        m.update((car_id + str(pile_id) + _datetime.datetime.now().isoformat()).encode(encoding="utf-8"))
        self.bill_id = m.hexdigest()
        car_table[car_id] = self.bill_id

car_table = {}

# 给SLC用的
def creatOrder(car_id, charge_amount, pile_id):
    session.add(Order(car_id, charge_amount, pile_id))
    session.commit()

# 需要提供充电时长，服务费，充电费，总费用
def finishOrder(car_id, service_fee, total_fee, charge_fee, charge_duration):
    session.query(Order).filter_by(bill_id=car_table.get(car_id)).update({"total_fee": total_fee, "total_service_fee": service_fee, "total_charge_fee": charge_fee, "charge_duration": charge_duration, "end_time": _datetime.datetime.now()})
    session.commit()

def findBillId(car_id):
    return car_table[car_id]

    '''
全局变量
'''


# 限制最多元素个数的list, 重写list
class LimitedList(list):
    def __init__(self, limit, *args, **kwargs):
        self.limit = limit
        super().__init__(*args, **kwargs)

    def append(self, elem):
        if len(self) < self.limit:
            super().append(elem)
        else:
            raise ValueError("List is full.")


# 充电桩管理的类, 隔绝订单和充电桩的交互,
# 但是和前端无关(比如用户和管理员的查看充电桩状态在这里都是一个函数, 由其他人来区分
class pile_manager(threading.Thread):
    def __init__(self, pile_num=5):
        super().__init__()
        self.pile_num = pile_num
        # 把这两个填上， 数组里面为充电桩编号 int
        self.normal_pile = []
        self.fast_pile = []
        # 计费的价钱 谷时 平时 峰时
        self.low_price = 0
        self.mid_price = 0
        self.high_price = 0
        self.pile_pool = []
        for i in range(pile_num):
            if i < 2:
                pile_temp = pile(i, charge_mode.T)
            else:
                pile_temp = pile(i, charge_mode.F)
            self.pile_pool.append(pile_temp)
        self.F_list = []
        self.T_list = []
        self.waiting_area = LimitedList(6)

    # 扔到线程中的运行部分
    def run(self):
        while True:
            self.update()
            time.sleep(1)

    '''
        这里是所有管理员和用户共用的部分
    '''

    # 查看充电桩状态(仅状态)
    def check_pile_state(self, id):
        state = self.pile_pool[id].pile_state()["working_state"]
        print(state)
        return state

    '''
    这里是所有与管理员有关的部分
    '''

    # 开启充电桩
    def open_pile(self, id):
        for i in self.pile_pool:
            if (i.pile_id == id):
                i.is_open = True
        pass

    # 关闭充电桩
    def close_pile(self, id):
        for i in self.pile_pool:
            if i.pile_id == id:
                i.is_open = False
        pass

    # 查看充电桩报表(所有数据)
    def check_pile_report(self, id):
        state = self.pile_pool[id].pile_state()
        return state

    '''
    这里是所有与用户有关的部分
    '''

    # 提交充电请求
    def submit_a_charging_request(self, car_id, request_amount, _charge_mode):
        if _charge_mode == "T":
            o = order(car_id, request_amount, charge_mode.T)
        else:
            o = order(car_id, request_amount, charge_mode.F)
        try:
            self.waiting_area.append(o)
            len = -1
            if _charge_mode == "T":
                self.T_list.append(o)
                o.init_num(len(self.T_list))
                len = len(self.T_list)
            else:
                self.F_list.append(o)
                o.init_num(len(self.F_list))
                len = len(self.F_list)

            return [1, _charge_mode, len]
        except Exception as e:
            print(e)
            return [0]

    # 修改充电模式
    # 返回True or False
    def modify_the_charging_mode(self, car_id, mode):
        pass

    # 修改充电量
    def modify_the_amount_of_charge(self, car_id, amount):
        pass

    # return True or False
    def if_car_in_charging(self, car_id):
        pass

    def car_in_wait(car_id):
        pass

    #返回[pile_id, charge_duration, 充电费， 服务费， 总费用]
    def look_charge_state(self, car_id):
        pass
    def retPipeAmount(self):
        return [self.pile_num, self.normal_pile, self.fast_pile]

    def look_query(self, car_id):
        return {
            "car_position": None,
            "car_state": None,
            "queue_num": None,
            "request_time": _datetime.datetime.now(),
            "pile_id": None,
            "request_mode": None,
            "request_amount": None

        }

    def setPrice(self, low, mid, high):
        self.low_price = low
        self.mid_price = mid
        self.high_price = high


    # 开始充电
    def start_charge(self, car_id):
        flag = False
        for _pile in self.pile_pool:
            if (_pile.waiting_list != [] and _pile.waiting_list[0].car_id == car_id):
                flag = True
                _pile.remianing_total = _pile.waiting_list[0].request_amount
                _pile.waiting_list[0].order_state = order_s.on_charge
                _pile.working_state = charging_pile_state.in_use
        return flag

    # 取消/结束充电
    def end_charge(self, car_id):
        flag = False
        # 判断是在充电区还是在等候区
        for i in self.waiting_area:
            if i.car_id == car_id:
                flag = True
                # 在充电区
                if i.request_mode == charge_mode.T:
                    self.T_list.remove(i)
                else:
                    self.F_list.remove(i)
                self.waiting_area.remove(i)  # 在所有list中删除他即可

        for _pile in self.pile_pool:
            if (_pile.waiting_list != [] and _pile.check_car_id(car_id) != 2):
                flag = True
                _pile.waiting_list[0].order_state = order_s.on_charge

        pass

    '''
    其他自己用的函数
    '''

    ### 每次更新的内容
    def update(self):
        Fflag = False
        Tflag = False
        # 在当前order中有的时候触发调度
        if self.waiting_area != []:
            # print("可以开始调度")
            for i in self.pile_pool:
                if i.charge_mode == charge_mode.T and i.check_waiting_list():
                    # print("   #T队列中有空")
                    Tflag = True
                if i.charge_mode == charge_mode.F and i.check_waiting_list():
                    ##print("   #F队列中有空")
                    Fflag = True  # F队列中有空
        # T类充电桩有空
        if Tflag == True:
            self.scheldur(charge_mode.T)
        if Fflag == True:
            self.scheldur(charge_mode.F)

        for i in self.pile_pool:
            i.update()

    # 调度充电桩
    def scheldur(self, _charge_mode):

        if (_charge_mode == charge_mode.T):  # 处理T类
            print("T类调度")
            if (self.T_list != []):
                self.waiting_area.remove(self.T_list[0])  # 在等候区删除
                self.T_list[0].order_state == order_s.wait_queue
                # 添加到充电桩的waiting_list中
                for _pile in self.pile_pool:
                    if _pile.charge_mode == charge_mode.T and _pile.check_waiting_list():
                        _pile.waiting_list.append(self.T_list[0])
                        break
                self.T_list.remove(self.T_list[0])  # 在T_list中删除
                for i in self.T_list:  # 更新其他所有T_list中的id
                    i.update_num()
        if (_charge_mode == charge_mode.F):  # 处理T类
            print("F类调度")
            if (self.F_list != []):
                self.waiting_area.remove(self.F_list[0])  # 在等候区删除
                self.F_list[0].order_state == order_s.wait_queue
                # 添加到充电桩的waiting_list中
                for _pile in self.pile_pool:
                    if _pile.charge_mode == charge_mode.F and _pile.check_waiting_list():
                        _pile.waiting_list.append(self.F_list[0])
                        break;
                self.F_list.remove(self.F_list[0])  # 在T_list中删除
                for i in self.F_list:  # 更新其他所有T_list中的id
                    i.update_num()

        self.PRINT()

    def PRINT(self):
        print("PRINT_pile")
        for _pile in self.pile_pool:
            print(f"_pile={_pile.pile_id}")
            for i in _pile.waiting_list:
                print(f"i.car_id={i.car_id}", end=";")
            print("")
        pass
        '''
        print("current waiting_area")
        for i in self.waiting_area:
            print(i.car_id,end=";")
            print(i.request_mode,end=";")
            print(i.order_num)
        print("====")
        print("current T_list")
        for i in self.T_list:
            print(i.car_id,end=";")
            print(i.request_mode,end=";")
            print(i.order_num)
        print("====")
        print("current F_list")
        for i in self.F_list:
            print(i.car_id,end=";")
            print(i.request_mode,end=";")
            print(i.order_num)
        print("====")
        '''

        '''
                self.car_id=car_id
        self.request_amount=request_amount
        self.request_mode=request_mode
        self.order_num=0
        self.order_state=order_s.wait_area
        '''
        # print(f"waiting_area={self.waiting_area}")

    def PRINT_pile(self):
        print("PRINT_pile")
        for _pile in self.pile_pool:
            print(f"_pile={_pile.pile_id}")
            for i in _pile.waiting_list:
                print(f"i.car_id={i.car_id}", end=";")
            print("")


if __name__ == "__main__":
    creatOrder("ADX100", 123, 123)
    finishOrder("ADX100", 100, 110, 10, 50.1)
    a = pile_manager()
    a.start()
    test.test_create(a)
