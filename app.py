# -*-coding:utf-8-*-
import os
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db1.sqlite3'



db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(50))
    def __init__(self,username,password):
        self.name = username;
        self.password = password;
    def __repr__(self):
        return '<User %s>' %self.username

#db.create_all()
with app.app_context():
    db.create_all()
username="test"

@app.route('/')
def test():
    pass
    #此处可以展示网页
    #return render_template('index1.html')

# 此方法处理用户注册
@app.route('/user/register', methods=['POST'])
def register():
    usernamePost = request.form['user_name']
    passwordPost = request.form['password']
    userCheckCount = User.query.filter_by(name=usernamePost).count()   #在数据库内找是否已经注册
    if(userCheckCount<=0):
        print(userCheckCount)
        user=User(usernamePost,passwordPost)
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
@app.route('/user/log',methods = ['POST'])
def log():
    usernamePost = request.form['username']
    passwordPost = request.form['password']
    userCheckCount = User.query.filter_by(name=usernamePost,password = passwordPost).count()
    # userCheckCount = db.session.query(User).get({'username': usernamePost}).count()
    if (userCheckCount <= 0):
        return jsonify({
            "code": 1,
            "message": "success",
            "data": {
                "user_id": 1,
                "user_name": "John Doe",
                "token": "12345"}
        })
    else:
        return jsonify({
            "code": 0,
            "message": "用户名与密码不匹配",
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
