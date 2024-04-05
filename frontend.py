import streamlit as st
import requests
import pandas as pd

# Replace with your actual API endpoint URLs
TRANSACTION_API_URL = "http://192.168.1.7:3000/transactions"
NAME_API_URL = "http://192.168.1.7:3000/get_user_name"
BALANCE_API_URL = "http://192.168.1.7:3000/get_balance"
LOGIN_API_URL = "http://192.168.1.7:3000/login"
TOP_UP_URL = "http://192.168.1.7:3000/update_balance"


def get_transactions(user_id):
    """Fetches transaction history for a user from the API"""
    response = requests.get(TRANSACTION_API_URL, params={"user_id": user_id})
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching transactions: {response.status_code}")
        return None


def get_user_name(user_id):
    """Fetches user name for a user from the API"""
    response = requests.get(f"{NAME_API_URL}/{user_id}")
    if response.status_code == 200:
        return response.json()["name"]
    else:
        st.error(f"Error fetching user name: {response.status_code}")
        return None


def get_balance(user_id):
    """Fetches user balance for a user from the API"""
    response = requests.get(BALANCE_API_URL + "/" + str(user_id))
    if response.status_code == 200:
        return response.json()["balance"]
    else:
        st.error(f"Error fetching user balance: {response.status_code}")
        return None


def login(user_id, pin):
    """Attempts to log in with the given user ID and PIN"""
    response = requests.post(LOGIN_API_URL, params={"id": user_id, "pin": pin}, json={})
    if response.status_code == 200:
        return True
    else:
        st.error(f"Login failed: {response.text}")
        return False


def top_up(user_id, amount):
    """Attempts to top up the given user's balance"""
    response = requests.post(
        TOP_UP_URL, params={"user_id": user_id, "type": 1, "amount": amount}, json={}
    )
    if response.status_code == 200:
        st.success(f"Top-up successful: Rp.{amount} added to user ID {user_id}")
    else:
        st.error(f"Top-up failed: {response.text}")


st.set_page_config(page_title="Transaction History Dashboard", layout="wide")

# Initial feature selection
selected_feature = st.selectbox("Select feature:", ["Transaction History", "Top Up"])

if selected_feature == "Transaction History":
    # Login form
    user_id = st.text_input("User ID")
    pin = st.text_input("PIN", type="password")

    if st.button("Get Transactions"):
        if login(user_id, pin):
            # Successful login, display transaction history features
            with st.spinner("Fetching transactions..."):
                transactions = get_transactions(user_id)

            if transactions:
                name = get_user_name(user_id)
                balance = get_balance(user_id)

                st.subheader(f"Transaction History - {name}")
                st.subheader(f"Current Balance: Rp.{balance}")

                df = pd.DataFrame(transactions)
                df["real_amount"] = df["amount"] * (
                    df["type"].apply(lambda x: -1 if x == "WITHDRAW" else 1)
                )

                st.dataframe(df[["timestamp", "type", "amount"]])
                st.line_chart(df, x="timestamp", y="real_amount")
            else:
                st.warning("No transactions found for this user ID.")

elif selected_feature == "Top Up":
    # Top-up form
    user_id = st.text_input("User ID")
    pin = st.text_input("PIN", type="password")
    amount = st.number_input("Amount to top up")

    if st.button("Top Up"):
        if login(user_id, pin):
            if amount > 0:
                top_up(user_id, int(amount))
            else:
                st.error("Top Up Amount must be greater than 0")
