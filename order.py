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

#订单状态的枚举类
class order_s(Enum):
    wait_area=0
    wait_queue=1
    able_to_charge=2
    on_charge=3

class charge_mode(Enum):
    F=0
    T=1



# 这里的order为每个充电的实质
class order():
    def __init__(self,car_id,request_amount,request_mode):
        self.car_id=car_id
        self.request_amount=request_amount
        self.request_mode=request_mode
        self.order_num=0
        self.order_state=order_s.wait_area
        self.fee=0

    def init_num(self,id):
        self.order_num=id
    def update_num(self):
        self.order_num-=1

    def get_queue_num(self):
        if self.request_mode==charge_mode.T:
            return f"T{self.order_num}"
        else:
            return f"F{self.order_num}"
    #设置订单状态是waiting_queue, 目前只应该在调度进充电区的时候调用(写了)
    def set_state_wait_queue(self):
        self.order_state=order_s.wait_queue
    #设置订单状态为可以充电,应该在
    #上一个订单结束
    #调度进充电区(写了)     的时候被调用
    def set_state_able_to_charge(self):
        self.order_state = order_s.able_to_charge
    #设置.......为正在充电
    #在开始充电时调用
    def set_state_on_charge(self):
        self.order_state = order_s.on_charge
