# -*-coding:utf-8-*-
import os

import hashlib
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import _datetime

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user'

db = SQLAlchemy(app)

class 充电桩():
    def __init__(self):
        self.id=1
a=充电桩()
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
    start_time = db.Column(db.DateTime, nullable=False, default=_datetime.datetime.now())
    end_time = db.Column(db.DateTime, default=None)
    bill_date = db.Column(db.Date, nullable=False, default=_datetime.date.today())

    def __init__(self, car_id, charge_amount, pile_id, charge_duration):
        self.car_id = car_id
        self.charge_amount = charge_amount
        self.pile_id = pile_id
        m = hashlib.md5()
        m.update((car_id + str(pile_id) + _datetime.datetime.now().isoformat()).encode(encoding="utf-8"))
        self.bill_id = m.hexdigest()
        self.charge_duration = charge_duration

class OrderManager:
    def __init__(self):
        pass

    def findBillAll(self, car_id, date):
        num = db.session.query(Order).filter_by(car_id=car_id, bill_date=date).count()
        if num == 0:
            return [0]
        info = db.session.query(Order.car_id, Order.bill_date, Order.bill_id, Order.pile_id, Order.start_time, Order.end_time, Order.total_fee, Order.pay_state).filter_by(car_id=car_id, bill_date=date).all()
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

    def findBillOnly(self, bill_id):
        i = db.session.query(Order.car_id, Order.bill_date, Order.bill_id, Order.pile_id, Order.start_time, Order.end_time, Order.total_fee, Order.pay_state, Order.charge_amount, Order.charge_duration, Order.total_charge_fee, Order.total_service_fee).filter_by(bill_id=bill_id).first()
        if len(i) == 0:
            return [0]
        return [1, i]



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
        userCheckCount = db.session.query(User).filter_by(user_name=name, car_id=car_id).count()  # 在数据库内找是否已经注册
        if userCheckCount <= 0:
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
        m.update((str(self.token) + info[1] + _datetime.datetime.now().isoformat()).encode(encoding="utf-8"))
        md5Token = m.hexdigest()
        self.tokenList[md5Token] = [info]
        return md5Token

    def checkToken(self, token):
        ret = self.tokenList.get(token)
        if ret is None:
            return False
        return True

    def removeToken(self, token):
        self.tokenList.pop(token)


userManager = UserManager()
orderManager = OrderManager()

@app.route('/')
def test():
    m = hashlib.md5()
    m.update("123".encode(encoding="utf-8"))

    db.session.add(Order("ADX100", 23, 1, 23.2))
    db.session.commit()
    print(orderManager.findBillAll("ADX100", _datetime.date.today()))
    print(db.session.query(User).filter_by(user_name="1").all())
    pass
    # 此处可以展示网页
    # return render_template('index1.html')


# 此方法处理用户注册
@app.route('/user/register', methods=['POST'])
def register():
    usernamePost = request.form['user_name']
    passwordPost = request.form['password']
    car_id = request.form['car_id']
    car_cap = request.form["car_capacity"]
    userCheckCount = userManager.register(usernamePost, passwordPost, car_id, car_cap)

    if userCheckCount[0] <= 0:
        print(userCheckCount)
        user = User(usernamePost, passwordPost)
        db.session.add(user)
        db.session.commit()
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
    bill_data = request.form["bill_data"]
    token = request.headers.get("Authorization")
    if not userManager.checkToken(token):
        return jsonify({
            "code": 0,
            "message": "useless token."
        })
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
        "code": 0,
        "message": "useless billid.",
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

with app.app_context():
    print(_datetime.datetime.now().isoformat())
    db.drop_all()
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
