from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
import sqlite3

app = Flask(__name__, template_folder='templates')
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Database initialization with Users and Tasks tables
def init_db():
    with sqlite3.connect('tasks.db') as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'Pending',
                user_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        ''')
        conn.commit()



# Function to get a connection to the SQLite database
def get_db_connection():
    conn = sqlite3.connect('tasks.db')
    conn.row_factory = sqlite3.Row
    return conn

# User registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']  # In a real app, you should hash the password
        try:
            with sqlite3.connect('tasks.db') as conn:
                conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
                conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return 'Username already taken'
    return render_template('register.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']  # Store username in session
            return redirect(url_for('index'))
        else:
            return 'Invalid username or password'
    return render_template('login.html')


# Logout functionality
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Display tasks for logged-in user
@app.route('/', methods=['GET', 'POST'])
def index():
    if not 'user_id' in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        add_task(title, description, session['user_id'])
        return redirect(url_for('index'))

    tasks = get_tasks_for_user(session['user_id'])
    return render_template('index.html', tasks=tasks)

# Function to add a new task to the database
def add_task(title, description, user_id):
    conn = get_db_connection()
    conn.execute('INSERT INTO tasks (title, description, user_id) VALUES (?, ?, ?)', 
                 (title, description, user_id))
    conn.commit()
    conn.close()

# Function to get tasks for a specific user
def get_tasks_for_user(user_id):
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    return tasks

# Function to update a task
@app.route('/update/<int:task_id>', methods=['GET', 'POST'])
def update(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        status = request.form['status']
        update_task(task_id, title, description, status)
        return redirect(url_for('index'))

    task = get_task(task_id)
    if task and task['user_id'] == session['user_id']:
        return render_template('update.html', task=task)
    return 'Task not found or access denied', 404

# Function to update a task in the database
def update_task(id, title, description, status):
    conn = get_db_connection()
    conn.execute('UPDATE tasks SET title = ?, description = ?, status = ? WHERE id = ?',
                 (title, description, status, id))
    conn.commit()
    conn.close()

# Function to delete a task
@app.route('/delete/<int:task_id>')
def delete(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task = get_task(task_id)
    if task and task['user_id'] == session['user_id']:
        delete_task(task_id)
        return redirect(url_for('index'))
    return 'Task not found or access denied', 404

# Function to delete a task from the database
def delete_task(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tasks WHERE id = ?', (id,))
    conn.commit()
    conn.close()

# Helper function to get a single task
def get_task(task_id):
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    conn.close()
    return task

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
