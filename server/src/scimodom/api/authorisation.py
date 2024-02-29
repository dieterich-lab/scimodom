# from pathlib import Path

from flask import request

# from flask_cors import cross_origin
# from flask_jwt_extended import create_access_token, create_refresh_token, set_access_cookies, set_refresh_cookies
# from flask_jwt_extended import unset_jwt_cookies, jwt_required

from . import api


@api.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data["username"]
    password = data["password"]
    print(f"USERNAME {username}, PASSWORD {password}")
    # user = authenticate(username, password) # SEE BELOW
    # user = User.authenticate(**data) # SEE BELOW
    # if user:
    #   access_token = create_access_token(identity=user.user_id)
    #   refresh_token = create_refresh_token(identity=user.user_id)
    #   response = jsonify()
    #   set_access_cookies(response, access_token)
    #   set_refresh_cookies(response, refresh_token)
    #   return response, 201
    # else:
    #   return jsonify(message="Unauthorized"), 401


@api.route("/logout", methods=["POST"])
# @jwt_required
def logout():
    pass
    # response = jsonify()
    # unset_jwt_cookies(response)
    # return response, 200


# A user model could look like
# class User():
#     __tablename__ = 'user'

#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String(120), unique=True, nullable=False)
#     password = db.Column(db.String(255), nullable=False)

#     def __init__(self, email, password):
#         self.email = email
#         self.password = some function to generate password hash e.g. sha256

#     @classmethod
#     def authenticate(cls, **kwargs):
#         email = kwargs.get('email')
#         password = kwargs.get('password')

#         if not email or not password:
#             return None

#         user = cls.query.filter_by(email=email).first()
#         if not user or not some function toch check password hash(user.password, password):
#             return None

#         return user
