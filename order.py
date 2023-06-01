from enum import Enum
#订单状态的枚举类
class order_s(Enum):
    wait_area=0
    wait_queue=1
    on_charge=2

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


class order():
    def __init__(self,car_id,request_amount,request_mode):
        self.car_id=car_id
        self.request_amount=request_amount
        self.request_mode=request_mode
        self.order_num=0
        self.order_state=order_s.wait_area

    def init_num(self,id):
        self.order_num=id
    def update_num(self):
        self.order_num-=1
