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
        self.is_open=False
        self.working_state=charging_pile_state.close
        self.total_charge_num=0            #总计充电次数
        self.total_charge_time=0           #总计充电时间
        self.total_capacity=0              #总计充电量
        self.charge_mode=_charge_mode      #充电模式
        self.order=None                    #外部传入的订单
        self.remianing_total=0
        self.waiting_list=LimitedList(2)
    #返回所有状态
    def pile_state(self):
        info_dict = {
            "pile_id": self.pile_id,
            "working_state": self.working_state,
            "total_charge_num": self.total_charge_num,
            "total_charge_time": self.total_charge_time,
            "total_capacity": self.total_capacity,
            "charge_mode": self.charge_mode
        }
        return info_dict

    def update(self):
        #只有运行中的需要更新
        if self.working_state==charging_pile_state.in_use:
            self.total_charge_time+=1
            if(self.charge_mode==charge_mode.T):
                self.remianing_total-=30
            else:
                self.remianing_total-=7



            #以下是正常的状态的更新
            if(self.remianing_total<=0):
                self.over(self.remianing_total)

    def over(self,more):
        self.working_state=charging_pile_state.idle
        self.waiting_list.remove(self.waiting_list[0])



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





