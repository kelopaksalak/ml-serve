from app.models.user import User
from app.database import db
from flask_jwt_extended import create_access_token

class AuthService:
    def register(self, data):
        if User.query.filter_by(username= data['username']).first():
            return None, 'usrname already exist'
        user = User(username=data['username'])
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        return user, None

    def login(self, data):
        user = User.query.filter_by(username=data['username']).first()
        if not user or not user.check_password(data['password']):
            return None, 'Invalid credentials'
        token = create_access_token(identity=str(user.id))
        return {'token': token}, None

    def get_user(self, user_id):
        return User.query.get(user_id)