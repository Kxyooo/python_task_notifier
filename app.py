from flask import Flask, render_template_string, request, jsonify
import json
from pathlib import Path
from task_notifier import load_tasks, send_assignment_notification
import os

app = Flask(__name__)

TASKS_FILE = Path(__file__).parent / "tasks.json"
LAST_SENT_FILE = Path(__file__).parent / "last_sent.txt"

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
            height: 100vh;
        }

        .container {
            width: 780px; /* Matched to image proportions */
            background-color: var(--content-bg);
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
            overflow: hidden;
            border: 1px solid #e1e6ef; /* Subtle edge */
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
                </div>
            </div>

            <div class="task-list">
                {% for task in tasks %}
                <div class="task-item">
                    <div class="task-left">
                        <div class="circle-icon"></div>
                        <span class="task-title">{{ task.title }}</span>
                    </div>
                    <div class="trash-icon"></div>
                </div>
                {% endfor %}
            </div>

            <div class="add-task-line">
                <form id="add-task-form" class="add-task-form">
                    <input type="text" id="task-title" class="add-task-input" placeholder="Enter task title" required>
                    <input type="text" id="assigned-to" class="form-input" placeholder="Assigned to" required>
                    <input type="email" id="email" class="form-input" placeholder="Email" required>
                    <input type="date" id="deadline" class="form-input" required>
                    <button type="submit" class="btn btn-blue">Add Task</button>
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
                    location.reload(); // Reload to show new task
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while adding the task.');
            });
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    tasks = load_tasks(TASKS_FILE)
    active_count = sum(1 for t in tasks if not t.get("completed", False))
    completed_count = len(tasks) - active_count
    last_sent = load_last_sent()
    return render_template_string(HTML_TEMPLATE, tasks=tasks, active_count=active_count, completed_count=completed_count, last_sent=last_sent)

@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.get_json()
    title = data.get('title')
    assigned_to = data.get('assigned_to')
    email = data.get('email')
    deadline = data.get('deadline')
    
    if not all([title, assigned_to, email, deadline]):
        return jsonify({'error': 'All fields are required'}), 400
    
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
    send_assignment_notification(new_task)
    save_last_sent(new_task['email'])
    
    return jsonify({'message': 'Task added successfully', 'task': new_task})

if __name__ == '__main__':
    # Start the Flask web server
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server... Open http://127.0.0.1:{port} in your browser.")
    app.run(host='0.0.0.0', port=port, debug=False)

    