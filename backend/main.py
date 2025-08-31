import os
import sys
from datetime import datetime
from typing import List, Dict, Optional

# Add the current directory to Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit

from agents import devil_agent, insight_agent, research_agent, summarizer_agent
from agents.base import (
    log_agent_response, get_topic_log, create_workflow, get_workflow,
    get_all_workflows, update_workflow, delete_workflow, create_workflow_session,
    update_session_status, add_session_result, get_session, get_workflow_sessions,
    notify_workflow_completion, format_workflow_results
)

app = FastAPI(title="Agent Workflow Engine API")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Shutdown scheduler when app stops
atexit.register(lambda: scheduler.shutdown())


# ---------- Request Models ----------
class CreateWorkflowRequest(BaseModel):
    name: str
    topic: str
    agents: List[str]  # e.g., ["Research", "Summarizer", "Insight"]
    schedule: str  # cron expression, e.g., "0 9 * * *" for daily at 9 AM
    notification_config: Optional[Dict] = None


class UpdateWorkflowRequest(BaseModel):
    name: Optional[str] = None
    topic: Optional[str] = None
    agents: Optional[List[str]] = None
    schedule: Optional[str] = None
    notification_config: Optional[Dict] = None
    active: Optional[bool] = None


class RunWorkflowRequest(BaseModel):
    workflow_id: str
    manual_query: Optional[str] = None  # Optional query for research agent


# ---------- Workflow Execution Logic ----------
def execute_workflow(workflow_id: str, manual_query: str = None):
    """Execute a workflow by running its agents in sequence."""
    workflow = get_workflow(workflow_id)
    if not workflow:
        print(f"Workflow {workflow_id} not found")
        return

    if not workflow.get("active", True):
        print(f"Workflow {workflow_id} is inactive")
        return

    # Create new session
    session_id = create_workflow_session(workflow_id)
    topic = workflow["topic"]

    print(f"Starting workflow '{workflow['name']}' for topic '{topic}' (Session: {session_id})")

    try:
        # Execute agents in sequence
        previous_output = None

        for agent_name in workflow["agents"]:
            try:
                print(f"Running {agent_name} agent...")

                if agent_name == "Devil":
                    output = devil_agent.run(topic)
                elif agent_name == "Insight":
                    if previous_output:
                        # Use previous agent's output as context
                        output = insight_agent.run(f"{topic}. Previous analysis: {previous_output}")
                    else:
                        output = insight_agent.run(topic)
                elif agent_name == "Research":
                    query = manual_query or f"latest developments in {topic}"
                    output = research_agent.run(topic, query)
                elif agent_name == "Summarizer":
                    if previous_output:
                        output = summarizer_agent.run(f"{topic}. Content to summarize: {previous_output}")
                    else:
                        output = summarizer_agent.run(topic)
                else:
                    raise ValueError(f"Unknown agent: {agent_name}")

                # Log the response
                log_agent_response(topic, agent_name, output, session_id)
                add_session_result(session_id, agent_name, output)

                # Use this output as input for next agent
                previous_output = output

            except Exception as e:
                error_msg = f"Error running {agent_name}: {str(e)}"
                print(error_msg)
                add_session_result(session_id, agent_name, None, error_msg)

        # Mark session as completed
        update_session_status(session_id, "completed", datetime.utcnow().isoformat())

        # Update workflow last run time
        update_workflow(workflow_id, {"last_run": datetime.utcnow().isoformat()})

        # Send notifications
        session = get_session(session_id)
        notify_workflow_completion(workflow, session)

        print(f"Workflow '{workflow['name']}' completed successfully")

    except Exception as e:
        error_msg = f"Workflow execution failed: {str(e)}"
        print(error_msg)
        update_session_status(session_id, "failed", datetime.utcnow().isoformat())


def schedule_workflow(workflow_id: str):
    """Schedule a workflow using its cron expression."""
    workflow = get_workflow(workflow_id)
    if not workflow:
        return False

    try:
        # Remove existing job if it exists
        try:
            scheduler.remove_job(workflow_id)
        except:
            pass  # Job doesn't exist yet

        # Add new scheduled job
        scheduler.add_job(
            execute_workflow,
            CronTrigger.from_crontab(workflow["schedule"]),
            args=[workflow_id],
            id=workflow_id,
            name=f"Workflow: {workflow['name']}"
        )

        return True
    except Exception as e:
        print(f"Failed to schedule workflow {workflow_id}: {e}")
        return False


def unschedule_workflow(workflow_id: str):
    """Remove a workflow from the scheduler."""
    try:
        scheduler.remove_job(workflow_id)
        return True
    except:
        return False


# ---------- Routes ----------
@app.get("/")
def root():
    return {"message": "Agent Workflow Engine API is running 🤖⚙️"}


@app.post("/workflows")
def create_workflow_endpoint(request: CreateWorkflowRequest):
    """Create a new workflow."""
    try:
        # Validate agents
        valid_agents = ["Devil", "Insight", "Research", "Summarizer"]
        for agent in request.agents:
            if agent not in valid_agents:
                raise HTTPException(status_code=400, detail=f"Invalid agent: {agent}")

        # Create workflow
        workflow_id = create_workflow(
            request.name,
            request.topic,
            request.agents,
            request.schedule,
            request.notification_config
        )

        # Schedule the workflow
        if schedule_workflow(workflow_id):
            return {
                "workflow_id": workflow_id,
                "message": f"Workflow '{request.name}' created and scheduled successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to schedule workflow")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating workflow: {str(e)}")


@app.get("/workflows")
def list_workflows():
    """List all workflows."""
    try:
        workflows = get_all_workflows()
        return {"workflows": workflows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving workflows: {str(e)}")


@app.get("/workflows/{workflow_id}")
def get_workflow_endpoint(workflow_id: str):
    """Get a specific workflow."""
    workflow = get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@app.put("/workflows/{workflow_id}")
def update_workflow_endpoint(workflow_id: str, request: UpdateWorkflowRequest):
    """Update a workflow."""
    workflow = get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        # Prepare updates
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.topic is not None:
            updates["topic"] = request.topic
        if request.agents is not None:
            # Validate agents
            valid_agents = ["Devil", "Insight", "Research", "Summarizer"]
            for agent in request.agents:
                if agent not in valid_agents:
                    raise HTTPException(status_code=400, detail=f"Invalid agent: {agent}")
            updates["agents"] = request.agents
        if request.schedule is not None:
            updates["schedule"] = request.schedule
        if request.notification_config is not None:
            updates["notification_config"] = request.notification_config
        if request.active is not None:
            updates["active"] = request.active

        # Update workflow
        if update_workflow(workflow_id, updates):
            # Reschedule if schedule or active status changed
            if "schedule" in updates or "active" in updates:
                unschedule_workflow(workflow_id)
                if updates.get("active", workflow.get("active", True)):
                    schedule_workflow(workflow_id)

            return {"message": "Workflow updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update workflow")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating workflow: {str(e)}")


@app.delete("/workflows/{workflow_id}")
def delete_workflow_endpoint(workflow_id: str):
    """Delete a workflow."""
    workflow = get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        # Remove from scheduler
        unschedule_workflow(workflow_id)

        # Delete from database
        if delete_workflow(workflow_id):
            return {"message": "Workflow deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete workflow")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting workflow: {str(e)}")


@app.post("/workflows/{workflow_id}/run")
def run_workflow_manually(workflow_id: str, request: RunWorkflowRequest,
                          background_tasks: BackgroundTasks):
    """Manually trigger a workflow execution."""
    workflow = get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Run workflow in background
    background_tasks.add_task(execute_workflow, workflow_id, request.manual_query)

    return {"message": f"Workflow '{workflow['name']}' started manually"}


@app.get("/workflows/{workflow_id}/sessions")
def get_workflow_sessions_endpoint(workflow_id: str):
    """Get all sessions for a workflow."""
    workflow = get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        sessions = get_workflow_sessions(workflow_id)
        return {"workflow_id": workflow_id, "sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving sessions: {str(e)}")


@app.get("/sessions/{session_id}")
def get_session_endpoint(session_id: str):
    """Get session details."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.get("/sessions/{session_id}/results")
def get_session_results(session_id: str):
    """Get formatted results for a session."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        formatted_results = format_workflow_results(session)
        return {
            "session_id": session_id,
            "formatted_results": formatted_results,
            "raw_results": session.get("results", []),
            "errors": session.get("errors", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error formatting results: {str(e)}")


@app.get("/logs/{topic}")
def get_logs(topic: str, session_id: Optional[str] = None):
    """Retrieve logs for a topic, optionally filtered by session."""
    try:
        logs = get_topic_log(topic, session_id)
        if not logs:
            raise HTTPException(status_code=404, detail="No logs found")
        return {"topic": topic, "session_id": session_id, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")


@app.get("/scheduler/status")
def get_scheduler_status():
    """Get scheduler status and active jobs."""
    try:
        jobs = []
        for job in scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })

        return {
            "scheduler_running": scheduler.running,
            "active_jobs": jobs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting scheduler status: {str(e)}")


@app.post("/scheduler/start")
def start_scheduler():
    """Start the scheduler (if stopped)."""
    try:
        if not scheduler.running:
            scheduler.start()
        return {"message": "Scheduler started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting scheduler: {str(e)}")


@app.post("/scheduler/stop")
def stop_scheduler():
    """Stop the scheduler."""
    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
        return {"message": "Scheduler stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping scheduler: {str(e)}")


# Load existing workflows into scheduler on startup
@app.on_event("startup")
def load_workflows():
    """Load existing workflows into scheduler on startup."""
    try:
        workflows = get_all_workflows()
        scheduled_count = 0

        for workflow in workflows:
            if workflow.get("active", True):
                if schedule_workflow(workflow["id"]):
                    scheduled_count += 1

        print(f"Loaded {scheduled_count} workflows into scheduler")
    except Exception as e:
        print(f"Error loading workflows: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)