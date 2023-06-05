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
time_table = {}

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

def create_time_table(car_id):
    time_table[car_id] = _datetime.datetime.now()


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
        self.normal_pile = [0,1]
        self.fast_pile = [2,3,4]
        # 计费的价钱 谷时 平时 峰时
        self.low_price = 0
        self.mid_price = 0
        self.high_price = 0
        self.pile_pool = []


        #以下是等候区
        self.F_list = []
        self.T_list = []
        self.waiting_area = LimitedList(6)  #修改这个数字更改等候区容量
        #故障队列
        self.error_list=[]
        #实例化五个充电桩
        for i in range(len(self.normal_pile)+len(self.fast_pile)):
            if i in self.fast_pile:
                pile_temp = pile(i, charge_mode.T)
            else:
                pile_temp = pile(i, charge_mode.F)
            self.pile_pool.append(pile_temp)

    # 完成 扔到线程中的运行部分
    def run(self):
        while True:
            self.update()
            time.sleep(1)

    '''
    这里是所有与管理员有关的部分
    '''

    #  完成  查看充电桩状态(仅状态)
    def check_pile_state(self, id):
        state = self.pile_pool[id].pile_state()["working_state"]
        print(state)
        return state
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
    def check_pile_report(self):
        list=[]
        for i in self.pile_pool:
            list.append(i.pile_state())
        return list
    #返回充电桩数量
    def retPipeAmount(self):
        return [len(self.normal_pile)+len(self.fast_pile), self.normal_pile, self.fast_pile]
    #设置价格
    def setPrice(self, low, mid, high):
        for _pile in self.pile_pool:
            _pile.set_price(low,mid,high)
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
            _len = -1
            if _charge_mode == "T":
                self.T_list.append(o)
                o.init_num(len(self.T_list))
                _len = len(self.T_list)
            else:
                self.F_list.append(o)
                o.init_num(len(self.F_list))
                _len = len(self.F_list)
            create_time_table(car_id)
            return [1, _charge_mode, _len]
        except Exception as e:
            print(e)
            return [0]


    # 开始充电
    def start_charge(self, car_id):
        #监测是否在某个_pile队列的最前端
        flag = False
        for _pile in self.pile_pool:
            if (_pile.waiting_list != [] and _pile.waiting_list[0].car_id == car_id):
                #确实在
                flag = True
                _pile.remianing_total = _pile.waiting_list[0].request_amount
                _pile.waiting_list[0].set_state_on_charge()
                _pile.working_state = charging_pile_state.in_use
                creatOrder(car_id,_pile.waiting_list[0].request_amount,_pile.waiting_list[0].request_mode)
        return flag
    # 轮询查看订单状态
    def look_query(self, car_id):
        _order,x=self.from_carid_to_everything(car_id)
        _state=""
        if(_order.order_state==order_s.wait_area):
            _state="wait_area" #等候区
        elif(_order.order_state==order_s.wait_queue):
            _state="wait_queue"
        elif(_order.order_state==order_s.able_to_charge):
            _state="able_to_charge"
        else:
            _state="on_charge"

        if x in ["T"]: #处于等候区的状态
            return {
                "car_position": _state,
                "car_state": _state,
                "queue_num": _order.get_queue_num(),
                "request_time": time_table[car_id],
                "pile_id": None,
                "request_mode": "T",
                "request_amount": _order.request_amount
            }
        elif x == "F":
            return {
                "car_position": _state,
                "car_state": _state,
                "queue_num": _order.get_queue_num(),
                "request_time": _datetime.datetime.now(),
                "pile_id": None,
                "request_mode": "F",
                "request_amount": _order.request_amount
            }
        else:
            return {
                "car_position": _state,
                "car_state": _state,
                "queue_num": None,
                "request_time": time_table[car_id],
                "pile_id": x,
                "request_mode": _order.request_mode,
                "request_amount": _order.request_amount
            }


    # 修改充电模式
    # 返回True or False
    def modify_the_charging_mode(self, car_id, mode_to):
        order,x=self.from_carid_to_everything(car_id)
        if(x=="T" or x=="F"):  #说明当前订单仍然在等候区
            if(mode_to=="T"):
                order.request_mode = charge_mode.T
            else:
                order.request_mode = charge_mode.F
            self.requeue(car_id, order.request_amount, order.request_mode)
            return True

        else:
            return False

    # 修改充电量
    def modify_the_amount_of_charge(self, car_id, amount):
        order, x = self.from_carid_to_everything(car_id)
        if (x == "T" or x == "F"):  # 说明当前订单仍然在等候区
            order.request_amount=amount
            self.requeue(car_id,order.request_amount,order.request_mode)
            return True

        else:
            return False

    # 用于让某个车重新排队的函数, 调用这个函数的时候只会在order在等候区
    def requeue(self, car_id,amount,mode):
        order, x = self.from_carid_to_everything(car_id)
        if x == "T":
            self.T_list.remove(order)
        else:
            self.F_list.remove(order)
        self.waiting_area.remove(order)
        self.submit_a_charging_request(car_id,amount,mode)


    '''
    只有小bqww用的
    '''

    def if_car_in_charging(self, car_id):
        a, _ = self.from_carid_to_everything(car_id)
        if a!=None and a.order_state == order_s.on_charge:
            return True
        return False
    def car_in_wait(self, car_id):
        a,_ = self.from_carid_to_everything(car_id)
        if a!=None and a.order_state != order_s.on_charge:
            return True
        return False



    def setPrice(self, low, mid, high):
        self.low_price = low
        self.mid_price = mid
        self.high_price = high




    # 取消/结束充电
    def end_charge(self, car_id):
        flag = False
        # 判断是在充电区还是在等候区
        #在等候区
        for i in self.waiting_area:
            if i.car_id == car_id:
                flag = True
                # 在充电区
                if i.request_mode == charge_mode.T:
                    self.T_list.remove(i)
                else:
                    self.F_list.remove(i)
                self.waiting_area.remove(i)  # 在所有list中删除他即可
        #在充电区
        for _pile in self.pile_pool:
            if (_pile.waiting_list != [] and _pile.check_car_id(car_id) == 1): #充电桩中存在waiting
                flag = True
                _pile.waiting_list[0].order_state = order_s.on_charge
        pass

    '''
    其他自己用的函数
    '''

    ### 每次更新的内容
    def update(self):
        # 在当前order中有的时候触发调度
        Tflag,Fflag = self.is_waiting_list_available()
        # T类充电桩有空
        if Tflag == True:
            self.scheldur(charge_mode.T)
        if Fflag == True:
            self.scheldur(charge_mode.F)
        #更新所有时刻
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
                    if _pile.charge_mode == charge_mode.T and _pile.check_waiting_list_available():
                        _pile.append_waiting_list(self.T_list[0])
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
                    if _pile.charge_mode == charge_mode.F and _pile.check_waiting_list_available():
                        _pile.waiting_list.append(self.F_list[0])
                        break;
                self.F_list.remove(self.F_list[0])  # 在T_list中删除
                for i in self.F_list:  # 更新其他所有T_list中的id
                    i.update_num()
        self.PRINT()

    def PRINT(self):
        print("======================")
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
        print("PRINT_pile")
        for _pile in self.pile_pool:
            print(f"_pile={_pile.pile_id}")
            for i in _pile.waiting_list:
                print(f"i.car_id={i.car_id}", end=";")
            print("")
        print("======================")

    def PRINT_pile(self):
        print("PRINT_pile")
        for _pile in self.pile_pool:
            print(f"_pile={_pile.pile_id}")
            for i in _pile.waiting_list:
                print(f"i.car_id={i.car_id}", end=";")
            print("")
    #传入car_id, 返回他的订单和所在位置
    #如果在等候区返回对应的请求id, 如果在充电桩就返回对应的充电桩id
    def from_carid_to_everything(self,car_id):
        for i in self.T_list:
            if i.car_id==car_id:
                return i,"T"
        for i in self.F_list:
            if i.car_id==car_id:
                return i,"F"
        for _pile in self.pile_pool:
            for j in _pile.waiting_list:
                if j.car_id == car_id:
                    return j,str(_pile.pile_id)
        return None,None
    #查询waiting_list是否有空位
    def is_waiting_list_available(self):
        Fflag = False
        Tflag = False
        if self.waiting_area != []:
            # print("可以开始调度")
            for i in self.pile_pool:
                if i.charge_mode == charge_mode.T and i.check_waiting_list_available():
                    # print("   #T队列中有空")
                    Tflag = True
                if i.charge_mode == charge_mode.F and i.check_waiting_list_available():
                    ##print("   #F队列中有空")
                    Fflag = True  # F队列中有空
        return Tflag,Fflag



if __name__ == "__main__":
    creatOrder("ADX100", 123, 123)
    finishOrder("ADX100", 100, 110, 10, 50.1)
    a = pile_manager()
    a.start()
    test.test_create(a)
