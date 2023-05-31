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


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    user_name = db.Column(db.String(20))
    password = db.Column(db.String(20))
    car_id = db.Column(db.String(20))
    car_capacity = db.Column(db.Float)

    def __init__(self, user_name, password, car_id, car_capacity):
        self.user_name = user_name
        self.password = password
        self.car_id = car_id
        self.car_capacity = car_capacity


class Order(db.Model):
    __tablename__ = "order"
    bill_id = db.Column(db.Integer, autoincrement=True, primary_key=True, nullable=False)
    car_id = db.Column(db.String(20))
    pile_id = db.Column(db.Integer)
    charge_amount = db.Column(db.Float)
    charge_duration = db.Column(db.Float)
    total_charge_fee = db.Column(db.Float)
    total_service_fee = db.Column(db.Float)
    total_fee = db.Column(db.Float)
    pay_state = db.Column(db.Integer, default=0)
    start_time = db.Column(db.DateTime, nullable=False, default=_datetime.datetime.now())
    end_time = db.Column(db.DateTime)
    bill_data = db.Column(db.Date, nullable=False, default=_datetime.date.today())

    def __init__(self, car_id, charge_amount, pile_id):
        self.car_id = car_id
        self.charge_amount = charge_amount
        self.pile_id = pile_id


class OrderManager:
    def __init__(self):
        pass








class UserManager:
    def __init__(self):
        self.token = 1
        self.tokenList = {}

    def login(self, name, password):
        userCheckCount = User.query.filter_by(user_name=name, password=hashlib.md5(password).hexdigest()).count()
        if userCheckCount > 0:

            info = db.session.query(User.id, User.user_name, User.car_id, User.car_capacity).filter_by(
                user_name=name).first()
            token = self.addToken(info)
            return [1, token, info]
        else:
            return [0]

    def register(self, name, password, car_id, cap):
        userCheckCount = User.query.filter_by(user_name=name, car_id=car_id).count()  # 在数据库内找是否已经注册
        if userCheckCount <= 0:
            db.session.add(User(name, hashlib.md5(password).hexdigest(), car_id, cap))
            db.commit()
            info = db.session.query(User.id, User.user_name, User.car_id, User.car_capacity).filter_by(
                user_name=name).first()

            token = self.addToken(info)
            user_id = info[0]
            return [0, user_id, token]
        return [1]

    def addToken(self, info):
        self.token += 1
        md5Token = hashlib.md5(self.token).hexdigest()
        self.tokenList[md5Token] = [info]
        return md5Token


userManager = UserManager()


@app.route('/')
def test():
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






with app.app_context():
    db.drop_all()
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
