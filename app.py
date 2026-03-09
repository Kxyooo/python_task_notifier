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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background: linear-gradient(180deg, #5a2a7a 0%, #3d1e5c 30%, #2a1845 60%, #1a0f2e 100%);
            position: relative;
            overflow: hidden;
        }

        /* Starfield background */
        body::before {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            background-image: 
                radial-gradient(2px 2px at 20px 30px, #eee, rgba(0,0,0,0)),
                radial-gradient(2px 2px at 60px 70px, #fff, rgba(0,0,0,0)),
                radial-gradient(1px 1px at 50px 50px, #ddd, rgba(0,0,0,0)),
                radial-gradient(1px 1px at 130px 80px, #fff, rgba(0,0,0,0)),
                radial-gradient(2px 2px at 90px 10px, #eee, rgba(0,0,0,0));
            background-repeat: repeat;
            background-size: 200px 200px;
            animation: twinkle 5s ease-in-out infinite;
            opacity: 0.6;
        }

        @keyframes twinkle {
            0%, 100% { opacity: 0.5; }
            50% { opacity: 1; }
        }

        /* Mountain silhouettes */
        body::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 40%;
            background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 400"><defs><linearGradient id="mg" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" style="stop-color:rgba(0,0,0,0.3)"/><stop offset="100%" style="stop-color:rgba(0,0,0,0.7)"/></linearGradient></defs><path fill="url(%23mg)" d="M0,250 L100,150 L150,200 L250,80 L350,180 L450,100 L550,160 L650,90 L750,170 L850,110 L950,190 L1050,120 L1150,180 L1200,150 L1200,400 L0,400 Z"/><path fill="rgba(0,0,0,0.2)" d="M0,300 L80,220 L180,280 L280,200 L380,270 L480,210 L580,260 L680,200 L780,250 L880,190 L980,240 L1080,180 L1180,220 L1200,200 L1200,400 L0,400 Z"/></svg>') repeat-x;
            background-size: 1200px 400px;
            opacity: 0.8;
            pointer-events: none;
        }

        .login-container {
            position: relative;
            z-index: 1;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .login-box {
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 45px 40px;
            width: 100%;
            max-width: 420px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        .login-box h2 {
            font-size: 36px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 35px;
            text-align: center;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        }

        .error {
            color: #ff6b6b;
            font-size: 13px;
            background: rgba(255, 107, 107, 0.15);
            padding: 10px 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 3px solid #ff6b6b;
            border-radius: 6px;
        }

        .form-group {
            margin-bottom: 20px;
            position: relative;
        }

        .input-wrapper {
            position: relative;
            display: flex;
            align-items: center;
        }

        /* ensure space for the eye icon inside inputs */
        .form-group input {
            padding-right: 40px; /* make room for toggle button */
        }

        .form-group input {
            width: 100%;
            padding: 14px 16px 14px 45px;
            background: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 10px;
            font-size: 15px;
            color: #ffffff;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }

        .form-group input::placeholder {
            color: rgba(255, 255, 255, 0.6);
        }

        .form-group input:focus {
            outline: none;
            background: rgba(255, 255, 255, 0.2);
            border-color: rgba(255, 255, 255, 0.4);
            box-shadow: 0 0 20px rgba(168, 85, 247, 0.3);
        }

        .form-group .icon {
            position: absolute;
            left: 14px;
            color: rgba(255, 255, 255, 0.7);
            font-size: 16px;
            pointer-events: none;
        }

        .toggle-password {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            right: 12px;
            background: transparent;
            border: none;
            color: rgba(255, 255, 255, 0.7);
            cursor: pointer;
            font-size: 16px;
            padding: 0;
            width: auto;
            height: auto;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2;
        }

        .toggle-password:hover {
            color: rgba(255, 255, 255, 1);
        }



        .toggle-password:hover {
            color: rgba(255, 255, 255, 1);
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
            gap: 8px;
        }

        .checkbox-wrapper input[type="checkbox"] {
            width: 18px;
            height: 18px;
            cursor: pointer;
            accent-color: #a855f7;
            border-radius: 3px;
        }

        .checkbox-wrapper label {
            margin: 0;
            cursor: pointer;
            color: rgba(255, 255, 255, 0.8);
            font-weight: 500;
        }

        .login-box button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
            color: #333333;
            border: none;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(255, 255, 255, 0.2);
        }

        .login-box button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 255, 255, 0.3);
            background: linear-gradient(135deg, #f5f5f5 0%, #ffffff 100%);
        }

        .login-box button:active {
            transform: translateY(0);
        }

        @media (max-width: 480px) {
            .login-box {
                padding: 35px 25px;
                margin: 20px;
                border-radius: 15px;
            }

            .login-box h2 {
                font-size: 28px;
                margin-bottom: 25px;
            }

            .form-options {
                flex-direction: column;
                gap: 15px;
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
                    <div class="input-wrapper">
                        <i class="fas fa-user icon"></i>
                        <input type="text" id="username" name="username" placeholder="Username" required>
                    </div>
                </div>

                <!-- Password Field -->
                <div class="form-group">
                    <div class="input-wrapper">
                        <i class="fas fa-lock icon"></i>
                        <input type="password" id="password" name="password" placeholder="Password" required>
                        <button type="button" class="toggle-password" id="togglePassword" onclick="togglePassword()">
                            <i class="fas fa-eye"></i>
                        </button>
                    </div>
                </div>

                <!-- Remember Me -->
                <div class="form-options">
                    <div class="checkbox-wrapper">
                        <input type="checkbox" id="remember" name="remember" value="on">
                        <label for="remember">Remember me</label>
                    </div>
                </div>

                <!-- Login Button -->
                <button type="submit">Login</button>
            </form>
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

        // Add visual feedback on form submission
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