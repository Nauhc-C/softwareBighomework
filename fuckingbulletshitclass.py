from pydantic import BaseModel
import _datetime


class admin_LOGIN(BaseModel):
    password: str


class admin_POWERON(BaseModel):
    pile_id: int


class admin_POWEROFF(BaseModel):
    pile_id: int


class admin_SETPRICE(BaseModel):
    low_price: float
    mid_price: float
    high_price: float


class admin_QUERYPILESTATE(BaseModel):
    pile_id: int


class admin_QUERYREPORT(BaseModel):
    pile_id: int
    start_date: str
    end_date: str


class admin_POWERCRASH(BaseModel):
    pile_id: int


class user_LOGIN(BaseModel):
    user_name: str
    password: str


class user_REGISTER(BaseModel):
    user_name: str
    password: str
    car_id: str
    car_capacity: float


class user_LOGOUT(BaseModel):
    user_id: str


class user_CHARGINGREQUEST(BaseModel):
    car_id: str
    request_amount: float
    request_mode: str


class user_QUERYCARSTATE(BaseModel):
    car_id: str


class user_CHANGECHARGINGMODE(BaseModel):
    car_id: str
    request_mode: str


class user_CHANGECHARGINGAMOUNT(BaseModel):
    car_id: str
    request_amount: float


class user_BEGINCHARGING(BaseModel):
    car_id: str


class user_GETCHARGINGSTATE(BaseModel):
    car_id: str


class user_ENDCHARGING(BaseModel):
    car_id: str


class user_CHANGECAPACITY(BaseModel):
    car_id: str
    car_capacity: float


class user_GETTOTALBILL(BaseModel):
    car_id: str
    bill_date: str


class user_GETDETAILBILL(BaseModel):
    bill_id: str


class user_GETPAYBILL(BaseModel):
    bill_id: str
