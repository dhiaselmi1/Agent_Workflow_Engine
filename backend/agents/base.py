import os
import requests
from datetime import datetime
from tinydb import TinyDB, Query
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
import uuid

# Database setup
db = TinyDB(os.path.join(os.path.dirname(__file__), "../../memory/memory_store.json"))
Topic = Query()
Workflow = Query()
Session = Query()


def call_llm(prompt: str) -> str:
    """Call the local LLM API."""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "llama3", "prompt": prompt, "stream": False}
    )
    return response.json()["response"].strip()


def log_agent_response(topic: str, agent: str, content: str, session_id: str = None):
    """Log agent response to database with optional session tracking."""
    entry = {
        "agent": agent,
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": session_id
    }

    if db.contains(Topic.name == topic):
        db.update(lambda t: t["log"].append(entry), Topic.name == topic)
    else:
        db.insert({"name": topic, "log": [entry]})


def get_topic_log(topic: str, session_id: str = None) -> List[Dict]:
    """Retrieve logs for a topic, optionally filtered by session."""
    result = db.search(Topic.name == topic)
    if not result:
        return []

    logs = result[0]["log"]

    if session_id:
        logs = [log for log in logs if log.get("session_id") == session_id]

    return logs


def create_workflow(name: str, topic: str, agents: List[str], schedule: str,
                    notification_config: Dict = None) -> str:
    """Create a new workflow configuration."""
    workflow_id = str(uuid.uuid4())
    workflow = {
        "id": workflow_id,
        "name": name,
        "topic": topic,
        "agents": agents,
        "schedule": schedule,
        "notification_config": notification_config or {},
        "created_at": datetime.utcnow().isoformat(),
        "active": True,
        "last_run": None
    }

    db.insert(workflow)
    return workflow_id


def get_workflow(workflow_id: str) -> Optional[Dict]:
    """Retrieve a workflow by ID."""
    result = db.search(Workflow.id == workflow_id)
    return result[0] if result else None


def get_all_workflows() -> List[Dict]:
    """Get all workflows."""
    return db.search(Workflow.id.exists())


def update_workflow(workflow_id: str, updates: Dict) -> bool:
    """Update a workflow configuration."""
    try:
        db.update(updates, Workflow.id == workflow_id)
        return True
    except Exception:
        return False


def delete_workflow(workflow_id: str) -> bool:
    """Delete a workflow."""
    try:
        db.remove(Workflow.id == workflow_id)
        return True
    except Exception:
        return False


def create_workflow_session(workflow_id: str) -> str:
    """Create a new session for workflow execution."""
    session_id = str(uuid.uuid4())
    session = {
        "id": session_id,
        "workflow_id": workflow_id,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "status": "running",
        "results": [],
        "errors": []
    }

    db.insert(session)
    return session_id


def update_session_status(session_id: str, status: str, completed_at: str = None):
    """Update session status."""
    updates = {"status": status}
    if completed_at:
        updates["completed_at"] = completed_at

    db.update(updates, Session.id == session_id)


def add_session_result(session_id: str, agent: str, result: str, error: str = None):
    """Add result to a session."""
    if error:
        db.update(lambda s: s["errors"].append({
            "agent": agent,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }), Session.id == session_id)
    else:
        db.update(lambda s: s["results"].append({
            "agent": agent,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }), Session.id == session_id)


def get_session(session_id: str) -> Optional[Dict]:
    """Get session by ID."""
    result = db.search(Session.id == session_id)
    return result[0] if result else None


def get_workflow_sessions(workflow_id: str) -> List[Dict]:
    """Get all sessions for a workflow."""
    return db.search(Session.workflow_id == workflow_id)


def send_email_notification(to_email: str, subject: str, body: str,
                            smtp_config: Dict = None):
    """Send email notification."""
    if not smtp_config:
        # Default SMTP configuration (adjust as needed)
        smtp_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": os.getenv("SMTP_USERNAME"),
            "password": os.getenv("SMTP_PASSWORD")
        }

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_config["username"]
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(smtp_config["smtp_server"], smtp_config["smtp_port"])
        server.starttls()
        server.login(smtp_config["username"], smtp_config["password"])
        text = msg.as_string()
        server.sendmail(smtp_config["username"], to_email, text)
        server.quit()

        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def send_slack_notification(webhook_url: str, message: str):
    """Send Slack notification."""
    try:
        payload = {"text": message}
        response = requests.post(webhook_url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send Slack notification: {e}")
        return False


def notify_workflow_completion(workflow: Dict, session: Dict):
    """Send notifications for completed workflow."""
    notification_config = workflow.get("notification_config", {})

    # Prepare notification content
    subject = f"Workflow '{workflow['name']}' Completed"

    results_summary = []
    for result in session.get("results", []):
        results_summary.append(f"• {result['agent']}: {result['result'][:100]}...")

    errors_summary = []
    for error in session.get("errors", []):
        errors_summary.append(f"• {error['agent']}: {error['error']}")

    body = f"""
    <h2>Workflow Execution Summary</h2>
    <p><strong>Workflow:</strong> {workflow['name']}</p>
    <p><strong>Topic:</strong> {workflow['topic']}</p>
    <p><strong>Started:</strong> {session['started_at']}</p>
    <p><strong>Completed:</strong> {session['completed_at']}</p>
    <p><strong>Status:</strong> {session['status']}</p>

    <h3>Results:</h3>
    <ul>
    {''.join(f'<li>{result}</li>' for result in results_summary)}
    </ul>

    {f'<h3>Errors:</h3><ul>{"".join(f"<li>{error}</li>" for error in errors_summary)}</ul>' if errors_summary else ''}
    """

    # Send email notification
    if notification_config.get("email"):
        send_email_notification(
            notification_config["email"],
            subject,
            body,
            notification_config.get("smtp_config")
        )

    # Send Slack notification
    if notification_config.get("slack_webhook"):
        slack_message = f"🤖 Workflow '{workflow['name']}' completed for topic '{workflow['topic']}'. Status: {session['status']}"
        if session.get("errors"):
            slack_message += f" (with {len(session['errors'])} errors)"

        send_slack_notification(notification_config["slack_webhook"], slack_message)


def format_workflow_results(session: Dict) -> str:
    """Format workflow results for dashboard display."""
    results_text = []

    for result in session.get("results", []):
        results_text.append(f"**{result['agent']}** ({result['timestamp']}):\n{result['result']}\n")

    if session.get("errors"):
        results_text.append("\n**Errors:**\n")
        for error in session["errors"]:
            results_text.append(f"• {error['agent']}: {error['error']}\n")

    return "\n".join(results_text)