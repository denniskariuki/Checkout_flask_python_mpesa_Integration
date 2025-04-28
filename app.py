from flask import Flask, render_template, request, jsonify, redirect, url_for
import mysql.connector
from flask_cors import CORS
import urllib3
import base64
urllib3.disable_warnings()
from dotenv import load_dotenv
import requests
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)
load_dotenv()
# Database Configuration (can also be in .env)
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_DATABASE', 'm_pesa_store')
}

# M-PESA API Credentials (now loaded from environment variables)
CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY')
CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET')
BUSINESS_SHORTCODE = os.environ.get('BUSINESS_SHORTCODE')
PASSKEY = os.environ.get('PASSKEY')
CALLBACK_URL_BASE = os.environ.get('YOUR_NGROK_HTTPS_URL')

# Product Details
PRODUCT_NAME = "Awesome Gadget"
PRODUCT_PRICE = 1

def get_db_connection():
    """Establishes and returns a MySQL database connection."""
    return mysql.connector.connect(**DB_CONFIG)

def close_db_connection(conn):
    """Closes a MySQL database connection."""
    if conn and conn.is_connected():
        conn.close()

def generate_access_token():
    """Generates an access token from the Safaricom Daraja API."""
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    headers = {'Content-Type': 'application/json'}
    auth = (CONSUMER_KEY, CONSUMER_SECRET)
    try:
        response = requests.get(api_url, headers=headers, auth=auth, verify=False)  # Disable SSL verification for sandbox
        response.raise_for_status()  # Raise an exception for bad status codes
        access_token = response.json().get('access_token') 
        return access_token                                 
    except requests.exceptions.RequestException as e:
        
        return None

def initiate_stk_push(access_token, phone_number, amount, callback_url):
    """Initiates an STK Push request to the M-PESA API."""

    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    # Load required values from environment
    shortcode = os.getenv("BUSINESS_SHORTCODE")
    passkey = os.getenv("PASSKEY")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode((shortcode + passkey + timestamp).encode()).decode('utf-8')
    


    payload = {
        "BusinessShortCode": BUSINESS_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": f"254{phone_number[-9:]}",  # e.g. 254712345678
        "PartyB": BUSINESS_SHORTCODE,
        "PhoneNumber": f"254{phone_number[-9:]}",  # Must match format
        "CallBackURL": "https://a153-2c0f-2d80-240-7f00-75d5-af97-2978-5507.ngrok-free.app/mpesa_callback",  # Use the dynamic callback URL
        "AccountReference": "ProductPayment",
        "TransactionDesc":"Payment"
    }

 
    try:
        response = requests.post(api_url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        
        return response.json()  # Return the successful response
    except requests.exceptions.HTTPError as err:
        
        if err.response is not None:
            print("📥 STK Push Raw Response:", err.response.text)
        return jsonify({'error': 'HTTPError occurred during STK push', 'details': err.response.text}), 400
    except requests.exceptions.RequestException as e:
        
        return jsonify({'error': 'Request failed', 'details': str(e)}), 400


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/pay', methods=['POST'])
def pay():
    try:
        name = request.form['name']
        phone_number = request.form['phone']
        amount = PRODUCT_PRICE

        print(f"📲 Initiating payment for {name} | Phone: {phone_number} | Amount: {amount}")

        access_token = generate_access_token()
        if not access_token:
            print("🔥 Failed to generate access token")
            return jsonify({'error': 'Failed to generate access token'}), 500

        callback_url = url_for('mpesa_callback', _external=True)
        stk_response = initiate_stk_push(access_token, phone_number, amount, callback_url)
        print(f"STK Response: {stk_response}")
        
        if 'error' in stk_response:
            print(f"🔥 STK Error: {stk_response}")
            return jsonify(stk_response), 400

        if stk_response.get('ResponseCode') == '0':
            merchant_request_id = stk_response.get('MerchantRequestID')
            checkout_request_id = stk_response.get('CheckoutRequestID')

            conn = get_db_connection()
            cursor = conn.cursor()
            query = "INSERT INTO transactions (name, phone_number, amount, merchant_request_id, checkout_request_id) VALUES (%s, %s, %s, %s, %s)"
            values = (name, phone_number, amount, merchant_request_id, checkout_request_id)
            cursor.execute(query, values)
            conn.commit()
            close_db_connection(conn)

            return jsonify({'message': stk_response.get('CustomerMessage', 'Payment initiated')})

        print("🔥 Unknown response from Safaricom:", stk_response)
        return jsonify({'error': 'Unknown response from Safaricom', 'response': stk_response}), 400

    except Exception as e:
        import traceback
        print("🔥 Exception occurred:", str(e))
        traceback.print_exc()
        return jsonify({'error': 'An error occurred', 'details': str(e)}), 500

@app.route('/mpesa_callback', methods=['POST'])
def mpesa_callback():
    """Handles the M-PESA STK Push callback."""
    callback_data = request.json
    print(f"M-PESA Callback Data: {callback_data}")

    if callback_data and callback_data.get('Body') and callback_data['Body'].get('stkCallback'):
        stk_callback = callback_data['Body']['stkCallback']
        merchant_request_id = stk_callback.get('MerchantRequestID')
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')

        receipt_number = None
        if stk_callback.get('CallbackMetadata') and stk_callback['CallbackMetadata'].get('Item'):
            for item in stk_callback['CallbackMetadata']['Item']:
                if item.get('Name') == 'MpesaReceiptNumber':
                    receipt_number = item.get('Value')
                    break

        conn = get_db_connection()
        cursor = conn.cursor()
        query = "UPDATE transactions SET receipt_number=%s, result_code=%s, result_desc=%s WHERE merchant_request_id=%s"
        values = (receipt_number, result_code, result_desc, merchant_request_id)
        cursor.execute(query, values)
        conn.commit()
        close_db_connection(conn)

        return jsonify({'ResultCode': 0, 'ResultDesc': 'Success'})
    else:
        return jsonify({'ResultCode': 1, 'ResultDesc': 'Failed'})

@app.route('/transactions', methods=['GET'])
def transactions():
    """Retrieves and displays all transaction records."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT name, phone_number, amount, receipt_number, result_code, transaction_date FROM transactions ORDER BY transaction_date DESC"
    cursor.execute(query)
    transaction_records = cursor.fetchall()
    close_db_connection(conn)
    return render_template('transactions.html', transactions=transaction_records)

if __name__ == '__main__':
    app.run(debug=True)