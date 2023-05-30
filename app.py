# -*-coding:utf-8-*-
import os

import hashlib
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user'

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_name = db.Column(db.String(20))
    password = db.Column(db.String(20))
    car_id = db.Column(db.String(20))
    car_capacity = db.Column(db.Float)

    def __init__(self, user_name, password, car_id, car_capacity):
        self.user_name = user_name
        self.password = password
        self.car_id = car_id
        self.car_capacity = car_capacity



class UserManager:
    def __init__(self):
        self.token = 1
        self.tokenList = {}

    def login(self, name, password):
        userCheckCount = User.query.filter_by(user_name=name, password=hashlib.md5(password).hexdigest()).count()
        # userCheckCount = db.session.query(User).get({'username': usernamePost}).count()
        token = 0
        if userCheckCount > 0:
            token = self.addToken(name)
        return [userCheckCount, token]

    def register(self, name, password, car_id, cap):
        userCheckCount = User.query.filter_by(name=name, car_id=car_id).count()  # 在数据库内找是否已经注册
        if userCheckCount <= 0:
            db.session.add(User(name, hashlib.md5(password).hexdigest(), car_id, cap))
            db.commit()
        return userCheckCount

    def addToken(self, name):
        self.token += 1
        md5Token = hashlib.md5(self.token).hexdigest()
        self.tokenList[name] = md5Token
        return md5Token


userManager = UserManager()



@app.route('/')
def test():
    db.session.add(User("1", "1", "1", 1))
    db.session.commit()
    pass
    # 此处可以展示网页
    # return render_template('index1.html')


# 此方法处理用户注册
@app.route('/user/register', methods=['POST'])
def register():
    usernamePost = request.form['user_name']
    passwordPost = request.form['password']
    userCheckCount = userManager.register(usernamePost, passwordPost)

    if userCheckCount <= 0:
        print(userCheckCount)
        user = User(usernamePost, passwordPost)
        db.session.add(user)
        db.session.commit()
        return jsonify({
            "code": 1,
            "message": "success",
            "data": {
                "user_id": 1,
                "user_name": "John Doe",
                "token": "12345"}
        })
    else:
        print('username:' + usernamePost)
        print('password:' + passwordPost)
        return jsonify({
            "code": 0,
            "message": "用户名与密码不匹配",
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
                "user_id": 1,
                "user_name": "John Doe",
                "token": userCheckCount[1],
                "car_id": 1,
                "car_capacity": 1,
            }
        })
    else:
        return jsonify({
            "code": 0,
            "message": "failed",
        })
































with app.app_context():
    db.create_all()

if __name__ == '__main__':


    app.run(host='0.0.0.0', port=80)
