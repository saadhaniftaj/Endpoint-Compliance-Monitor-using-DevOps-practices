# 🛡️ Endpoint Compliance Monitor

A comprehensive endpoint compliance monitoring system that tracks disk encryption, OS updates, and system security status across your infrastructure in real time. Developed as a final project for a DevOps internship, this system leverages modern DevOps practices to ensure scalability, security, and maintainability.

## 📋 Features

- **Real-time Compliance Monitoring**: Tracks disk encryption, OS updates, and system security.
- **Cross-Platform Support**: Compatible with macOS, Windows, and Linux.
- **Beautiful Dashboard**: Streamlit-based interface with real-time charts and metrics.
- **RESTful API**: FastAPI backend with comprehensive endpoints for data interaction.
- **Agent-Based Collection**: Lightweight agents for secure compliance data collection.
- **Docker Support**: Easy deployment with Docker and Docker Compose.
- **SQLite Database**: Lightweight, file-based storage for efficient data management.

## 🏗️ Architecture

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

1. **Agents**: Collect compliance data and send it to the backend.
2. **Backend**: Processes data, stores it in SQLite, and serves metrics.
3. **Dashboard**: Displays compliance status with interactive visuals.

## Workflow

1. **Data Collection**: Agents check disk encryption (FileVault, BitLocker, LUKS) and OS updates, calculating scores (50% encryption, 50% updates).
2. **Data Submission**: Agents send data to the FastAPI backend via REST API.
3. **Processing**: Backend stores reports and computes metrics.
4. **Visualization**: Streamlit dashboard shows compliance rates, device details, and charts.

## DevOps Practices

Built with best DevOps practices:
- **Containerization**: Docker for consistent deployments.
- **Security**: Non-root containers, HTTPS support, minimal data collection.
- **Automation**: CI/CD pipelines for integration and deployment.
- **Monitoring**: Health checks, logging, and metrics for compliance and performance.
- **Scalability**: Modular design with SQLite for efficient scaling.

## Compliance Checks

- **Disk Encryption**: Verifies FileVault (macOS), BitLocker (Windows), LUKS (Linux).
- **OS Updates**: Checks update status via OS-specific tools.
- **Scoring**: 80% compliance threshold (configurable).

## Deployment

- **Docker**: Run `docker-compose up -d` for setup.
- **Configuration**: Set environment variables for API and dashboard.
- **Storage**: Persist data via Docker volumes.

## Monitoring & Security

- **Logs**: Agent and app logs for debugging.
- **Metrics**: Tracks compliance trends and API performance.
- **Security**: HTTPS, network isolation, limited data collection.

## Contributing

1. Fork the repo.
2. Create a feature branch.
3. Submit a pull request with changes.

## License

MIT License. See LICENSE file for details.

---

**Built with FastAPI, Streamlit, Python, and DevOps best practices**
