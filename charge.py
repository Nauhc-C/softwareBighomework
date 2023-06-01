from enum import Enum
import threading
import time
### 注意所有变量都为下划线命名, 所有api都是驼峰命名

'''
全局变量
'''
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

class order():
    def __init__(self,car_id,request_amount,request_mode):
        self.car_id=car_id
        self.request_amount=request_amount
        self.request_mode=request_mode








# 充电桩的类
class pile():
    def __init__(self,id):
        self.pile_id=id
        self.working_state=charging_pile_state.close
        self.total_charge_num=0            #总计充电次数
        self.total_charge_time=0           #总计充电时间
        self.total_capacity=0              #总计充电量
        self.charge_mode=charge_mode.T     #充电模式
        self.order=None                    #外部传入的订单
        self.waiting_list=[]
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








#充电桩管理的类, 隔绝订单和充电桩的交互,
# 但是和前端无关(比如用户和管理员的查看充电桩状态在这里都是一个函数, 由其他人来区分
class pile_manager(threading.Thread):
    def __init__(self,pile_num=5):
        super().__init__()
        self.pile_pool = []
        for i in range(pile_num):
            pile_temp=pile(i)
            self.pile_pool.append(pile_temp)


        self.waiting_list=[]   #存点什么好呢

    #扔到线程中的运行部分
    def run(self):
        while True:
            self.update()
            time.sleep(1)
    '''
        这里是所有管理员和用户共用的部分
    '''
    #查看充电桩状态(仅状态)
    def check_pile_state(self,id):
        state=self.pile_pool[id].pile_state()["working_state"]
        print(state)
        return state

    '''
    这里是所有与管理员有关的部分
    '''
    #开启充电桩
    def open_pile(self):
        pass
    #关闭充电桩
    def close_pile(self):
        pass

    #查看充电桩报表(所有数据)
    def check_pile_report(self):
        state = self.pile_pool[id].pile_state()
        return state
    '''
    这里是所有与用户有关的部分
    '''
    #提交充电请求
    def submit_a_charging_request(self):
        pass
    #修改充电模式
    def modify_the_charging_mode(self):
        pass
    #修改充电量
    def modify_the_amount_of_charge(self):
        pass
    #开始充电
    def start_charge(self):
        pass
    #取消/结束充电
    def end_charge(self):
        pass
    '''
    其他自己用的函数
    '''
    def update(self):
        for i in self.pile_pool:
            i.update()

if __name__ == "__main__":
    a=pile_manager()
    a.start()
    time.sleep(1)
    a.check_pile_state(2)
