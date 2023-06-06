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

    def __init__(self):
        pass