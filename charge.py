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

import pile_utils

### 注意所有变量都为下划线命名, 所有api都是驼峰命名
engine = create_engine('sqlite:///instance/user')
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


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
class MyTime(threading.Thread):

    def __init__(self):
        super().__init__()
        self.mydate = _datetime.datetime(2023, 6, 5, 7, 50, 00, 00)

    def run(self):
        while True:
            self.mydate = self.mydate + _datetime.timedelta(seconds=20)
            time.sleep(1)

    def getData(self):
        return self.mydate.date()

    def getDataTime(self):
        return self.mydate


myTime = MyTime()
myTime.start()

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
    start_time = Column(DateTime, nullable=False, default=myTime.getDataTime())
    end_time = Column(DateTime, default=None)
    bill_date = Column(Date, nullable=False, default=myTime.getData())


    def __init__(self, car_id, charge_amount, pile_id):
        self.car_id = car_id
        self.charge_amount = charge_amount
        self.pile_id = pile_id
        m = hashlib.md5()
        m.update((car_id + str(pile_id) + myTime.getDataTime().isoformat()).encode(encoding="utf-8"))
        self.bill_id = m.hexdigest()
        self.start_time = myTime.getDataTime()
        self.bill_date = myTime.getData()
        car_table[car_id] = self.bill_id

car_table = {}
time_table = {}

# 给SLC用的
def creatOrder(car_id, charge_amount, pile_id):
    session.add(Order(car_id, charge_amount, pile_id))
    session.commit()
# 需要提供充电时长，服务费，充电费，总费用
def finishOrder(car_id, service_fee, total_fee, charge_fee, charge_duration):
    session.query(Order).filter_by(bill_id=car_table.get(car_id)).update({"total_fee": total_fee, "total_service_fee": service_fee, "total_charge_fee": charge_fee, "charge_duration": charge_duration, "end_time": myTime.getDataTime()})
    session.commit()
def findBillId(car_id):
    return car_table[car_id]
def create_time_table(car_id):
    time_table[car_id] = myTime.getDataTime()


'''
======================================================================================================================================
'''

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

        self.strategy="a"    #a,b,c分别代表一种调度策略

        #以下是等候区
        self.F_list = []
        self.T_list = []
        self.waiting_area = LimitedList(6)  #修改这个数字更改等候区容量
        #故障队列
        self.error_list_T=[]
        self.error_list_F = []
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
    # 完成  开启充电桩
    def open_pile(self, id):
        for i in self.pile_pool:
            if i.pile_id == id and i.working_state==charging_pile_state.close:
                i.working_state=charging_pile_state.idle
            if i.pile_id == id and i.working_state==charging_pile_state.broke:
                i.set_not_error()
        pass
    # 完成   关闭充电桩
    def close_pile(self, id):
        print(f"close_pile id = {id}")
        for i in self.pile_pool:
            if i.pile_id == id and i.working_state==charging_pile_state.idle:
                i.working_state=charging_pile_state.close
        pass


    #设置充电桩故障/非故障
    def set_pile_error(self,id):
        print("set broke")
        for i in self.pile_pool:
            if i.pile_id == id:
                i.set_error()
        pass

    # 查看充电桩报表(所有数据)
    def check_pile_report(self):
        list=[]
        for i in self.pile_pool:
            list.append(i.pile_state())
        return list
    #查看充电桩一段时间内的数据
    def queryReport(self,id,start_time,end_time):
        for _pile in self.pile_pool:
            if _pile.pile_id == id:
                return _pile.queryReport()



    #返回充电桩数量
    def retPipeAmount(self):
        return [len(self.normal_pile)+len(self.fast_pile), self.normal_pile, self.fast_pile]
    #设置价格
    def setPrice(self, low, mid, high):
        print(f"low={low}")
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
                #creatOrder(car_id,_pile.waiting_list[0].request_amount,_pile.pile_id)
        return flag
    # 轮询查看订单状态
    def look_query(self, car_id):
        _order,x=self.from_carid_to_everything(car_id)
        _state=""
        if(_order.order_state==order_s.wait_area):
            _state="处于等待区" #等候区
        elif(_order.order_state==order_s.wait_queue):
            _state="处于充电区"
        elif(_order.order_state==order_s.able_to_charge):
            _state="允许充电"
        else:
            _state="正在充电"
        if _order.request_mode == charge_mode.T:
            _mode="T"
        else:
            _mode="F"
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
                "request_time": time_table[car_id],
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
                "request_mode": _mode,
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
    def requeue(self, car_id,amount,mode,position='area'):
        if position == 'area':
            print(f"charge--requeue mode={mode}")
            order, _ = self.from_carid_to_everything(car_id)
            if mode == charge_mode.T:
                self.T_list.remove(order)
            elif mode == charge_mode.F:
                self.F_list.remove(order)
            self.waiting_area.remove(order)
            self.submit_a_charging_request(car_id,amount,mode)
        elif position=='pile':
            self.submit_a_charging_request(car_id, amount, mode)
    #用于查看订单
    def view_billing(self, car_id):
        try:
            order,_=self.from_carid_to_everything(car_id)
            _,pile = self.from_carid_to_everything(car_id)
            a = order.get_cost()
            a["pip_id"] = pile
            return a
        except Exception as e:
            print(e)
            return None
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



    # 取消/结束充电
    def end_charge(self, car_id):
        #print(f"charge--end_charge")
        flag = False
        _order,_ = self.from_carid_to_everything(car_id)
        # 判断是在充电区还是在等候区
        #在等候区
        for i in self.waiting_area:
            if i.car_id == car_id:
                flag = True
                if i.request_mode == charge_mode.T:
                    self.T_list.remove(i)
                else:
                    self.F_list.remove(i)
                self.waiting_area.remove(i)  # 在所有list中删除他即可
                #print(f"charge--end_charge in waiting area")
        #在充电区
        for _pile in self.pile_pool:
            if (_pile.waiting_list != [] and _pile.check_car_id(car_id) == 0): #充电桩中存在waiting且当前car_id在第一位
                flag = True
                #print(f"charge--end_charge 定位到充电桩{_pile.pile_id}")
                if _pile.waiting_list[0].order_state == order_s.on_charge:#正在充电则结束充电
                    #print(f"charge--end_charge on charge")
                    _pile.over()
                elif  _pile.waiting_list[0].order_state == order_s.able_to_charge: #还没充电就消除这一单然后去排队
                    _pile.waiting_list.remove(_order)
                    #print(f"charge--end_charge car_id={car_id}  "
                    #      f"_order.request_amount={_order.request_amount}   "
                    #      f"_order.request_mode={_order.request_mode}")
                    #self.requeue(car_id,_order.request_amount,_order.request_mode,'pile')


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
        self.PRINT()


    def get_broke_list(self):
        Tbroke=False
        Fborke=False
        for _pile in self.pile_pool:
            if len(_pile.broke_list)>0:  #当前的充电桩存在brokelist
                for i in _pile.broke_list:
                    if i.request_mode == charge_mode.T:
                        Tbroke=True
                    else:
                        Fborke=True
        return Tbroke,Fborke
    #将所有的转移到error_list中
    def append_broke_list(self):
        for _pile in self.pile_pool:
            if len(_pile.broke_list)>0:  #当前的充电桩存在brokelist
                for i in _pile.broke_list:
                    if i.request_mode == charge_mode.T:
                        self.error_list_T.append(i)
                    else:
                        self.error_list_F.append(i)

    #将所有的重新排队
    def requeue_broke(self):
        for _pile in self.pile_pool:
            if len(_pile.broke_list)>0:  #当前的充电桩存在brokelist
                for i in _pile.broke_list:
                    self.requeue(i.car_id,i.request_amount,i.request_mode)  #重新排队

    def scheldur_T(self):
        if (self.error_list_T != []):   #调度error_T里的
            self.error_list_T[0].order_state == order_s.wait_queue
            # 添加到充电桩的waiting_list中
            for _pile in self.pile_pool:
                if _pile.charge_mode == charge_mode.T and _pile.check_waiting_list_available():
                    _pile.append_waiting_list(self.error_list_T[0])
                    break
            self.error_list_T.remove(self.error_list_T[0])  # 在error_T中删除
        elif (self.T_list != []):
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

    def scheldur_F(self):
        if (self.error_list_F != []):   #调度error_F里的 , 并且不动别处的
            self.error_list_F[0].order_state == order_s.wait_queue
            # 添加到充电桩的waiting_list中
            for _pile in self.pile_pool:
                if _pile.charge_mode == charge_mode.F and _pile.check_waiting_list_available():
                    _pile.append_waiting_list(self.error_list_F[0])
                    break
            self.error_list_F.remove(self.error_list_F[0])  # 在error_F中删除
        elif (self.F_list != []):
            self.waiting_area.remove(self.F_list[0])  # 在等候区删除
            self.F_list[0].order_state == order_s.wait_queue
            # 添加到充电桩的waiting_list中
            for _pile in self.pile_pool:
                if _pile.charge_mode == charge_mode.F and _pile.check_waiting_list_available():
                    _pile.append_waiting_list(self.F_list[0])
                    break;
            self.F_list.remove(self.F_list[0])  # 在T_list中删除
            for i in self.F_list:  # 更新其他所有T_list中的id
                i.update_num()
    # 调度充电桩
    #
    def scheldur(self, _charge_mode):
        #判断是否存在没被收集的broke
        #放置在broke列表里, 然后调度时先去把broke列表里的调度了


        if self.strategy=="a":   #调度策略 优先级调度
            T,F=self.get_broke_list()
            if(T or F):
                self.append_broke_list()
            if (_charge_mode == charge_mode.T):  # 处理T类
                self.scheldur_T()
            if (_charge_mode == charge_mode.F):  # 处理T类
                self.scheldur_F()
        elif self.strategy=="b":   #调度策略  时间顺序调度
            T, F = self.get_broke_list()
            if (T or F):
                self.requeue_broke()
            if (_charge_mode == charge_mode.T):  # 处理T类
                self.scheldur_T()
            if (_charge_mode == charge_mode.F):  # 处理T类
                self.scheldur_F()
        elif self.strategy=="c":   #调度策略    故障回复调度
            pass



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
                        _pile.append_waiting_list(self.F_list[0])
                        break;
                self.F_list.remove(self.F_list[0])  # 在T_list中删除
                for i in self.F_list:  # 更新其他所有T_list中的id
                    i.update_num()
        #self.PRINT()

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
            print(f"_pile={_pile.pile_id},work_state={_pile.working_state}")
            for i in _pile.waiting_list:
                print(f"i.car_id={i.car_id}", end=";")

            print("")
        print("======================")

'''
====================================================================================================================================
'''
from enum import Enum

#限制最多元素个数的list, 重写list
class LimitedList(list):
    def __init__(self, limit, *args, **kwargs):
        self.limit = limit
        super().__init__(*args, **kwargs)
    def append(self, elem):
        if len(self) < self.limit:
            super().append(elem)
        else:
            raise ValueError("List is full.")
class order_s(Enum):
    wait_area=0
    wait_queue=1
    able_to_charge=2
    on_charge=3


#充电速度
F_charge_per_second=30
T_charge_per_second=7

#充电桩状态的枚举类
class charging_pile_state(Enum):
    close=1   #关闭
    idle=2    #空闲
    in_use=3  #使用中
    broke=4   #损坏
#充电模式的枚举类
class charge_mode(Enum):
    F=0
    T=1



# 充电桩的类
class pile():
    def __init__(self,id,_charge_mode):
        self.pile_id=id
        self.is_open=True
        self.working_state=charging_pile_state.idle
        self.total_charge_num=0            #总计充电次数
        self.total_charge_time=0           #总计充电时间
        self.total_capacity=0              #总计充电量
        self.charge_mode=_charge_mode      #充电模式
        self.remianing_total=0
        self.waiting_list=LimitedList(2)   #充电区的两个位置(如果需要更改就直接改这里即可)

        self.broke_list=[]
        self.history_list=[[0,0,0,0,0,0]]
        self.low_price = 0.4
        self.mid_price = 0.7
        self.high_price = 1.0

    def set_error(self):
        self.working_state=charging_pile_state.broke  #设置为损坏状态
        for i in self.waiting_list:
            self.broke_list.append(i)  #把目前waiting_list中的全都复制到broke_list中
        if len(self.waiting_list) > 0:
            self.over()  # 结束当前订单
    def set_not_error(self):
        self.working_state=charging_pile_state.idle
    #返回所有状态
    def pile_state(self):
        if self.working_state == charging_pile_state.idle:
            _state="空闲"
        elif self.working_state == charging_pile_state.in_use:
            _state="使用中"
        elif self.working_state == charging_pile_state.broke:
            _state="损坏"
        elif self.working_state == charging_pile_state.close:
            _state="关闭"

        if self.charge_mode==charge_mode.T:
            _mode='T'
        else:
            _mode='F'

        info_dict = {
            "pile_id": self.pile_id,
            "working_state": _state,
            "total_charge_num": self.total_charge_num,
            "total_charge_time": self.total_charge_time,
            "total_capacity": self.total_capacity,
            "charge_mode": _mode
        }
        return info_dict

    def update(self):
        over=0
        amount=0
        charge_cost=0
        service_cost=0
        #只有运行中的需要更新
        if self.working_state==charging_pile_state.in_use:
            print(f"pile:{self.pile_id}is use")
            self.total_charge_time+=1
            self.waiting_list[0].charge_time+=1
            if(self.charge_mode==charge_mode.T):
                amount=T_charge_per_second/3600
                self.remianing_total-=T_charge_per_second/3600
                self.total_capacity+=T_charge_per_second/3600
                self.waiting_list[0].electric_cost+=(T_charge_per_second/3600)*self.get_current_price()         #计费
                charge_cost=(T_charge_per_second/3600)*self.get_current_price()
                self.waiting_list[0].service_cost+=(T_charge_per_second/3600)*0.8
                service_cost=(T_charge_per_second/3600)*0.8
            else:
                amount = F_charge_per_second / 3600
                self.remianing_total-=F_charge_per_second/3600
                self.total_capacity+=F_charge_per_second/3600
                self.waiting_list[0].electric_cost += (F_charge_per_second / 3600) * self.get_current_price()   #计费
                charge_cost = (F_charge_per_second / 3600) * self.get_current_price()
                self.waiting_list[0].service_cost += (F_charge_per_second / 3600) * 0.8
                charge_cost = (F_charge_per_second / 3600) * self.get_current_price()
            #以下是正常的状态的更新
            if(self.remianing_total<=0):
                self.over()
                over=1
        #每帧更新
        self.history_list.append([over,1,amount,charge_cost,service_cost,charge_cost+service_cost])


    def over(self):
        #首先停止充电
        self.working_state=charging_pile_state.idle
        #然后进入统计
        self.total_charge_num+=1

        #最后清除这一单
        self.waiting_list.remove(self.waiting_list[0])
        print("over")
        finishOrder(self.waiting_list[0].car_id,
                    self.waiting_list[0].service_cost,
                    self.waiting_list[0].total_cost,
                    self.waiting_list[0].charge_cost,
                    self.waiting_list[0].charge_time)



    def check_waiting_list_available(self):
        if len(self.waiting_list)==1 or len(self.waiting_list)==0:
            return True
        else:
            return False

    def check_car_id(self,car_id):
        count=0
        for i in self.waiting_list:
            if i.car_id==car_id:
                break
            count+=1
        return count
    #塞进等候区
    def append_waiting_list(self,order):
        self.waiting_list.append(order)
        if(len(self.waiting_list)==1):  #如果是第一个
            order.set_state_able_to_charge()
        else:
            order.set_state_wait_queue()

    def get_current_price(self):
        import datetime

        now = datetime.datetime.now()  # 获取当前时间
        if 7 <= now.hour < 10:
            return self.mid_price
        elif 10 <= now.hour < 15:
            return self.high_price
        elif 15 <= now.hour < 18:
            return self.mid_price
        elif 18 <= now.hour < 21:
            return self.high_price
        elif 21 <= now.hour < 23:
            return self.mid_price
        else:
            return self.low_price

    def set_price(self,low,mid,high):
        self.low_price=low
        self.mid_price=mid
        self.high_price=high

    def queryReport(self,start,end):
        total_charge_num=0
        total_charge_time=0
        total_capacity=0
        total_charge_fee=0
        total_service_fee=0
        total_fee=0
        for i in self.history_list[start:end]:
            total_charge_num+=i[0]
            total_charge_time+=i[1]
            total_capacity +=i[2]
            total_charge_fee+=i[3]
            total_service_fee+=i[4]
            total_fee +=i[5]

        return {
            "total_charge_num":total_charge_num,              #累计充电次数
            "total_charge_time": total_charge_time ,           #累计充电时长(小时)
            "total_capacity":  total_capacity ,             #累计充电电量
            "total_charge_fee":   total_charge_fee   ,        #充电费
            "total_service_fee":   total_service_fee  ,        #服务费
            "total_fee":   total_fee   ,               #总费用
            "start_date":    start  ,              #开始时间
            "end_date":   end                   #结束时间
        }





if __name__ == "__main__":
    #creatOrder("ADX100", 123, 123)
    #finishOrder("ADX100", 100, 110, 10, 50.1)
    a = pile_manager()
    a.start()
    test.test_mofity_fee(a)
