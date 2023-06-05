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

        self.low_price = 0.4
        self.mid_price = 0.7
        self.high_price = 1.0
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
            print(f"pile:{self.pile_id}is use")
            self.total_charge_time+=1
            self.waiting_list[0].charge_time+=1
            if(self.charge_mode==charge_mode.T):
                self.remianing_total-=F_charge_per_second/3600
                self.total_capacity+=F_charge_per_second/3600
                self.waiting_list[0].electric_cost+=(F_charge_per_second/3600)*self.get_current_price()         #计费
                self.waiting_list[0].service_cost+=(F_charge_per_second/3600)*0.8
            else:
                self.remianing_total-=T_charge_per_second/3600
                self.total_capacity+=T_charge_per_second/3600
                self.waiting_list[0].electric_cost += (T_charge_per_second / 3600) * self.get_current_price()   #计费
                self.waiting_list[0].service_cost += (F_charge_per_second / 3600) * 0.8
            #以下是正常的状态的更新
            if(self.remianing_total<=0):
                self.over()

    def over(self):
        #首先停止充电
        self.working_state=charging_pile_state.idle
        #然后进入统计
        self.total_charge_num+=1








        #最后清除这一单
        self.waiting_list.remove(self.waiting_list[0])
        print("over")



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





