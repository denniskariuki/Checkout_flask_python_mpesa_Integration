# Checkout_flask_python_mpesa_Integration

📲 Flask M-Pesa STK Push Payment Integration
Overview
This project demonstrates how to integrate M-Pesa STK Push payments into a Flask web application.
Users can input their name and phone number, then click Pay Now, triggering an M-Pesa prompt on their mobile device to complete the payment.

Features
Securely trigger M-Pesa STK Push from a Flask backend

Clean, responsive checkout form

Real-time feedback: loading, success, or error messages

Works with both M-Pesa Sandbox and Live environments

Technologies Used
🐍 Flask (Python web framework)

🌐 HTML/CSS/JavaScript (Frontend)

🔐 Safaricom M-Pesa Daraja API (STK Push)

⚡ Fetch API (for frontend-backend communication)

Project Structure
bash
Copy
Edit
.
├── app.py          # Flask server handling payment
├── templates/
│   └── index.html  # Payment form (frontend)
├── static/
│   └── styles.css  # CSS styling (optional)
├── requirements.txt  # Python dependencies
├── README.md       # Project documentation


Setup Instructions
1. Clone the Repository
bash
Copy
Edit
git clone https://github.com/your-username/mpesa-flask-integration.git
cd mpesa-flask-integration
2. Create and Activate Virtual Environment (Recommended)
bash
Copy
Edit
python -m venv venv
source venv/bin/activate   # On Mac/Linux
venv\Scripts\activate      # On Windows
3. Install Dependencies
bash
Copy
Edit
pip install -r requirements.txt
4. Set Up Environment Variables
Create a .env file in the root directory and add the following:

env
Copy
Edit
CONSUMER_KEY=your_safaricom_consumer_key

CONSUMER_SECRET=your_safaricom_consumer_secret

BUSINESS_SHORTCODE=your_business_shortcode

PASSKEY=your_safaricom_passkey

CALLBACK_URL=https://yourdomain.com/callback

ENVIRONMENT=sandbox  # or 'production'
⚡ Tip: Never expose your credentials publicly!

5. Run the Flask App
bash
Copy
Edit
python app.py
Access it at: http://localhost:5000

Setting Up M-Pesa Daraja API
Go to Safaricom Developer Portal.

Create an account and login.

Create a new app under "My Apps" to get:

Consumer Key

Consumer Secret

Get your Business Shortcode and Passkey.

Configure your Callback URL (can use ngrok during testing).

Example Flow
User enters name and phone number.

Clicks "Pay Now."

Flask server requests an OAuth token.

Server sends an STK Push request to Safaricom.

M-Pesa prompts the user on their mobile phone.

User confirms payment.

Server handles success or failure responses.


License
This project is licensed under the MIT License.

Author
Tom
Your friendly ICT Developer 🚀


🔥 Happy Coding!
Notes:

If you’re in the sandbox, only test numbers like 254708374149 will work.

If going live, you must use TLS/SSL HTTPS for callback URLs.
