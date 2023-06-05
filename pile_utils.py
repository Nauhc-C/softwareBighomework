from enum import Enum

#订单状态的枚举类

class charge_mode(Enum):
    F=0
    T=1
class order_s(Enum):
    wait_area=0
    wait_queue=1
    able_to_charge=2
    on_charge=3
class charging_pile_state(Enum):
    close=1   #关闭
    idle=2    #空闲
    in_use=3  #使用中
    broke=4   #损坏

# 用于存储所有工具的工具类
class utils():
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
    #返回值的第一个是, T类有空闲, 第二个是F类有空
    def is_waiting_list_available(self):
        Fflag = False
        Tflag = False
        if self.waiting_area != []:
            # print("可以开始调度")
            for i in self.pile_pool:
                if i.charge_mode == charge_mode.T and i.check_waiting_list_available() and i.working_state==charging_pile_state.idle:
                    # print("   #T队列中有空")
                    Tflag = True
                if i.charge_mode == charge_mode.F and i.check_waiting_list_available() and i.working_state==charging_pile_state.idle:
                    ##print("   #F队列中有空")
                    Fflag = True  # F队列中有空
        return Tflag,Fflag