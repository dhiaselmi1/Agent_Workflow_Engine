# 🤖 Agent Workflow Engine

## Automated Multi-Agent Collaboration System with Intelligent Scheduling

A powerful workflow automation platform that orchestrates multiple AI agents to work together on scheduled tasks. Create sophisticated agent pipelines that run automatically - perfect for daily briefings, research monitoring, content generation, and business intelligence.

![Agent Workflow Engine UI](https://via.placeholder.com/800x200)
![Agent Workflow Engine Dashboard](https://via.placeholder.com/800x200)
![Agent Workflow Engine Monitoring](https://via.placeholder.com/800x200)
![Agent Workflow Engine Results](https://via.placeholder.com/800x200)

---

## 🌟 Features

### 🔄 Intelligent Agent Orchestration
- **Multi-Agent Workflows**: Chain together Research, Summarizer, Insight, and Devil agents.
- **Sequential Processing**: Each agent builds upon the previous agent's output.
- **Error Handling**: Graceful failure management without breaking the entire workflow.

### ⏰ Advanced Scheduling
- **Cron-based Scheduling**: Flexible timing with standard cron expressions.
- **Background Execution**: Workflows run automatically without user intervention.
- **Manual Triggers**: Run workflows on-demand for immediate results.

### 📊 Comprehensive Monitoring
- **Session Tracking**: Every workflow run is tracked with unique sessions.
- **Real-time Status**: Monitor running, completed, and failed executions.
- **Detailed Logging**: Complete audit trail of all agent interactions.

### 🔔 Smart Notifications
- **Email Alerts**: Get notified when workflows complete via SMTP.
- **Slack Integration**: Send results directly to Slack channels.
- **Customizable Content**: Rich notification templates with a results summary.

### 🎛️ Intuitive Dashboard
- **Web-based Interface**: Beautiful Streamlit dashboard for workflow management.
- **Visual Agent Indicators**: Color-coded agents with intuitive icons.
- **Export Capabilities**: Generate PDF reports of workflow results.

---

## 🏗️ Architecture

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │    FastAPI      │    │     Agents      │
│   Dashboard     │◄──►│   Workflow      │◄──►│   Research      │
│                 │    │   Engine        │    │   Summarizer    │
│  • Create       │    │                 │    │   Insight       │
│  • Monitor      │    │  • Scheduling   │    │   Devil         │
│  • Manage       │    │  • Execution    │    │                 │
└─────────────────┘    │  • Notifications│    └─────────────────┘
                       └─────────────────┘
                                │
                       ┌─────────────────┐
                       │    TinyDB       │
                       │   Database      │
                       │                 │
                       │  • Workflows    │
                       │  • Sessions     │
                       │  • Logs         │
                       └─────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Local LLM server (Ollama with `llama3` model)

### Installation
1. Clone the repository:
   ```bash
   git clone [https://github.com/yourusername/agent-workflow-engine.git](https://github.com/yourusername/agent-workflow-engine.git)
   cd agent-workflow-engine
   ```
2. Install dependencies:
   ```bash
   pip install fastapi uvicorn streamlit tinydb apscheduler pdfkit requests
   ```
3. Set up your LLM server:
   ```bash
   # Install Ollama
   curl -fsSL [https://ollama.ai/install.sh](https://ollama.ai/install.sh) | sh

   # Pull the llama3 model
   ollama pull llama3

   # Start Ollama server
   ollama serve
   ```
4. Start the backend:
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```
5. Launch the dashboard:
   ```bash
   cd frontend
   streamlit run app.py
   ```

### Access the application
- **Dashboard**: `http://localhost:8501`
- **API Documentation**: `http://localhost:8000/docs`

---

## 📋 Usage Examples

### Create a Daily Research Workflow
1. Navigate to "Create Workflow".
2. Configure your workflow:
    - **Name**: Daily AI Research
    - **Topic**: artificial intelligence
    - **Agents**: Research → Summarizer → Insight
    - **Schedule**: Daily at 9 AM
    - **Email**: your-email@example.com
3. Click "Create Workflow".

### Example Workflow Configurations

📈 **Market Intelligence Pipeline**
```json
{
  "name": "Market Intelligence",
  "topic": "cryptocurrency market trends",
  "agents": ["Research", "Summarizer", "Devil", "Insight"],
  "schedule": "0 8,16 * * 1-5",
  "notifications": "email + slack"
}
```

🔬 **Research Monitoring**
```json
{
  "name": "Weekly Research Digest",
  "topic": "machine learning breakthroughs",
  "agents": ["Research", "Summarizer"],
  "schedule": "0 9 * * 0",
  "notifications": "email"
}
```

💼 **Business Intelligence**
```json
{
  "name": "Competitive Analysis",
  "topic": "SaaS industry developments",
  "agents": ["Research", "Devil", "Insight"],
  "schedule": "0 7 1 * *",
  "notifications": "slack"
}
```

---

## 🎯 Agent Roles

| Agent      | Icon | Purpose                                  | Output                        |
| :--------- | :--: | :--------------------------------------- | :---------------------------- |
| **Research** |  🔬  | Gathers latest information and data      | Raw research findings         |
| **Summarizer**|  📝  | Condenses complex information            | Clean, digestible summaries   |
| **Insight** |  💡  | Generates analysis and recommendations   | Strategic insights            |
| **Devil** |  😈  | Provides contrarian perspective          | Critical analysis & challenges|

---

## 📅 Schedule Examples

| Schedule           | Cron Expression   | Description                  |
| :----------------- | :---------------- | :--------------------------- |
| Daily at 9 AM      | `0 9 * * *`       | Every day at 9:00 AM         |
| Weekdays at 8:30 AM| `30 8 * * 1-5`    | Monday-Friday at 8:30 AM     |
| Every 6 hours      | `0 */6 * * *`     | 4 times per day              |
| Weekly on Sunday   | `0 9 * * 0`       | Every Sunday at 9:00 AM      |
| Monthly report     | `0 9 1 * *`       | First day of every month     |
| Twice daily        | `0 9,17 * * *`    | 9 AM and 5 PM daily          |

---

## 📡 API Reference

### Workflow Management
```http
POST   /workflows              # Create new workflow
GET    /workflows              # List all workflows
GET    /workflows/{id}         # Get workflow details
PUT    /workflows/{id}         # Update workflow
DELETE /workflows/{id}         # Delete workflow
```

### Execution & Monitoring
```http
POST   /workflows/{id}/run     # Manually trigger workflow
GET    /workflows/{id}/sessions # Get execution history
GET    /sessions/{id}          # Get session details
GET    /sessions/{id}/results  # Get formatted results
```

### Scheduler Control
```http
GET    /scheduler/status       # Check scheduler status
POST   /scheduler/start        # Start scheduler
POST   /scheduler/stop         # Stop scheduler
```

---

## ⚙️ Configuration

### Environment Variables
```bash
# Email notifications (optional)
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# LLM Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

### Notification Setup
- **Email (Gmail)**
  1. Enable 2-factor authentication.
  2. Generate an app password.
  3. Set environment variables.
- **Slack**
  1. Create a Slack app.
  2. Enable incoming webhooks.
  3. Copy the webhook URL to your workflow configuration.

---

## 📁 Project Structure

```
agent-workflow-engine/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── agents/
│   │   ├── base.py          # Core functions & database
│   │   ├── research_agent.py
│   │   ├── summarizer_agent.py
│   │   ├── insight_agent.py
│   │   └── devil_agent.py
│   └── memory/
│       └── memory_store.json # TinyDB database
├── frontend/
│   └── app.py               # Streamlit dashboard
├── requirements.txt
└── README.md
```

---

## 🛠️ Development

### Adding New Agents
1. Create your agent file in `backend/agents/`.
2. Implement the `run(topic, query=None)` method.
3. Add the agent to the `valid_agents` list in `main.py`.
4. Update the `AGENT_VISUALS` dictionary in the frontend `app.py`.

### Custom Notification Channels
Extend the `notify_workflow_completion()` function in `base.py` to add new services like:
- Discord webhooks
- Microsoft Teams
- SMS notifications
- Custom webhooks

---

## 🚨 Troubleshooting

### Common Issues
- **"Failed to connect to API"**
  - Ensure the FastAPI backend is running on port 8000.
  - Check that the Ollama server is running.
- **"No workflows found"**
  - Create your first workflow using the dashboard.
  - Verify the database file has write permissions.
- **"Scheduler not running"**
  - Check the scheduler status in the dashboard.
  - Restart the backend server.
- **"PDF export not available"**
  - Install `wkhtmltopdf`: https://wkhtmltopdf.org/downloads.html
  - Ensure it's in your system PATH.

### Debug Mode
Start the backend with debug logging for more detailed output:
```bash
uvicorn main:app --reload --port 8000 --log-level debug
```

---

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add amazing feature'`).
4. Push to the branch (`git push origin feature/amazing-feature`).
5. Open a Pull Request.

---

## 📄 License
This project is licensed under the MIT License - see the `LICENSE` file for details.

---

## 🙏 Acknowledgments
- Built with **FastAPI** for robust API development.
- Powered by **Streamlit** for beautiful web interfaces.
- Scheduled with **APScheduler** for reliable automation.
- Data persistence via **TinyDB** for simplicity.

---

## 💡 Use Cases
- 📊 **Daily Business Intelligence**: Automated market research and competitive analysis.
- 📰 **News Monitoring**: Track industry developments and generate briefings.
- 🔍 **Research Automation**: Continuous literature review and insight generation.
- 📈 **Investment Research**: Regular analysis of financial markets and trends.
- 🎯 **Content Strategy**: Automated content research and ideation pipelines.
- 🚨 **Trend Detection**: Early warning systems for industry changes.

Ready to automate your agent workflows? **Get started in minutes!** 🚀
