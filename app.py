from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from dotenv import dotenv_values

app = Flask(__name__)

# TODO: Set the DATABASE_URL environment variable, following structure of this table
# users (id, name, balance, pin)
# transactions (id, user_id, created_at, type, amount)
app.config["SQLALCHEMY_DATABASE_URI"] = dotenv_values(".env").get("DATABASE_URL")
db = SQLAlchemy(app)


@app.route("/")
def index():
    return "Hello World"


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    balance = db.Column(db.Float)
    pin = db.Column(db.Integer)


class Transactions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime)
    type = db.Column(db.Integer)
    amount = db.Column(db.Float)


# create login api that match id with its pin
@app.route("/login", methods=["POST", "GET"])
def login():
    user_id = int(request.args.get("id"))
    pin = int(request.args.get("pin"))

    user = Users.query.get(user_id)
    if user:
        if user.pin == pin:
            return jsonify({"message": "Login successful"})
        else:
            return jsonify({"error": "Invalid pin"}), 401
    else:
        return jsonify({"error": "User not found"}), 404


# create get user_list api
@app.route("/user_list", methods=["GET"])
def user_list():
    users = Users.query.all()
    user_list = []
    for user in users:
        user_list.append({"id": user.id, "name": user.name})
    return jsonify(user_list)


# create get transaction api for specified user_id
@app.route("/transactions", methods=["GET"])
def get_transactions():
    user_id = int(request.args.get("user_id"))
    transactions = Transactions.query.filter_by(user_id=user_id).all()
    transaction_list = []
    for transaction in transactions:
        transaction_list.append(
            {
                "id": transaction.id,
                "timestamp": transaction.created_at,
                "type": "TOP UP" if transaction.type == 1 else "WITHDRAW",
                "amount": transaction.amount,
            }
        )
    return jsonify(transaction_list)


# create get user name
@app.route("/get_user_name/<int:user_id>", methods=["GET"])
def get_user_name(user_id):
    user = Users.query.get(user_id)
    if user:
        return jsonify({"name": user.name})
    else:
        return jsonify({"error": "User not found"}), 404


@app.route("/update_balance", methods=["POST", "GET"])
def update_balance():
    # PARSE QUERY FROM URL FOLLOWING ?key1=value1&key2=value2 format
    user_id = int(request.args.get("user_id"))
    transaction_type = int(request.args.get("type"))
    amount = int(request.args.get("amount"))

    user = Users.query.get(user_id)

    if user:
        if transaction_type == 1:  # top-up
            user.balance += amount
            transaction = Transactions(
                user_id=user_id, created_at=datetime.now(), type=1, amount=amount
            )
            db.session.add(transaction)
            db.session.commit()
            return jsonify({"message": "Balance updated successfully"})
        elif transaction_type == -1:  # deduct
            if user.balance >= amount:
                user.balance -= amount
                transaction = Transactions(
                    user_id=user_id, created_at=datetime.now(), type=-1, amount=amount
                )
                db.session.add(transaction)
                db.session.commit()
                return jsonify({"message": "Balance updated successfully"})
            else:
                return jsonify({"error": "Insufficient balance"}), 401
        else:
            return jsonify({"error": "Invalid transaction type"}), 402
    else:
        return jsonify({"error": "User not found"}), 404


@app.route("/get_balance/<int:user_id>", methods=["GET"])
def get_balance(user_id):
    user = Users.query.get(user_id)
    if user:
        return jsonify({"balance": user.balance})
    else:
        return jsonify({"error": "User not found"}), 404


if __name__ == "__main__":
    # app run in port 80
    app.run(debug=True, port=5000)
