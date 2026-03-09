from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import json
from pathlib import Path
from task_notifier import load_tasks, send_assignment_notification
import os

app = Flask(__name__)

TASKS_FILE = Path(__file__).parent / "tasks.json"
LAST_SENT_FILE = Path(__file__).parent / "last_sent.txt"

# simple user store - replace with real datastore or env variables in production
USERS = {
    "Admin": "Password123"
}

app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")


def login_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper

def save_tasks(tasks: list[dict]) -> None:
    """Save task list to JSON file."""
    with TASKS_FILE.open("w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)

def save_last_sent(email: str) -> None:
    """Save the last sent email."""
    with LAST_SENT_FILE.open("w", encoding="utf-8") as f:
        f.write(email)

def load_last_sent() -> str:
    """Load the last sent email."""
    if LAST_SENT_FILE.exists():
        with LAST_SENT_FILE.open("r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

# HTML Template defined as a Python string
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Task Reminder</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            position: relative;
            overflow: hidden;
        }

        /* Animated background */
        body::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px);
            background-size: 50px 50px;
            animation: float 20s infinite linear;
        }

        @keyframes float {
            0% { transform: translate(0, 0); }
            100% { transform: translate(50px, 50px); }
        }

        .login-container {
            position: relative;
            z-index: 1;
        }

        .login-box {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 50px 40px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            width: 100%;
            max-width: 400px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .login-box h2 {
            font-size: 32px;
            font-weight: 700;
            color: #333;
            margin-bottom: 30px;
            text-align: center;
        }

        .error {
            color: #e74c3c;
            font-size: 14px;
            background: #fadbd8;
            padding: 10px 12px;
            border-radius: 6px;
            margin-bottom: 20px;
            border-left: 4px solid #e74c3c;
        }

        .form-group {
            margin-bottom: 20px;
            position: relative;
        }

        .form-group label {
            display: block;
            font-size: 13px;
            color: #666;
            margin-bottom: 8px;
            font-weight: 500;
        }

        .input-wrapper {
            position: relative;
            display: flex;
            align-items: center;
        }

        .form-group input {
            width: 100%;
            padding: 12px 15px 12px 40px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s;
            background: #f8f9fa;
        }

        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            background: #fff;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .form-group .icon {
            position: absolute;
            left: 12px;
            color: #999;
            font-size: 16px;
        }

        .toggle-password {
            position: absolute;
            right: 12px;
            background: none;
            border: none;
            color: #667eea;
            cursor: pointer;
            font-size: 16px;
            padding: 5px;
            transition: all 0.3s;
        }

        .toggle-password:hover {
            color: #764ba2;
            transform: scale(1.1);
        }

        .form-options {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            font-size: 13px;
        }

        .checkbox-wrapper {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .checkbox-wrapper input[type="checkbox"] {
            width: 16px;
            height: 16px;
            cursor: pointer;
            accent-color: #667eea;
        }

        .checkbox-wrapper label {
            margin: 0;
            cursor: pointer;
            color: #666;
        }

        .forgot-password {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s;
        }

        .forgot-password:hover {
            color: #764ba2;
            text-decoration: underline;
        }

        .login-box button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }

        .login-box button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }

        .login-box button:active {
            transform: translateY(0);
        }

        .register-link {
            text-align: center;
            margin-top: 20px;
            font-size: 13px;
            color: #666;
        }

        .register-link a {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s;
        }

        .register-link a:hover {
            color: #764ba2;
            text-decoration: underline;
        }

        /* Responsive */
        @media (max-width: 480px) {
            .login-box {
                padding: 40px 25px;
                margin: 20px;
            }

            .login-box h2 {
                font-size: 24px;
            }

            .form-options {
                flex-direction: column;
                gap: 12px;
                align-items: flex-start;
            }
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-box">
            <h2>Login</h2>
            {% if error %}<div class="error">{{ error }}</div>{% endif %}
            
            <form method="post" id="loginForm">
                <!-- Username Field -->
                <div class="form-group">
                    <label for="username">Username</label>
                    <div class="input-wrapper">
                        <i class="fas fa-user icon"></i>
                        <input type="text" id="username" name="username" placeholder="Enter your username" required>
                    </div>
                </div>

                <!-- Password Field -->
                <div class="form-group">
                    <label for="password">Password</label>
                    <div class="input-wrapper">
                        <i class="fas fa-lock icon"></i>
                        <input type="password" id="password" name="password" placeholder="Enter your password" required>
                        <button type="button" class="toggle-password" id="togglePassword" onclick="togglePassword()">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                </div>

                <!-- Remember Me & Forgot Password -->
                <div class="form-options">
                    <div class="checkbox-wrapper">
                        <input type="checkbox" id="remember" name="remember" value="on">
                        <label for="remember">Remember me</label>
                    </div>
                    <a href="#" class="forgot-password">Forgot password?</a>
                </div>

                <!-- Login Button -->
                <button type="submit">Login</button>
            </form>

            <!-- Register Link -->
            <div class="register-link">
                Don't have an account? <a href="#">Register</a>
            </div>
        </div>
    </div>

    <script>
        function togglePassword() {
            const passwordInput = document.getElementById('password');
            const toggleBtn = document.getElementById('togglePassword');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                toggleBtn.innerHTML = '<i class="fas fa-eye-slash"></i>';
            } else {
                passwordInput.type = 'password';
                toggleBtn.innerHTML = '<i class="fas fa-eye"></i>';
            }
        }

        // Optional: Add visual feedback on form submission
        document.getElementById('loginForm').addEventListener('submit', function() {
            const btn = this.querySelector('button[type="submit"]');
            btn.disabled = true;
            btn.textContent = 'Logging in...';
        });
    </script>
</body>
</html>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Reminder System</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        :root {
            /* Exact color matching from the image */
            --primary-blue: #3260de; /* The main blue color */
            --bg-color: #f1f3f7;     /* The light grey background outside the box */
            --content-bg: #fdfefe;   /* The white/off-white content area */
            --text-on-blue: #fefefe; 
            --text-primary: #111111; 
            --text-secondary: #777c85; /* For dates and status */
            --text-tertiary: #a4abb4;  /* For the icon in input */
            --border-color: #f1f3f7;  /* Border around the task list */
            --btn-light-bg: #f2f3f7;  /* Background for 'Check & Notify' */
            --font-family: 'Poppins', sans-serif;
        }

        body {
            font-family: var(--font-family);
            background-color: var(--bg-color);
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }

        .container {
            width: 780px; /* Matched to image proportions */
            background-color: var(--content-bg);
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
            overflow: hidden;
            border: 1px solid #e1e6ef; /* Subtle edge */
            margin-top: 20px; /* To align with header padding */
            margin-bottom: 20px;
        }

        /* --- Blue Header Section --- */
        .header {
            background-color: var(--primary-blue);
            padding: 30px 40px;
            color: var(--text-on-blue);
        }

        .header h1 {
            margin: 0;
            font-size: 30px;
            font-weight: 700;
        }

        .header p {
            margin: 6px 0 16px 0;
            font-size: 13px;
            font-weight: 300;
            opacity: 0.9;
        }

        .email-info {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
        }

        /* Replicating the 'p' icon, scaled down */
        .p-icon {
            display: inline-block;
            font-family: 'Times New Roman', serif;
            font-weight: bold;
            font-size: 10px;
            text-transform: lowercase;
            padding: 0 4px;
            margin-right: 2px;
            border: 1px solid #7c98e8;
            border-radius: 3px;
            background: #4770e2; /* Slightly darker than main blue */
        }

        /* --- Content Section --- */
        .content {
            padding: 25px 40px;
        }

        .top-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }

        .title-section h2 {
            margin: 0;
            font-size: 20px;
            font-weight: 600;
            color: var(--text-primary);
        }

        .title-section .status {
            font-size: 11px;
            color: var(--text-secondary);
            margin-top: 3px;
        }

        .action-buttons {
            display: flex;
            gap: 10px;
        }

        .btn {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            border-radius: 7px;
            font-size: 13px;
            cursor: pointer;
            border: none;
            text-decoration: none;
            font-family: var(--font-family);
        }

        .btn-light {
            background-color: var(--btn-light-bg);
            color: var(--text-primary);
        }
        
        /* Simulating the notification icon */
        .btn-light::before {
            content: '▧'; /* Unicode similar to the bell/grid */
            font-size: 15px;
            opacity: 0.8;
        }

        .btn-blue {
            background-color: var(--primary-blue);
            color: var(--text-on-blue);
            font-weight: 500;
        }

        /* --- Task List Section --- */
        .task-list {
            margin-bottom: 15px;
        }

        .task-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px 20px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-tertiary);
            position: relative;
        }

        .task-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .circle-icon {
            width: 14px;
            height: 14px;
            border: 1.5px solid var(--text-tertiary);
            border-radius: 50%;
        }

        .task-title {
            font-size: 13px;
            color: var(--text-tertiary);
            margin-top: -1px;
        }

        /* Simulating the trash can icon with border technique */
        .trash-icon {
            width: 13px;
            height: 17px;
            border: 1px solid var(--text-tertiary);
            position: relative;
            margin-right: 5px;
        }
        .trash-icon::before { /* Lid */
            content: '';
            position: absolute;
            top: -3px;
            left: 1px;
            width: 9px;
            height: 2px;
            border: 1px solid var(--text-tertiary);
        }

        .add-task-line {
            padding-left: 20px;
            display: flex;
            align-items: center;
            position: relative;
        }

        /* Vertical grey line to the left of task input */
        .add-task-line::before {
            content: '';
            position: absolute;
            left: 26px;
            top: -20px;
            width: 1px;
            height: 70px;
            background-color: var(--border-color);
        }

        .add-task-input {
            width: calc(100% - 20px);
            padding: 12px 10px 12px 35px; /* Offset for line */
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background-color: var(--content-bg);
            color: var(--text-tertiary);
            font-family: var(--font-family);
            font-size: 13px;
        }
        
        .add-task-form {
            display: none;
            flex-direction: column;
            gap: 10px;
            margin-top: 10px;
        }

        .add-task-form.show {
            display: flex;
        }

        .form-input {
            padding: 8px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            font-family: var(--font-family);
            font-size: 13px;
        }

        .add-task-form .add-task-input {
            margin-bottom: 10px;
        }

        .task-actions {
            display: flex;
            gap: 8px;
        }

        .edit-btn, .delete-btn {
            padding: 6px 10px;
            border: none;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
            font-family: var(--font-family);
        }

        .edit-btn {
            background-color: #4a90e2;
            color: white;
        }

        .delete-btn {
            background-color: #e74c3c;
            color: white;
        }

        .edit-btn:hover {
            background-color: #357abd;
        }

        .delete-btn:hover {
            background-color: #c0392b;
        }

        .btn-blue:disabled {
            opacity: 0.7;
            cursor: not-allowed;
        }

        .spinner {
            display: inline-block;
            width: 12px;
            height: 12px;
            border: 2px solid rgba(255,255,255,0.4);
            border-top-color: #fff;
            border-radius: 50%;
            animation: spin 0.7s linear infinite;
            vertical-align: middle;
            margin-right: 6px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Task Reminder System</h1>
            <p>Stay on top of your activities with email notifications</p>
            <div class="email-info">
                <span class="p-icon">p</span>
                <span>{% if last_sent %}Successfully sent email to: {{ last_sent }}{% else %}{% endif %}</span>
            </div>
        </div>

        <div class="content">
            <div class="top-bar">
                <div class="title-section">
                    <h2>Your Tasks</h2>
                    <div class="status">{{ active_count }} active • {{ completed_count }} completed</div>
                </div>
                <div class="action-buttons">
                    <button class="btn btn-light">Check & Notify</button>
                    <button class="btn btn-blue" id="add-task-btn"><span>+</span> Add Task</button>
                    <a href="/logout" class="btn btn-light">Logout</a>
                </div>
            </div>

            <div class="task-list">
                {% for task in tasks %}
                <div class="task-item" data-task-id="{{ task.id }}">
                    <div class="task-left">
                        <div class="circle-icon"></div>
                        <span class="task-title">{{ task.title }}</span>
                    </div>
                    <div class="task-actions">
                        <button class="edit-btn" data-id="{{ task.id }}">Edit</button>
                        <button class="delete-btn" data-id="{{ task.id }}">Remove</button>
                    </div>
                </div>
                {% endfor %}
            </div>

            <div class="add-task-line">
                <form id="add-task-form" class="add-task-form">
                    <input type="text" id="task-title" class="add-task-input" placeholder="Enter task title" required>
                    <input type="text" id="assigned-to" class="form-input" placeholder="Assigned to" required>
                    <input type="email" id="email" class="form-input" placeholder="Email" required>
                    <input type="date" id="deadline" class="form-input" required>
                    <button type="submit" class="btn btn-blue" id="add-task-submit">Add Task</button>
                </form>
            </div>
        </div>
    </div>
    <script>
        document.getElementById('add-task-btn').addEventListener('click', function() {
            document.getElementById('add-task-form').classList.toggle('show');
            document.getElementById('task-title').focus();
        });

        document.getElementById('add-task-form').addEventListener('submit', function(e) {
            e.preventDefault();
            const title = document.getElementById('task-title').value;
            const assignedTo = document.getElementById('assigned-to').value;
            const email = document.getElementById('email').value;
            const deadline = document.getElementById('deadline').value;

            const submitBtn = document.getElementById('add-task-submit');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner"></span>Sending...';

            fetch('/add_task', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: title,
                    assigned_to: assignedTo,
                    email: email,
                    deadline: deadline
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.message) {
                    alert('Task added successfully!');
                    location.reload();
                } else {
                    alert('Error: ' + data.error);
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = 'Add Task';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while adding the task.');
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Add Task';
            });
        });

        // Edit task
        document.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const taskId = this.getAttribute('data-id');
                const taskItem = document.querySelector(`[data-task-id="${taskId}"]`);
                const taskTitle = taskItem.querySelector('.task-title').textContent;
                
                const newTitle = prompt('Edit task title:', taskTitle);
                if (newTitle && newTitle.trim() !== '') {
                    fetch('/edit_task', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            id: taskId,
                            title: newTitle.trim()
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.message) {
                            alert('Task updated successfully!');
                            location.reload();
                        } else {
                            alert('Error: ' + data.error);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('An error occurred while editing the task.');
                    });
                }
            });
        });

        // Delete task
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const taskId = this.getAttribute('data-id');
                const taskItem = document.querySelector(`[data-task-id="${taskId}"]`);
                const taskTitle = taskItem.querySelector('.task-title').textContent;
                
                if (confirm(`Are you sure you want to delete "${taskTitle}"?`)) {
                    fetch('/delete_task', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            id: taskId
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.message) {
                            alert('Task deleted successfully!');
                            location.reload();
                        } else {
                            alert('Error: ' + data.error);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('An error occurred while deleting the task.');
                    });
                }
            });
        });
    </script>
</body>
</html>
"""

@app.route('/')
@login_required
def home():
    tasks = load_tasks(TASKS_FILE)
    active_count = sum(1 for t in tasks if not t.get("completed", False))
    completed_count = len(tasks) - active_count
    last_sent = load_last_sent()
    return render_template_string(HTML_TEMPLATE, tasks=tasks, active_count=active_count, completed_count=completed_count, last_sent=last_sent)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if USERS.get(username) == password:
            session['user'] = username
            return redirect(url_for('home'))
        else:
            error = 'Invalid credentials'
    return render_template_string(LOGIN_TEMPLATE, error=error)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    data = request.get_json()
    title = data.get('title')
    assigned_to = data.get('assigned_to')
    email = data.get('email')
    deadline = data.get('deadline')
    
    if not all([title, assigned_to, email, deadline]):
        return jsonify({'error': 'All fields are required'}), 400
    
    try:
        tasks = load_tasks(TASKS_FILE)
        new_id = max(t['id'] for t in tasks) + 1 if tasks else 1
        new_task = {
            'id': new_id,
            'title': title,
            'assigned_to': assigned_to,
            'email': email,
            'deadline': deadline,
            'completed': False
        }
        tasks.append(new_task)
        save_tasks(tasks)
        
        # Send assignment notification
        email_sent = send_assignment_notification(new_task)
        if email_sent:
            save_last_sent(new_task['email'])
            message = 'Task added successfully and notification sent!'
        else:
            message = 'Task added but email notification failed. Check server logs.'
        
        return jsonify({'message': message, 'task': new_task, 'email_sent': email_sent})
    except Exception as e:
        print(f"[ERROR] Exception in add_task: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/edit_task', methods=['POST'])
@login_required
def edit_task():
    data = request.get_json()
    task_id = int(data.get('id'))
    new_title = data.get('title')
    
    if not new_title or not new_title.strip():
        return jsonify({'error': 'Title cannot be empty'}), 400
    
    tasks = load_tasks(TASKS_FILE)
    task = next((t for t in tasks if t['id'] == task_id), None)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    task['title'] = new_title.strip()
    save_tasks(tasks)
    
    return jsonify({'message': 'Task updated successfully', 'task': task})


@app.route('/delete_task', methods=['POST'])
@login_required
def delete_task():
    data = request.get_json()
    task_id = int(data.get('id'))
    
    tasks = load_tasks(TASKS_FILE)
    original_count = len(tasks)
    tasks = [t for t in tasks if t['id'] != task_id]
    
    if len(tasks) == original_count:
        return jsonify({'error': 'Task not found'}), 404
    
    save_tasks(tasks)
    return jsonify({'message': 'Task deleted successfully'})

if __name__ == '__main__':
    # Start the Flask web server
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server... Open http://127.0.0.1:{port} in your browser.")
    app.run(host='0.0.0.0', port=port, debug=False)