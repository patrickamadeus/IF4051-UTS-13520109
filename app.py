from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

from dotenv import dotenv_values

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = dotenv_values('.env').get('DATABASE_URL')
db = SQLAlchemy(app)

@app.route('/')
def index():
    return 'Hello World'

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    balance = db.Column(db.Float)

class Transactions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    type = db.Column(db.Integer)
    amount = db.Column(db.Float)

@app.route('/update_balance', methods=['POST'])
def update_balance():
    data = request.get_json()
    user_id = data.get('user_id')
    transaction_type = data.get('type')
    amount = data.get('amount')

    user = Users.query.get(user_id)
    if user:
        if transaction_type == 1:  # top-up
            user.balance += amount
            transaction = Transactions(user_id=user_id, type=1, amount=amount)
            db.session.add(transaction)
            db.session.commit()
            return jsonify({'message': 'Balance updated successfully'})
        elif transaction_type == -1:  # deduct
            if user.balance >= amount:
                user.balance -= amount
                transaction = Transactions(user_id=user_id, type=-1, amount=amount)
                db.session.add(transaction)
                db.session.commit()
                return jsonify({'message': 'Balance updated successfully'})
            else:
                return jsonify({'error': 'Insufficient balance'}), 401
        else:
            return jsonify({'error': 'Invalid transaction type'}), 402
    else:
        return jsonify({'error': 'User not found'}), 404

@app.route('/get_balance/<int:user_id>', methods=['GET'])
def get_balance(user_id):
    user = Users.query.get(user_id)
    if user:
        return jsonify({'balance': user.balance})
    else:
        return jsonify({'error': 'User not found'}), 404


if __name__ == '__main__':
    # app run in port 80
    app.run(port=8080)
