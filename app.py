from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'database.db'

# Hardcoded admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

# Initialize the database
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        with open('schema.sql') as f:
            conn.executescript(f.read())

# Helper function to query the database
def query_db(query, args=(), one=False):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute(query, args)
        rv = cur.fetchall()
        conn.commit()
        return (rv[0] if rv else None) if one else rv

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        password = request.form['password']
        role = request.form['role']
        
        # Check if the username is already registered
        user = query_db('SELECT * FROM Users WHERE username = ?', [username], one=True)
        if user:
            flash('Username already registered!')
            return redirect(url_for('register'))
        
        # Insert the new user into the database
        query_db('INSERT INTO Users (username, name, password, role) VALUES (?, ?, ?, ?)',
                 [username, name, password, role])
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the user is the admin
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['user_id'] = 'admin'
            session['role'] = 'admin'
            return redirect(url_for('admin_dashboard'))
        
        # Check if the user is a student or supervisor
        user = query_db('SELECT * FROM Users WHERE username = ? AND password = ?', [username, password], one=True)
        if user:
            session['user_id'] = user[0]
            session['role'] = user[4]
            if user[4] == 'student':
                return redirect(url_for('student_dashboard'))
            elif user[4] == 'supervisor':
                return redirect(url_for('supervisor_dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    
    # Fetch the logged-in student's details from the database
    student = query_db('SELECT * FROM Users WHERE id = ?', [session['user_id']], one=True)
    
    # Fetch the student's attachments (if any)
    attachments = query_db('SELECT * FROM Attachments WHERE student_id = ?', [session['user_id']])
    
    # Fetch the student's evaluations (if any)
    evaluations = query_db('SELECT * FROM Evaluations WHERE student_id = ?', [session['user_id']])
    
    return render_template('student.html', student=student, attachments=attachments, evaluations=evaluations)

@app.route('/supervisor/dashboard')
def supervisor_dashboard():
    if 'user_id' not in session or session['role'] != 'supervisor':
        return redirect(url_for('login'))
    students = query_db('SELECT * FROM Users WHERE role = "student"')
    return render_template('supervisor.html', students=students)

@app.route('/evaluate/<int:student_id>', methods=['GET', 'POST'])
def evaluate_student(student_id):
    if 'user_id' not in session or session['role'] != 'supervisor':
        return redirect(url_for('login'))

    if request.method == 'POST':
        supervisor_id = session['user_id']
        rating = request.form['rating']
        comments = request.form['comments']
        
        # Insert the evaluation into the Evaluations table
        query_db('INSERT INTO Evaluations (student_id, supervisor_id, rating, comments) VALUES (?, ?, ?, ?)',
                 [student_id, supervisor_id, rating, comments])
        flash('Evaluation submitted successfully!')
        return redirect(url_for('supervisor_dashboard'))

    # Render the evaluation form
    return render_template('evaluate.html', student_id=student_id)

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    users = query_db('SELECT * FROM Users')
    attachments = query_db('SELECT * FROM Attachments')
    evaluations = query_db('SELECT * FROM Evaluations')
    return render_template('admin.html', users=users, attachments=attachments, evaluations=evaluations)

@app.route('/add_attachment', methods=['GET', 'POST'])
def add_attachment():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        student_id = request.form['student_id']
        company_name = request.form['company_name']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        
        query_db('INSERT INTO Attachments (student_id, company_name, start_date, end_date) VALUES (?, ?, ?, ?)',
                 [student_id, company_name, start_date, end_date])
        flash('Attachment added successfully!')
        return redirect(url_for('admin_dashboard'))
    
    students = query_db('SELECT * FROM Users WHERE role = "student"')
    return render_template('add_attachment.html', students=students)

@app.route('/edit_attachment/<int:attachment_id>', methods=['GET', 'POST'])
def edit_attachment(attachment_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        company_name = request.form['company_name']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        
        query_db('UPDATE Attachments SET company_name = ?, start_date = ?, end_date = ? WHERE id = ?',
                 [company_name, start_date, end_date, attachment_id])
        flash('Attachment updated successfully!')
        return redirect(url_for('admin_dashboard'))
    
    attachment = query_db('SELECT * FROM Attachments WHERE id = ?', [attachment_id], one=True)
    return render_template('edit_attachment.html', attachment=attachment)

@app.route('/delete_attachment/<int:attachment_id>', methods=['POST'])
def delete_attachment(attachment_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    query_db('DELETE FROM Attachments WHERE id = ?', [attachment_id])
    flash('Attachment deleted successfully!')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5002)