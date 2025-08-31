import os
import time
from datetime import datetime
from typing import Dict, List

import pdfkit
import requests
import streamlit as st

st.set_page_config(page_title="Agent Workflow Engine", layout="wide", page_icon="🤖")

# --- Configuration ---
API_URL = "http://localhost:8000"

# Configuration for PDF export
try:
    path_wkhtmltopdf = pdfkit.configuration().wkhtmltopdf
    config_pdf = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    PDF_AVAILABLE = True
except OSError:
    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    if os.path.exists(path_wkhtmltopdf):
        config_pdf = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
        PDF_AVAILABLE = True
    else:
        PDF_AVAILABLE = False

# Visual settings for each agent
AGENT_VISUALS = {
    "Research": {"icon": "🔬", "color": "#4CAF50"},
    "Summarizer": {"icon": "📝", "color": "#2196F3"},
    "Insight": {"icon": "💡", "color": "#FFC107"},
    "Devil": {"icon": "😈", "color": "#F44336"},
    "default": {"icon": "🤖", "color": "#9E9E9E"}
}

SCHEDULE_PRESETS = {
    "Daily at 9 AM": "0 9 * * *",
    "Every Monday at 9 AM": "0 9 * * 1",
    "Every 6 hours": "0 */6 * * *",
    "Every hour": "0 * * * *",
    "Weekly on Sunday": "0 9 * * 0",
    "Custom": "custom"
}


# --- Helper Functions ---
@st.cache_data(ttl=30)
def check_api_status():
    """Check if the FastAPI backend is running."""
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False


@st.cache_data(ttl=60)
def fetch_workflows():
    """Fetch all workflows from the API."""
    try:
        response = requests.get(f"{API_URL}/workflows")
        response.raise_for_status()
        return response.json().get("workflows", [])
    except Exception as e:
        st.error(f"Error fetching workflows: {e}")
        return []


@st.cache_data(ttl=30)
def fetch_scheduler_status():
    """Fetch scheduler status."""
    try:
        response = requests.get(f"{API_URL}/scheduler/status")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching scheduler status: {e}")
        return {}


@st.cache_data(ttl=30)
def fetch_workflow_sessions(workflow_id: str):
    """Fetch sessions for a workflow."""
    try:
        response = requests.get(f"{API_URL}/workflows/{workflow_id}/sessions")
        response.raise_for_status()
        return response.json().get("sessions", [])
    except Exception as e:
        st.error(f"Error fetching sessions: {e}")
        return []


@st.cache_data(ttl=30)
def fetch_session_results(session_id: str):
    """Fetch results for a session."""
    try:
        response = requests.get(f"{API_URL}/sessions/{session_id}/results")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching session results: {e}")
        return {}


def create_workflow(name: str, topic: str, agents: List[str], schedule: str,
                    notification_config: Dict = None):
    """Create a new workflow."""
    try:
        payload = {
            "name": name,
            "topic": topic,
            "agents": agents,
            "schedule": schedule,
            "notification_config": notification_config or {}
        }
        response = requests.post(f"{API_URL}/workflows", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error creating workflow: {e}")
        return None


def run_workflow_manually(workflow_id: str, manual_query: str = None):
    """Manually trigger a workflow."""
    try:
        payload = {"workflow_id": workflow_id}
        if manual_query:
            payload["manual_query"] = manual_query

        response = requests.post(f"{API_URL}/workflows/{workflow_id}/run", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error running workflow: {e}")
        return None


def delete_workflow(workflow_id: str):
    """Delete a workflow."""
    try:
        response = requests.delete(f"{API_URL}/workflows/{workflow_id}")
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Error deleting workflow: {e}")
        return False


def update_workflow_status(workflow_id: str, active: bool):
    """Update workflow active status."""
    try:
        payload = {"active": active}
        response = requests.put(f"{API_URL}/workflows/{workflow_id}", json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Error updating workflow: {e}")
        return False


def generate_workflow_report(sessions: List[Dict], workflow_name: str):
    """Generate HTML report for workflow sessions."""
    html = f"<html><head><title>Workflow Report: {workflow_name}</title>"
    html += """
    <style>
        body { font-family: sans-serif; margin: 20px; }
        .session { border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 5px; }
        .session-header { background-color: #f5f5f5; padding: 10px; margin: -15px -15px 15px -15px; border-radius: 5px 5px 0 0; }
        .agent-result { border-left: 4px solid; padding: 10px; margin: 10px 0; background-color: #f9f9f9; }
        .error { color: #d32f2f; background-color: #ffebee; }
        h1, h2 { color: #333; }
    </style>
    </head><body>"""
    html += f"<h1>🤖 Workflow Report: {workflow_name}</h1>"
    html += f"<p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
    html += f"<p>Total sessions: {len(sessions)}</p><hr>"

    for session in sessions:
        status_color = "#4CAF50" if session["status"] == "completed" else "#F44336"
        html += f'<div class="session">'
        html += f'<div class="session-header" style="border-left: 4px solid {status_color};">'
        html += f'<h3>Session: {session["started_at"]}</h3>'
        html += f'<p>Status: {session["status"]} | Duration: {session.get("completed_at", "Running...")}</p>'
        html += '</div>'

        for result in session.get("results", []):
            agent_color = AGENT_VISUALS.get(result["agent"], AGENT_VISUALS["default"])["color"]
            html += f'<div class="agent-result" style="border-left-color: {agent_color};">'
            html += f'<strong>{result["agent"]}:</strong><br>{result["result"]}'
            html += '</div>'

        for error in session.get("errors", []):
            html += f'<div class="agent-result error">'
            html += f'<strong>Error in {error["agent"]}:</strong><br>{error["error"]}'
            html += '</div>'

        html += '</div>'

    html += "</body></html>"
    return html


# --- Main Application ---
st.title("🤖 Agent Workflow Engine")
st.markdown("*Automated multi-agent collaboration with scheduling*")

# Check API status
if not check_api_status():
    st.error("❌ FastAPI backend is not running! Please start the backend server first.")
    st.code("cd backend\nuvicorn main:app --reload --port 8000")
    st.stop()
else:
    st.success("✅ Connected to Agent Workflow Engine API")

# --- Sidebar Navigation ---
st.sidebar.title("🗂️ Navigation")
page = st.sidebar.radio(
    "Choose a page:",
    ["🏠 Dashboard", "➕ Create Workflow", "📊 Monitor Sessions", "⚙️ Scheduler Status"],
    index=0
)

# Clear cache button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

# --- Page Content ---
if page == "🏠 Dashboard":
    st.header("📋 Workflow Dashboard")

    # Fetch workflows
    workflows = fetch_workflows()

    if not workflows:
        st.info("ℹ️ No workflows created yet. Use the 'Create Workflow' page to get started!")
    else:
        st.markdown(f"**Active Workflows:** {len([w for w in workflows if w.get('active', True)])}")
        st.markdown("---")

        for workflow in workflows:
            with st.expander(
                    f"{workflow['name']} - {workflow['topic']} "
                    f"({'🟢 Active' if workflow.get('active', True) else '🔴 Inactive'})",
                    expanded=False
            ):
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.write(f"**Agents:** {' → '.join(workflow['agents'])}")
                    st.write(f"**Schedule:** `{workflow['schedule']}`")
                    if workflow.get('last_run'):
                        last_run = datetime.fromisoformat(workflow['last_run']).strftime('%Y-%m-%d %H:%M')
                        st.write(f"**Last Run:** {last_run}")

                with col2:
                    if workflow.get('notification_config'):
                        config = workflow['notification_config']
                        if config.get('email'):
                            st.write(f"📧 Email: {config['email']}")
                        if config.get('slack_webhook'):
                            st.write("💬 Slack: Configured")

                with col3:
                    # Control buttons
                    if st.button(f"▶️ Run Now", key=f"run_{workflow['id']}"):
                        with st.spinner("Starting workflow..."):
                            result = run_workflow_manually(workflow['id'])
                            if result:
                                st.success("✅ Workflow started!")
                                time.sleep(2)
                                st.rerun()

                    current_status = workflow.get('active', True)
                    new_status = not current_status
                    status_label = "⏸️ Pause" if current_status else "▶️ Activate"

                    if st.button(status_label, key=f"toggle_{workflow['id']}"):
                        if update_workflow_status(workflow['id'], new_status):
                            st.success(f"✅ Workflow {'activated' if new_status else 'paused'}!")
                            st.cache_data.clear()
                            st.rerun()

                    if st.button(f"🗑️ Delete", key=f"delete_{workflow['id']}"):
                        if delete_workflow(workflow['id']):
                            st.success("✅ Workflow deleted!")
                            st.cache_data.clear()
                            st.rerun()

elif page == "➕ Create Workflow":
    st.header("🛠️ Create New Workflow")

    with st.form("create_workflow_form"):
        col1, col2 = st.columns([1, 1])

        with col1:
            workflow_name = st.text_input("Workflow Name*", placeholder="e.g., Daily AI Research")
            topic = st.text_input("Topic*", placeholder="e.g., artificial intelligence")

            # Agent selection
            st.subheader("Select Agents (in execution order)")
            available_agents = ["Research", "Summarizer", "Insight", "Devil"]
            selected_agents = []

            for agent in available_agents:
                visuals = AGENT_VISUALS[agent]
                if st.checkbox(f"{visuals['icon']} {agent}", key=f"agent_{agent}"):
                    selected_agents.append(agent)

        with col2:
            # Schedule configuration
            st.subheader("Schedule Configuration")
            schedule_type = st.selectbox("Schedule Preset", list(SCHEDULE_PRESETS.keys()))

            if schedule_type == "Custom":
                cron_expression = st.text_input(
                    "Cron Expression*",
                    placeholder="0 9 * * *",
                    help="Format: minute hour day month day_of_week"
                )
            else:
                cron_expression = SCHEDULE_PRESETS[schedule_type]
                st.code(f"Cron: {cron_expression}")

            # Notification configuration
            st.subheader("Notifications (Optional)")
            enable_email = st.checkbox("Email Notifications")
            email_address = ""
            if enable_email:
                email_address = st.text_input("Email Address", placeholder="user@example.com")

            enable_slack = st.checkbox("Slack Notifications")
            slack_webhook = ""
            if enable_slack:
                slack_webhook = st.text_input("Slack Webhook URL", type="password")

        submitted = st.form_submit_button("🚀 Create Workflow", type="primary")

        if submitted:
            if not workflow_name or not topic or not selected_agents:
                st.error("❌ Please fill in all required fields and select at least one agent.")
            elif schedule_type == "Custom" and not cron_expression:
                st.error("❌ Please provide a cron expression for custom schedule.")
            else:
                # Prepare notification config
                notification_config = {}
                if enable_email and email_address:
                    notification_config["email"] = email_address
                if enable_slack and slack_webhook:
                    notification_config["slack_webhook"] = slack_webhook

                with st.spinner("Creating workflow..."):
                    result = create_workflow(
                        workflow_name,
                        topic,
                        selected_agents,
                        cron_expression,
                        notification_config if notification_config else None
                    )

                    if result:
                        st.success(f"✅ Workflow '{workflow_name}' created successfully!")
                        st.info(f"Workflow ID: `{result['workflow_id']}`")
                        st.cache_data.clear()
                        time.sleep(2)
                        st.rerun()

elif page == "📊 Monitor Sessions":
    st.header("📈 Session Monitoring")

    workflows = fetch_workflows()

    if not workflows:
        st.info("ℹ️ No workflows available to monitor.")
    else:
        # Workflow selector
        workflow_options = {f"{w['name']} ({w['topic']})": w['id'] for w in workflows}
        selected_workflow_name = st.selectbox("Select Workflow to Monitor", list(workflow_options.keys()))

        if selected_workflow_name:
            workflow_id = workflow_options[selected_workflow_name]

            # Fetch sessions
            sessions = fetch_workflow_sessions(workflow_id)

            if not sessions:
                st.info("ℹ️ No execution sessions found for this workflow.")
            else:
                st.markdown(f"**Total Sessions:** {len(sessions)}")

                # Filter options
                col1, col2 = st.columns([1, 1])
                with col1:
                    status_filter = st.selectbox("Filter by Status", ["All", "completed", "running", "failed"])
                with col2:
                    show_results = st.checkbox("Show Detailed Results", value=True)

                # Filter sessions
                filtered_sessions = sessions
                if status_filter != "All":
                    filtered_sessions = [s for s in sessions if s.get("status") == status_filter]

                # Sort by most recent
                filtered_sessions.sort(key=lambda x: x.get("started_at", ""), reverse=True)

                st.markdown("---")

                for session in filtered_sessions:
                    status = session.get("status", "unknown")
                    status_color = {
                        "completed": "🟢",
                        "running": "🟡",
                        "failed": "🔴"
                    }.get(status, "⚪")

                    started_at = datetime.fromisoformat(session["started_at"]).strftime('%Y-%m-%d %H:%M:%S')

                    with st.expander(f"{status_color} Session {started_at} - {status.title()}", expanded=False):
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            st.write(f"**Started:** {started_at}")
                            if session.get("completed_at"):
                                completed_at = datetime.fromisoformat(session["completed_at"]).strftime(
                                    '%Y-%m-%d %H:%M:%S')
                                st.write(f"**Completed:** {completed_at}")

                            if show_results:
                                session_results = fetch_session_results(session["id"])
                                if session_results:
                                    st.markdown("**Results:**")
                                    for result in session_results.get("raw_results", []):
                                        agent_visuals = AGENT_VISUALS.get(result["agent"], AGENT_VISUALS["default"])
                                        st.markdown(f"**{agent_visuals['icon']} {result['agent']}:**")
                                        with st.container():
                                            st.markdown(result["result"])
                                        st.markdown("---")

                                    # Show errors if any
                                    if session_results.get("errors"):
                                        st.markdown("**❌ Errors:**")
                                        for error in session_results["errors"]:
                                            st.error(f"{error['agent']}: {error['error']}")

                        with col2:
                            if PDF_AVAILABLE and show_results:
                                if st.button(f"📄 Export PDF", key=f"export_{session['id']}"):
                                    with st.spinner("Generating PDF..."):
                                        try:
                                            session_data = fetch_session_results(session["id"])
                                            if session_data:
                                                # Create a mini report for this session
                                                report_html = f"<h1>Session Report</h1>"
                                                report_html += f"<p>Session ID: {session['id']}</p>"
                                                report_html += f"<p>Started: {started_at}</p>"
                                                report_html += f"<p>Status: {status}</p><hr>"

                                                for result in session_data.get("raw_results", []):
                                                    report_html += f"<h3>{result['agent']}</h3>"
                                                    report_html += f"<p>{result['result']}</p><hr>"

                                                pdf_bytes = pdfkit.from_string(report_html, False,
                                                                               configuration=config_pdf)

                                                st.download_button(
                                                    "⬇️ Download PDF",
                                                    data=pdf_bytes,
                                                    file_name=f"session_{session['id'][:8]}_{started_at.replace(':', '_')}.pdf",
                                                    mime="application/pdf"
                                                )
                                        except Exception as e:
                                            st.error(f"PDF generation failed: {e}")

elif page == "⚙️ Scheduler Status":
    st.header("⚙️ Scheduler Management")

    # Get scheduler status
    scheduler_status = fetch_scheduler_status()

    if scheduler_status:
        col1, col2 = st.columns([2, 1])

        with col1:
            status_text = "🟢 Running" if scheduler_status.get("scheduler_running") else "🔴 Stopped"
            st.markdown(f"**Scheduler Status:** {status_text}")

            active_jobs = scheduler_status.get("active_jobs", [])
            st.markdown(f"**Active Jobs:** {len(active_jobs)}")

            if active_jobs:
                st.markdown("**Scheduled Jobs:**")
                for job in active_jobs:
                    next_run = "Not scheduled"
                    if job.get("next_run"):
                        try:
                            next_run_dt = datetime.fromisoformat(job["next_run"])
                            next_run = next_run_dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            next_run = job["next_run"]

                    st.markdown(f"• **{job['name']}** - Next run: {next_run}")

        with col2:
            if scheduler_status.get("scheduler_running"):
                if st.button("⏸️ Stop Scheduler"):
                    try:
                        response = requests.post(f"{API_URL}/scheduler/stop")
                        if response.status_code == 200:
                            st.success("✅ Scheduler stopped!")
                            st.cache_data.clear()
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error stopping scheduler: {e}")
            else:
                if st.button("▶️ Start Scheduler"):
                    try:
                        response = requests.post(f"{API_URL}/scheduler/start")
                        if response.status_code == 200:
                            st.success("✅ Scheduler started!")
                            st.cache_data.clear()
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error starting scheduler: {e}")

# --- Footer ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.8em;'>"
    "Agent Workflow Engine | Automated Multi-Agent Collaboration"
    "</div>",
    unsafe_allow_html=True
)