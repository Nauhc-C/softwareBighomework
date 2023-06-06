# -*-coding:utf-8-*-
import os
import time
import threading
import hashlib
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import _datetime
from charge import pile_manager, findBillId, myTime, MyTime, time_table
from flask_cors import CORS

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user'

db = SQLAlchemy(app)



class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    user_name = db.Column(db.String(20))
    password = db.Column(db.String(200))
    car_id = db.Column(db.String(20))
    car_capacity = db.Column(db.Float)

    def __init__(self, user_name, password, car_id, car_capacity):
        self.user_name = user_name
        self.password = password
        self.car_id = car_id
        self.car_capacity = car_capacity


class Order(db.Model):
    __tablename__ = "order"
    bill_id = db.Column(db.String(50), primary_key=True, nullable=False)
    car_id = db.Column(db.String(20))
    pile_id = db.Column(db.Integer)
    charge_amount = db.Column(db.Float)
    charge_duration = db.Column(db.Float)
    total_charge_fee = db.Column(db.Float, default=0)
    total_service_fee = db.Column(db.Float, default=0)
    total_fee = db.Column(db.Float, default=0)
    pay_state = db.Column(db.Integer, default=0)
    start_time = db.Column(db.DateTime, nullable=False, default=myTime.getDataTime())
    end_time = db.Column(db.DateTime, default=None)
    bill_date = db.Column(db.Date, nullable=False, default=myTime.getData())

    def __init__(self, car_id, charge_amount, pile_id):
        self.car_id = car_id
        self.charge_amount = charge_amount
        self.pile_id = pile_id
        m = hashlib.md5()
        m.update((car_id + str(pile_id) + myTime.getDataTime().isoformat()).encode(encoding="utf-8"))
        self.bill_id = m.hexdigest()


class OrderManager:
    def __init__(self):
        pass

    def findBillAll(self, car_id, date):
        num = 0
        if date == " " or date == None or date == "null" or date == "":
            num = db.session.query(Order).filter_by(car_id=car_id).count()
        else:
            num = db.session.query(Order).filter_by(car_id=car_id, bill_date=date).count()

        if num == 0:
            return [0]
        info = 0
        if date == " " or date == None or date == "null" or date == "":
            info = db.session.query(Order.car_id, Order.bill_date, Order.bill_id, Order.pile_id, Order.start_time,
                                    Order.end_time, Order.total_fee, Order.pay_state).filter_by(car_id=car_id).all()
        else:
            info = db.session.query(Order.car_id, Order.bill_date, Order.bill_id, Order.pile_id, Order.start_time,
                                Order.end_time, Order.total_fee, Order.pay_state).filter_by(car_id=car_id,
                                                                                            bill_date=date).all()
        list = []
        for i in info:
            dic = {}
            dic["car_id"] = i[0]
            dic["bill_date"] = i[1]
            dic["bill_id"] = i[2]
            dic["pile_id"] = i[3]
            dic["start_time"] = i[4]
            dic["end_time"] = i[5]
            dic["total_fee"] = i[6]
            dic["pay_state"] = i[7]
            list.append(dic)
        return [1, list]

    def creatOrder(self, car_id, charge_amount, pile_id):
        db.session.add(Order(car_id, charge_amount, pile_id))
        db.session.commit()

    def findBillOnly(self, bill_id):
        i = db.session.query(Order.car_id, Order.bill_date, Order.bill_id, Order.pile_id, Order.start_time,
                             Order.end_time, Order.total_fee, Order.pay_state, Order.charge_amount,
                             Order.charge_duration, Order.total_charge_fee, Order.total_service_fee).filter_by(
            bill_id=bill_id).first()
        return [1, i]

    def payBill(self, bill_id):
        state = db.session.query(Order.pay_state, Order.car_id).filter_by(bill_id=bill_id).first()
        if pileManager.if_car_in_charging(state[1]):
            return False
        if state[0] == 0:
            Order.query.filter_by(bill_id=bill_id).update({"pay_state": 1})
            db.session.commit()
            return True
        return False

    def if_no_pay(self, car_id):
        state = db.session.query(Order.pay_state).filter_by(car_id=car_id).all()
        for i in state:
            if i[0] == 0:
                return True
        return False


class UserManager:
    def __init__(self):
        self.token = 1
        self.tokenList = {}

    def login(self, name, password):
        m = hashlib.md5()
        m.update(password.encode(encoding="utf-8"))
        userCheckCount = db.session.query(User).filter_by(user_name=name, password=m.hexdigest()).count()
        if userCheckCount > 0:

            info = db.session.query(User.id, User.user_name, User.car_id, User.car_capacity).filter_by(
                user_name=name).first()
            token = self.addToken(info)
            return [1, token, info]
        else:
            return [0]

    def register(self, name, password, car_id, cap):
        userCheckCount1 = db.session.query(User).filter_by(user_name=name).count()  # 在数据库内找是否已经注册
        userCheckCount2 = db.session.query(User).filter_by(car_id=car_id).count()

        if userCheckCount1 == 0 and userCheckCount2 == 0:
            m = hashlib.md5()
            m.update(password.encode(encoding="utf-8"))
            db.session.add(User(name, m.hexdigest(), car_id, cap))
            db.session.commit()
            info = db.session.query(User.id, User.user_name, User.car_id, User.car_capacity).filter_by(
                user_name=name).first()

            token = self.addToken(info)
            user_id = info[0]
            return [0, user_id, token]
        return [1]

    def addToken(self, info):
        self.token += 1
        m = hashlib.md5()
        m.update((str(self.token) + info[1] + myTime.getDataTime().isoformat()).encode(encoding="utf-8"))
        md5Token = m.hexdigest()  # 用户id 用户名 用户车id 车总电量 充电量 充电模式 是否在充电
        self.tokenList[md5Token] = [info[0], info[1], info[2], info[3], 0, 0]
        return md5Token

    def checkToken(self, token):
        ret = self.tokenList.get(token)
        if ret is None:
            return False
        return True

    def requestC(self, token, amount, mode):
        info = self.tokenList.get(token)
        ret = pileManager.submit_a_charging_request(info[2], amount, mode)
        if ret[0] == 0:
            return [0]
        info[4] = amount
        info[5] = mode
        return ret

    def checkIfUpMax(self, token, amount):
        info = self.tokenList.get(token)
        amount = float(amount)
        if amount > info[3]:
            return False
        return True

    def removeToken(self, token):
        self.tokenList.pop(token)

    def modifyCar(self, token, car_id, car_cap):
        userInfo = self.tokenList.get(token)
        if pileManager.if_car_in_charging(car_id):
            return False
        count = db.session.query(User).filter_by(car_id=car_id).count()  # 在数据库内找是否已经注册

        if count == 0:
            return False
        print("FOUR:", car_id, car_cap)
        a = car_cap
        db.session.query(User).filter_by(car_id=car_id).first().car_capacity = a
        db.session.commit()
        userInfo[3] = car_cap

        return True

    def findAllCarState(self):
        list = []
        info1 = db.session.query(User.id, User.user_name, User.car_id, User.car_capacity).all()
        for value in info1:
            print(value[2])
            print(pileManager.if_car_in_charging(value[2]))
            print(pileManager.car_in_wait(value[2]))
            if (not pileManager.if_car_in_charging(value[2])) and (not pileManager.car_in_wait(value[2])):
                continue
            info = pileManager.look_query(value[2])
            dict = {}
            dict["user_id"] = str(value[0])
            dict["car_capacity"] = value[3]
            dict["request_amount"] = info["request_amount"]
            dict["pile_id"] = info["pile_id"]
            end_time = myTime.getDataTime()
            ini_time = time_table[value[2]]
            dict["wait_time"] = (end_time - ini_time).total_seconds()
            dict["car_state"] = info["car_state"]
            dict["request_mode"] = info["request_mode"]
            list.append(dict)
        return list

    def modifyMode(self, token, car_id, mode):
        userInfo = self.tokenList.get(token)
        userInfo[5] = mode
        return pileManager.modify_the_charging_mode(car_id, mode)

    def modifyAmount(self, token, car_id, amount):
        userInfo = self.tokenList.get(token)
        userInfo[4] = amount
        return pileManager.modify_the_amount_of_charge(car_id, amount)

    def lookState(self, car_id):
        print("@asdasfasfasfd")
        if not pileManager.if_car_in_charging(car_id):
            return [0]

        info = db.session.query(Order.car_id, Order.bill_date, Order.bill_id, Order.start_time,
                                Order.charge_amount).filter_by(bill_id=findBillId(car_id)).first()
        info2 = pileManager.view_billing(car_id)
        data = {
            "car_id": car_id,
            "bill_date": info[1],
            "bill_id": findBillId(car_id),
            "pile_id": info2["pip_id"],
            "charge_amount": info[4],
            "charge_duration": info2["time"],
            "start_time": info[3],
            "end_time": None,
            "total_charge_fee": info2["electric"],
            "total_service_fee": info2["service"],
            "total_fee": info2["total_cost"]

        }
        return [1, data]


pileManager = pile_manager()
userManager = UserManager()
orderManager = OrderManager()


@app.route('/', methods=["OPTIONS"])
def test():
    userManager.register("123", "123", "ad111", 1000)
    token = userManager.login("123", "123")[1]
    print(userManager.checkToken(token))
    db.session.add(Order("ADX100", 23, 1))
    db.session.commit()
    print(orderManager.findBillAll("ADX100", myTime.getData()))
    print(db.session.query(User).filter_by(user_name="1").all())
    print(db.session.query(Order.pay_state).filter_by(car_id="ADX100").first())
    Order.query.filter_by(car_id="ADX100").update({"pay_state": 1})
    db.session.commit()
    print(db.session.query(Order.pay_state).filter_by(car_id="ADX100").first())
    pass
    # 此处可以展示网页
    # return render_template('index1.html')
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_preflight(path):
    response = jsonify()
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'PUT, POST, GET, DELETE, OPTIONS'
    response.headers['Access-Control-Expose-Headers'] = '*'
    return response

# 此方法处理用户注册
@app.route('/user/register', methods=['POST'])
def register():
    usernamePost = request.form['user_name']
    passwordPost = request.form['password']
    car_id = request.form['car_id']
    car_cap = request.form["car_capacity"]
    userCheckCount = userManager.register(usernamePost, passwordPost, car_id, car_cap)

    if userCheckCount[0] <= 0:
        return jsonify({
            "code": 1,
            "message": "success",
            "data": {
                "user_id": userCheckCount[1],
                "user_name": usernamePost,
                "token": userCheckCount[2],
                "car_id": car_id,
                "car_capacity": car_cap,
            }
        })
    else:
        return jsonify({
            "code": 0,
            "message": "用户名与密码不匹配",
        })


@app.route("/user/getTotalBill", methods=["POST"])
def getTotalBill():
    car_id = request.form["car_id"]
    bill_data = request.form["bill_date"]
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "useless token."
        })
    if bill_data == "null" or bill_data == None or bill_data == "":
        pass
    else:
        bill_data = _datetime.datetime.strptime(bill_data, '%Y-%m-%d')
        print(bill_data)
        bill_data = bill_data.date()
    info = orderManager.findBillAll(car_id, bill_data)
    if info[0] == 0:
        return jsonify({
            "code": 0,
            "message": "there is no bill.",
        })
    return jsonify({
        "code": 1,
        "message": "success.",
        "data": {
            "bill_list": info[1]
        }
    })


@app.route("/user/getDetailBill", methods=["POST"])
# 乌鱼子 为什么要有这个函数，合并到上一个不行吗
def getOnlyBill():
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "useless token."
        })
    bill_id = request.form["bill_id"]
    i = orderManager.findBillOnly(bill_id)
    if i[0] == 0:
        return jsonify({
            "code": 0,
            "message": "useless billid."
        })
    i = i[1]
    return jsonify({
        "code": 1,
        "message": "success.",
        "data": {
            "car_id": i[0],
            "bill_date": i[1],
            "bill_id": i[2],
            "pile_id": i[3],
            "start_time": i[4],
            "end_time": i[5],
            "total_fee": i[6],
            "pay_state": i[7],
            "charge_amount": i[8],
            "charge_duration": i[9],
            "total_charge_fee": i[10],
            "total_service_fee": i[11],
        }
    })


# 此方法处理用户登录
@app.route('/user/login', methods=['POST'])
def log():
    usernamePost = request.form['user_name']
    passwordPost = request.form['password']
    userCheckCount = userManager.login(usernamePost, passwordPost)
    if userCheckCount[0] > 0:
        return jsonify({
            "code": 1,
            "message": "success",
            "data": {
                "user_id": userCheckCount[2][0],
                "user_name": userCheckCount[2][1],
                "token": userCheckCount[1],
                "car_id": userCheckCount[2][2],
                "car_capacity": userCheckCount[2][3],
            }
        })
    else:
        return jsonify({
            "code": 0,
            "message": "failed",
        })


@app.route("/user/logout", methods=["POST"])
def logout():
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    userManager.removeToken(token)
    return jsonify({
        "code": 1,
        "message": "注销成功."
    })


@app.route("/user/getPayBill", methods=["POST"])
def pay():
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    bill_id = request.form["bill_id"]

    if orderManager.payBill(bill_id):
        return jsonify({
            "code": 1,
            "message": "支付成功."
        })
    else:
        return jsonify({
            "code": 0,
            "message": "重复支付或者正在充电中或者订单不存在."
        })


@app.route("/user/changeCapacity", methods=["POST"])
def changeCapacity():
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    car_id = request.form["car_id"]
    car_cap = request.form["car_capacity"]
    car_cap = float(car_cap)
    if userManager.modifyCar(token, car_id, car_cap):
        return jsonify({
            "code": 1,
            "message": "success.",
            "data": {
                "car_capacity": car_cap
            }
        })
    else:
        return jsonify({
            "code": 0,
            "message": "正在充电或者不存在该车辆."
        })


@app.route("/user/chargingRequest", methods=['POST'])
def requestCharge():
    token = request.headers.get("Authorization")

    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    amount = request.form["request_amount"]
    amount = float(amount)
    mode = request.form["request_mode"]
    if not userManager.checkIfUpMax(token, amount):
        return jsonify({
            "code": 0,
            "message": "请求电量超过车辆总电量."
        })

    info = userManager.requestC(token, amount, mode)
    if info[0] == 0:
        return jsonify({
            "code": 0,
            "message": "等待区已满."
        })

    return jsonify({
        "code": 1,
        "message": "success.",
        "data": {
            "car_position": info[1],
            "car_state": "等待区",
            "queue_num": str(info[1]),
            "request_time": myTime.getDataTime()
        }
    })

@app.route("/user/getChargingState", methods=["POST"])
def lookCharge():
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    car_id = request.form["car_id"]
    info = userManager.lookState(car_id)
    if info[0] == 0:
        return jsonify({
            "code": 0,
            "message": "failed.",
        })
    return jsonify({
        "code": 1,
        "message": "success.",
        "data": info[1]
    })

@app.route("/user/changeChargingAmount", methods=['POST'])
def changeAmount():
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    amount = request.form["request_amount"]
    car_id = request.form["car_id"]
    amount = float(amount)
    if userManager.modifyAmount(car_id, amount):
        return jsonify({
            "code": 1,
            "message": "success."
        })
    return jsonify({
        "code": 0,
        "message": "failed."
    })


@app.route("/user/changeChargingMode", methods=['POST'])
def changeMode():
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    mode = request.form["request_mode"]
    car_id = request.form["car_id"]
    if userManager.modifyMode(car_id, mode):
        return jsonify({
            "code": 1,
            "message": "success."
        })
    return jsonify({
        "code": 0,
        "message": "failed."
    })


@app.route("/user/getChargingState", methods=["POST"])
def getState():
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    car_id = request.form["car_id"]
    info = userManager.lookState(car_id)
    if info[0] == 0:
        return jsonify({
            "code": 0,
            "message": "充电已结束."
        })
    print(info[1])
    return jsonify({
        "code": 1,
        "message": "success.",
        "data": info[1],
    })

@app.route("/user/endCharging", methods=["POST"])
def endCharge():
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    car_id = request.form["car_id"]
    pileManager.end_charge(car_id)
    return jsonify({
        "code": 1,
        "message": "取消成功或者根本没在充电，你猜？"
    })

@app.route("/user/queryCarState", methods=["POST"])
def lookQuery():
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    car_id = request.form["car_id"]
    if (not pileManager.if_car_in_charging(car_id)) and (not pileManager.car_in_wait(car_id)):
        if orderManager.if_no_pay(car_id):
            return jsonify({
                "code": 1,
                "message": "充电结束",
                "data": {
                    "car_position": None,
                    "car_state": "充电结束",
                    "queue_num": None,
                    "request_time": None,
                    "pile_id": None,
                    "request_mode": None,
                    "request_amount": None
                }
            })

    if (not pileManager.if_car_in_charging(car_id)) and (not pileManager.car_in_wait(car_id)):
        return jsonify({
            "code": 1,
            "message": "空闲",
            "data": {
                "car_position": None,
                "car_state": "空闲",
                "queue_num": None,
                "request_time": None,
                "pile_id": None,
                "request_mode": None,
                "request_amount": None
            }
        })
    return jsonify({
        "code": 1,
        "message": "success.",
        "data": pileManager.look_query(car_id)
    })

@app.route("/user/beginCharging", methods=["POST"])
def beginCharge():
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    car_id = request.form["car_id"]
    if pileManager.start_charge(car_id):
        return jsonify({
            "code": 1,
            "message": "正在充电."
        })
    else:
        return jsonify({
            "code": 0,
            "message": "无法."
        })
@app.route("/admin/login", methods=["POST"])
def adminLog():
    password = request.form["password"]
    info = userManager.login("admin", password)
    if info[0] > 0:
        return jsonify({
            "code": 1,
            "message": "admin login.",
            "data": {
                "token": info[1]
            }
        })
    return jsonify({
        "code": 0,
        "message": "密码错误."
    })


@app.route("/admin/logout", methods=["POST"])
def adminLogout():
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    userManager.removeToken(token)
    return jsonify({
        "code": 1,
        "message": "注销成功."
    })


@app.route("/admin/powerOn", methods=["POST"])
def powerOn():
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    id = request.form["pile_id"]
    id = int(id)
    pileManager.open_pile(id)
    return jsonify({
        "code": 1,
        "message": "success."
    })


@app.route("/admin/powerOff", methods=["POST"])
def powerOff():
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    id = request.form["pile_id"]
    id = int(id)
    pileManager.close_pile(id)
    return jsonify({
        "code": 1,
        "message": "success."
    })


@app.route("/admin/queryPileAmount", methods=["POST"])
def lookPileAmount():
    token = request.headers.get("Authorization")
    amount = pileManager.retPipeAmount()
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    dictl = [[], []]
    for i in range(1, 3):
        for j in amount[i]:
            dictl[i - 1].append({"pile_id": j})
    return jsonify({
        "code": 1,
        "message": "success.",
        "data": {
            "amount": amount[0],
            "fast_pile_id": dictl[1],
            "slow_pile_id": dictl[0]
        }
    })


@app.route("/admin/setPrice", methods=["POST"])
def setPrice():
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    low = request.form["low_price"]
    mid = request.form["mid_price"]
    high = request.form["high_price"]
    low = int(low)
    mid = int(mid)
    high = int(high)
    pileManager.setPrice(low, mid, high)
    return jsonify({
        "code": 1,
        "message": "success."
    })

@app.route("/admin/powerCrash", methods=["POST"])
def setCrash():
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    pile_id = request.form["pile_id"]
    pile_id = int(pile_id)
    pileManager.set_pile_error(pile_id)
    return jsonify({
        "code": 1,
        "message": "已故障."
    })

@app.route("/admin/queryQueueState", methods=["POST"])
def lookQueueC():
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    info = userManager.findAllCarState()
    print(info)
    return jsonify({
        "code": 1,
        "message": "success.",
        "data": {
            "state_list": info
        }
    })

@app.route("/admin/queryPileState", methods=["POST"])
def lookQueryPile():
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    pile_id = request.form["pile_id"]
    pile_id = int(pile_id)
    info = pileManager.check_pile_report()[pile_id]
    return jsonify({
        "code": 1,
        "message": "success.",
        "data": {
            "workingState": info["working_state"],
            "totalChargeNum": info["total_charge_num"],
            "totalChargeTime": info["total_charge_time"],
            "totalCapacity": info["total_capacity"],
            "charge_mode": info["charge_mode"]
        }
    })

@app.route("/admin/queryReport", methods=["POST"])
def look_report():
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "用户未登录."
        })
    pile_id = request.form["pile_id"]
    pile_id = int(pile_id)
    start = request.form["start_date"]
    end = request.form["end_date"]

@app.route("/getTime", methods=["POST"])
def geTime():
    return jsonify({
        "code": 1,
        "data": {
            "time": myTime.getDataTime()
        }
    })


with app.app_context():
    db.create_all()
    m = hashlib.md5()
    count = db.session.query(User).filter_by(user_name="admin").count()
    if count == 0:
        m.update("zxc123456".encode(encoding="utf-8"))
        db.session.add(User("admin", m.hexdigest(), None, None))
        db.session.commit()
    pileManager.start()




if __name__ == '__main__':
    cors = CORS(app, resources=r"/*")

    app.run(host='0.0.0.0', port=8888)
