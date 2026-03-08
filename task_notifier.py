"""
Task Notification System
Sends email reminders to users who have not completed their assigned tasks.

Setup:
  1. Fill in your SMTP credentials in the CONFIG section below.
  2. For Gmail, enable 2-Step Verification and use an App Password:
     https://myaccount.google.com/apppasswords
  3. Add/update tasks in tasks.json.
  4. Run:  python task_notifier.py
"""

import json
import smtplib
import ssl
import os
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIG — Read from environment variables or use defaults for local dev
# ---------------------------------------------------------------------------
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 465))
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "licayanelisonbrent@gmail.com")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "hjzqdoajxyvsniks")
TASKS_FILE = Path(__file__).parent / "tasks.json"
# ---------------------------------------------------------------------------


def load_tasks(filepath: Path) -> list[dict]:
    """Load task list from a JSON file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Tasks file not found: {filepath}")
    with filepath.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_incomplete_tasks(tasks: list[dict]) -> list[dict]:
    """Return tasks that are not completed and whose deadline has passed or is today."""
    today = date.today()
    overdue = []
    for task in tasks:
        if not task.get("completed", False):
            deadline = date.fromisoformat(task["deadline"])
            if deadline <= today:
                task["days_overdue"] = (today - deadline).days
                overdue.append(task)
    return overdue


def build_email(sender: str, task: dict) -> MIMEMultipart:
    """Build an HTML email message for a single incomplete task."""
    recipient = task["email"]
    assigned_to = task["assigned_to"]
    title = task["title"]
    deadline = task["deadline"]
    days_overdue = task.get("days_overdue", 0)

    overdue_note = (
        f"<p style='color:red;'>This task is <strong>{days_overdue} day(s) overdue</strong>.</p>"
        if days_overdue > 0
        else "<p style='color:orange;'>This task is <strong>due today</strong>.</p>"
    )

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #c0392b;">&#9888; Task Reminder</h2>
        <p>Hi <strong>{assigned_to}</strong>,</p>
        <p>This is a reminder that the following task has not been completed:</p>
        <table border="1" cellpadding="8" cellspacing="0"
               style="border-collapse:collapse; width:100%; max-width:500px;">
          <tr style="background:#f2f2f2;">
            <th align="left">Field</th>
            <th align="left">Details</th>
          </tr>
          <tr>
            <td><strong>Task</strong></td>
            <td>{title}</td>
          </tr>
          <tr>
            <td><strong>Deadline</strong></td>
            <td>{deadline}</td>
          </tr>
          <tr>
            <td><strong>Status</strong></td>
            <td style="color:red;">Incomplete</td>
          </tr>
        </table>
        {overdue_note}
        <p>Please complete this task as soon as possible.</p>
        <p>Thank you,<br/>Task Notification System</p>
      </body>
    </html>
    """

    message = MIMEMultipart("alternative")
    message["Subject"] = f"[REMINDER] Incomplete Task: {title}"
    message["From"] = sender
    message["To"] = recipient
    message.attach(MIMEText(html_body, "html"))
    return message


def send_notifications(incomplete_tasks: list[dict]) -> None:
    """Send email notifications for all incomplete tasks."""
    if not incomplete_tasks:
        print("No incomplete/overdue tasks found. No emails sent.")
        return

    context = ssl.create_default_context()

    print(f"Connecting to {SMTP_HOST}:{SMTP_PORT} ...")
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        print("Login successful.\n")

        for task in incomplete_tasks:
            try:
                email = build_email(SENDER_EMAIL, task)
                server.sendmail(SENDER_EMAIL, task["email"], email.as_string())
                status = "OVERDUE" if task.get("days_overdue", 0) > 0 else "DUE TODAY"
                print(f"  [{status}] Sent notification to {task['email']} — \"{task['title']}\"")
            except smtplib.SMTPException as exc:
                print(f"  [ERROR] Failed to send to {task['email']}: {exc}")

    print(f"\nDone. {len(incomplete_tasks)} notification(s) sent.")


def build_assignment_email(sender: str, task: dict) -> MIMEMultipart:
    """Build an HTML email message for a newly assigned task."""
    recipient = task["email"]
    assigned_to = task["assigned_to"]
    title = task["title"]
    deadline = task["deadline"]

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #27ae60;">&#10003; New Task Assigned</h2>
        <p>Hi <strong>{assigned_to}</strong>,</p>
        <p>You have been assigned a new task:</p>
        <table border="1" cellpadding="8" cellspacing="0"
               style="border-collapse:collapse; width:100%; max-width:500px;">
          <tr style="background:#f2f2f2;">
            <th align="left">Field</th>
            <th align="left">Details</th>
          </tr>
          <tr>
            <td><strong>Task</strong></td>
            <td>{title}</td>
          </tr>
          <tr>
            <td><strong>Deadline</strong></td>
            <td>{deadline}</td>
          </tr>
          <tr>
            <td><strong>Status</strong></td>
            <td style="color:orange;">Assigned</td>
          </tr>
        </table>
        <p>Please complete this task by the deadline.</p>
        <p>Thank you,<br/>Task Management System</p>
      </body>
    </html>
    """

    message = MIMEMultipart("alternative")
    message["Subject"] = f"[ASSIGNED] New Task: {title}"
    message["From"] = sender
    message["To"] = recipient
    message.attach(MIMEText(html_body, "html"))
    return message


def send_assignment_notification(task: dict) -> bool:
    """Send email notification for a newly assigned task. Returns True if successful."""
    try:
        print(f"[INFO] Attempting to send email to {task['email']}...")
        print(f"[INFO] Using SMTP: {SMTP_HOST}:{SMTP_PORT}")
        
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            print("[ERROR] SMTP credentials not configured. Set SENDER_EMAIL and SENDER_PASSWORD environment variables.")
            return False
        
        context = ssl.create_default_context()
        
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=10) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            email = build_assignment_email(SENDER_EMAIL, task)
            server.sendmail(SENDER_EMAIL, task["email"], email.as_string())
            print(f"[SUCCESS] Sent notification to {task['email']} — \"{task['title']}\"")
            return True
    except smtplib.SMTPAuthenticationError as exc:
        print(f"[ERROR] Authentication failed: {exc}. Check SENDER_EMAIL and SENDER_PASSWORD.")
        return False
    except smtplib.SMTPException as exc:
        print(f"[ERROR] SMTP error: {exc}")
        return False
    except Exception as exc:
        print(f"[ERROR] Unexpected error: {type(exc).__name__}: {exc}")
        return False


def print_summary(tasks: list[dict], incomplete: list[dict]) -> None:
    """Print a console summary before sending emails."""
    print("=" * 55)
    print(" TASK COMPLETION SUMMARY")
    print("=" * 55)
    print(f"  Total tasks   : {len(tasks)}")
    print(f"  Completed     : {sum(1 for t in tasks if t.get('completed'))}")
    print(f"  Incomplete    : {len(tasks) - sum(1 for t in tasks if t.get('completed'))}")
    print(f"  Due/Overdue   : {len(incomplete)}")
    print("=" * 55)

    if incomplete:
        print("\n  Tasks requiring notification:")
        for task in incomplete:
            days = task.get("days_overdue", 0)
            label = f"{days}d overdue" if days > 0 else "due today"
            print(f"    - [{label}] {task['title']} ({task['assigned_to']})")
    print()


def main() -> None:
    tasks = load_tasks(TASKS_FILE)
    incomplete = get_incomplete_tasks(tasks)
    print_summary(tasks, incomplete)
    send_notifications(incomplete)


if __name__ == "__main__":
    main()
