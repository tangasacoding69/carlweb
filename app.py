from flask import Flask, request, render_template, redirect, url_for, session
import mysql.connector
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="ereklamo"
    )

@app.route('/')
def home():
    return "<h2>Welcome to Ereklamo API</h2><p>Use <a href='/login'>/login</a> or <a href='/register'>/register</a>.</p>"

# --- REGISTER PAGE (GET) ---
@app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

# --- REGISTER API (POST) ---
@app.route('/register', methods=['POST'])
def register_user():
    name = request.form.get('name', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not name or not username or not password:
        return "incomplete"

    conn = get_db_connection()
    try:
        with conn.cursor(dictionary=True) as cursor:
            # Check if username already exists
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            existing_user = cursor.fetchone()

            if existing_user:
                return "exists"

            # Insert new user
            cursor.execute("INSERT INTO users (name, username, password) VALUES (%s, %s, %s)",
                           (name, username, password))
            conn.commit()
            return "success"
    except Exception as e:
        print("Registration Error:", e)
        return "error"
    finally:
        conn.close()

# --- LOGIN PAGE ---
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

# --- LOGIN API ---
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    conn = get_db_connection()
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user and user['password'] == password:
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error="Invalid credentials")
    finally:
        conn.close()

# --- DASHBOARD ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('dashboard.html')

# --- VIEW NEWS ---
@app.route('/news')
def news():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM news_posts ORDER BY created_at DESC")
            news_posts = cursor.fetchall()
            return render_template('news.html', news=news_posts)
    finally:
        conn.close()

# --- SUBMIT COMPLAINT FORM ---
@app.route('/submit-complaint', methods=['GET'])
def submit_complaint_form():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('submit_complaint.html')

# --- SUBMIT COMPLAINT ACTION ---
@app.route('/submit-complaint', methods=['POST'])
def submit_complaint():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    complaint_text = request.form.get('complaint')

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO complaints (UserID, ComplaintText, Status, DateSubmitted) VALUES (%s, %s, 'Pending', NOW())",
                (user_id, complaint_text))
            conn.commit()
        return redirect('/my-complaints')
    finally:
        conn.close()

# --- MY COMPLAINTS PAGE ---
@app.route('/my-complaints')
def my_complaints():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT DateSubmitted, ComplaintText, Status FROM complaints WHERE UserID = %s ORDER BY DateSubmitted DESC",
                (user_id,))
            complaints = cursor.fetchall()
            return render_template('my_complaints.html', complaints=complaints)
    finally:
        conn.close()

# --- VIEW ALL COMPLAINTS (ADMIN/STAFF) ---
@app.route('/all-complaints')
def all_complaints():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT c.ComplaintText, c.DateSubmitted, c.Status, u.name AS SubmittedBy
                FROM complaints c
                JOIN users u ON c.UserID = u.id
                ORDER BY c.DateSubmitted DESC
            """)
            complaints = cursor.fetchall()
            return render_template('all_complaints.html', complaints=complaints)
    finally:
        conn.close()

# --- LOGOUT ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
