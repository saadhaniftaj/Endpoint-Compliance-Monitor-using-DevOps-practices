🛡️ Endpoint Compliance Monitor
A comprehensive endpoint compliance monitoring system that tracks disk encryption, OS updates, and system security status across your infrastructure in real time. Developed as a final project for a DevOps internship, this system leverages modern DevOps practices to ensure scalability, security, and maintainability.
📋 Features

Real-time Compliance Monitoring: Tracks disk encryption, OS updates, and system security.
Cross-Platform Support: Compatible with macOS, Windows, and Linux.
Beautiful Dashboard: Streamlit-based interface with real-time charts and metrics.
RESTful API: FastAPI backend with comprehensive endpoints for data interaction.
Agent-Based Collection: Lightweight agents for secure compliance data collection.
Docker Support: Easy deployment with Docker and Docker Compose.
SQLite Database: Lightweight, file-based storage for efficient data management.

🏗️ Architecture
The system follows a modular architecture:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Agent Script  │    │   FastAPI       │    │   Streamlit     │
│   (check_in.py) │───▶│   Backend       │◀───│   Dashboard     │
│                 │    │   (main.py)     │    │   (dashboard.py)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   SQLite        │
                       │   Database      │
                       │   (reports.db)  │
                       └─────────────────┘


Agents: Collect compliance data (disk encryption, OS updates, system info) and send it to the backend.
Backend: Processes data via FastAPI, stores it in SQLite, and serves metrics to the dashboard.
Dashboard: Visualizes compliance status with interactive charts and tables.

🚀 Workflow

Data Collection: Lightweight agents perform OS-specific checks (e.g., FileVault on macOS, BitLocker on Windows, LUKS on Linux) and calculate compliance scores based on disk encryption (50% weight) and OS updates (50% weight).
Data Submission: Agents securely transmit data to the FastAPI backend using RESTful endpoints.
Data Processing: The backend stores reports in a SQLite database and computes compliance metrics.
Visualization: The Streamlit dashboard displays real-time metrics, including compliance rates, device distribution, and detailed device tables, with auto-refresh and responsive design.

🔒 Development and DevOps Practices
Built as a DevOps internship final project, this system adheres to best DevOps practices:

Containerization: Uses Docker and Docker Compose for consistent, isolated deployments.
Security: Runs non-root containers, supports HTTPS, and limits data collection to essential metrics.
Automation: CI/CD pipelines ensure seamless integration and deployment.
Monitoring: Includes health checks, logging (agent.log, app.log), and metrics for compliance trends and API performance.
Scalability: Modular design and lightweight SQLite database enable easy scaling.
Maintainability: Comprehensive error handling, debug logging, and clear documentation.

🔧 Compliance Checks

Disk Encryption: Checks FileVault (macOS), BitLocker (Windows), or LUKS (Linux).
OS Updates: Verifies update status via OS-specific tools (e.g., Windows Update, Linux package managers).
System Information: Collects hostname, device ID, and limited process data.
Scoring: Compliance score = 50% (encryption) + 50% (updates), with a configurable 80% threshold.

🐳 Deployment
The system is designed for easy deployment:

Docker: Use docker-compose up -d for quick setup.
Environment Variables: Configure API base URL, Streamlit port, and database paths.
Volumes: Persist data and SQLite database via mounted volumes.

📈 Monitoring and Security

Logging: Agent and application logs for troubleshooting.
Metrics: Tracks compliance rates, device check-ins, and API response times.
Security: HTTPS support, network isolation, and minimal data collection to protect privacy.

🤝 Contributing

Fork the repository.
Create a feature branch.
Make changes and add tests if applicable.
Submit a pull request.

📄 License
Licensed under the MIT License. See the LICENSE file for details.

Built with ❤️ using FastAPI, Streamlit, Python, and DevOps best practices
