# 🛡️ CarbonCompliance - Endpoint Compliance Monitor

A comprehensive endpoint compliance monitoring system that tracks disk encryption, OS updates, and system security status across your infrastructure.

## 📋 Features

- **Real-time Compliance Monitoring**: Track disk encryption, OS updates, and system security
- **Cross-Platform Support**: Works on macOS, Windows, and Linux
- **Beautiful Dashboard**: Streamlit-based dashboard with real-time charts and metrics
- **RESTful API**: FastAPI backend with comprehensive endpoints
- **Agent-Based Collection**: Lightweight agents that collect and report compliance data
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **SQLite Database**: Lightweight, file-based storage

## 🏗️ Architecture

```
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
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- pip
- Git

### Local Development Setup

1. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd compliance-monitor
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Start the Backend**:
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Start the Dashboard** (in a new terminal):
   ```bash
   cd dashboard
   streamlit run dashboard.py
   ```

4. **Test the Agent**:
   ```bash
   cd agent
   python check_in.py --dry-run  # Test data collection
   python check_in.py            # Submit to API
   ```

### Docker Deployment

1. **Build and Run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

2. **Access the Services**:
   - Dashboard: http://localhost:8501
   - API Documentation: http://localhost:8000/docs
   - API Health Check: http://localhost:8000/health

## 📊 Dashboard Features

- **Real-time Metrics**: Total devices, compliance rate, and device distribution
- **Interactive Charts**: Gauge charts and pie charts for compliance visualization
- **Device Tables**: Detailed view of compliant and non-compliant devices
- **Auto-refresh**: Configurable refresh intervals
- **Responsive Design**: Works on desktop and mobile devices

## 🔧 API Endpoints

### Core Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /report` - Submit compliance report
- `GET /summary` - Get compliance summary
- `GET /reports` - Get recent reports
- `GET /devices` - Get all devices
- `GET /device/{device_id}` - Get device history

### Example API Usage

```bash
# Submit a compliance report
curl -X POST "http://localhost:8000/report" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-123",
    "hostname": "workstation-01",
    "disk_encryption_status": "Encrypted",
    "os_updates_status": "Up to Date",
    "compliance_score": 95.0,
    "is_compliant": true
  }'

# Get compliance summary
curl "http://localhost:8000/summary"
```

## 🤖 Agent Configuration

### Agent Features

- **Automatic Device ID**: Generates and persists unique device identifiers
- **Cross-Platform Checks**: OS-specific compliance checks
- **Secure Data Collection**: Limited process information for security
- **Error Handling**: Graceful failure handling and logging

### Agent Usage

```bash
# Basic usage
python agent/check_in.py

# Custom API URL
python agent/check_in.py --api-url http://your-api-server:8000

# Dry run (collect data without submitting)
python agent/check_in.py --dry-run

# View help
python agent/check_in.py --help
```

### Compliance Checks

The agent performs the following checks:

1. **Disk Encryption**:
   - macOS: FileVault status
   - Windows: BitLocker status
   - Linux: LUKS encryption status

2. **OS Updates**:
   - macOS: Software Update status
   - Windows: Windows Update status
   - Linux: Package manager updates

3. **System Information**:
   - Hostname and device ID
   - Running processes (limited for security)
   - OS version and type

### Compliance Scoring

- **Disk Encryption**: 50% weight
  - Encrypted: 50 points
  - Not Encrypted: 0 points
  - Unknown: 25 points

- **OS Updates**: 50% weight
  - Up to Date: 50 points
  - Updates Available: 25 points
  - Check Required: 25 points
  - Unknown: 25 points

- **Compliance Threshold**: 80% (configurable)

## 🔒 Security Considerations

### Data Security

- **Limited Process Data**: Only collects basic process information
- **Local Device IDs**: Device identifiers stored locally
- **No Sensitive Data**: Avoids collecting passwords or personal information
- **Secure Communication**: HTTPS support for API communication

### Deployment Security

- **Non-root Containers**: Docker containers run as non-root users
- **Network Isolation**: Docker networks for service communication
- **Health Checks**: Built-in health monitoring
- **Resource Limits**: Configurable memory and CPU limits

### Best Practices

1. **Use HTTPS**: Configure SSL certificates for production
2. **API Authentication**: Implement API key or token authentication
3. **Network Security**: Use firewalls and VPNs for remote access
4. **Regular Updates**: Keep dependencies and system packages updated
5. **Monitoring**: Set up logging and alerting for the system

## 🐳 Docker Configuration

### Environment Variables

```bash
# Backend
PYTHONPATH=/app
API_BASE_URL=http://backend:8000

# Dashboard
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Volume Mounts

- `./data:/app/data` - Persistent data storage
- `./backend/reports.db:/app/reports.db` - SQLite database

### Health Checks

Both services include health checks:
- Backend: HTTP health check endpoint
- Dashboard: Process health monitoring

## 📈 Monitoring and Logging

### Log Files

- `agent.log` - Agent execution logs
- `app.log` - Application logs (if configured)

### Metrics

- Compliance rate trends
- Device check-in frequency
- API response times
- Error rates

## 🔧 Troubleshooting

### Common Issues

1. **Port Conflicts**:
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   # Kill process if needed
   kill -9 <PID>
   ```

2. **Database Locked**:
   ```bash
   # Ensure only one process accesses SQLite
   # Check for multiple instances
   ps aux | grep uvicorn
   ```

3. **Agent Permissions**:
   ```bash
   # Run agent with appropriate permissions
   # Some checks may require sudo on Linux
   sudo python agent/check_in.py
   ```

4. **API Connection Issues**:
   ```bash
   # Test API connectivity
   curl http://localhost:8000/health
   ```

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python agent/check_in.py --dry-run
```

## 🚀 Production Deployment

### VM Deployment

1. **Prepare the VM**:
   ```bash
   # Install Docker and Docker Compose
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

2. **Deploy the Application**:
   ```bash
   git clone <repository-url>
   cd compliance-monitor
   docker-compose up -d
   ```

3. **Configure Firewall**:
   ```bash
   sudo ufw allow 8000  # API
   sudo ufw allow 8501  # Dashboard
   ```

### SSL Configuration

1. **Generate Certificates**:
   ```bash
   mkcert localhost 127.0.0.1 ::1
   ```

2. **Configure FastAPI with SSL**:
   ```python
   uvicorn.run(app, ssl_certfile='./localhost.pem', ssl_keyfile='./localhost-key.pem')
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation at `/docs`

---

**Built with ❤️ using FastAPI, Streamlit, and Python** 