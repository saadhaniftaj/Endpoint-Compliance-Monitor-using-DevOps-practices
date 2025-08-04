from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import os
from datetime import datetime
import uuid

from db import db_manager
from certificates import check_certificate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Endpoint Compliance Monitor API",
    description="API for monitoring endpoint compliance status",
    version="1.0.0"
)

# Add CORS middleware for dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for production flexibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for the HTML dashboard
try:
    app.mount("/static", StaticFiles(directory="../frontend"), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

# Pydantic models for data validation
class ComplianceReport(BaseModel):
    device_id: str = Field(..., description="Unique device identifier")
    hostname: str = Field(..., description="Device hostname")
    disk_encryption_status: Optional[str] = Field("Unknown", description="Disk encryption status")
    os_updates_status: Optional[str] = Field("Unknown", description="OS updates status")
    running_processes: Optional[str] = Field("", description="List of running processes")
    compliance_score: Optional[float] = Field(0.0, ge=0.0, le=100.0, description="Compliance score (0-100)")
    is_compliant: Optional[bool] = Field(False, description="Overall compliance status")
    details: Optional[str] = Field("", description="Additional compliance details")

class ComplianceSummary(BaseModel):
    total_devices: int
    compliant_devices: int
    compliance_rate: float
    non_compliant_devices: List[Dict[str, Any]]

class EndpointData(BaseModel):
    name: str = Field(..., description="Endpoint name")
    hostname: str = Field(..., description="Endpoint hostname")
    ip_address: str = Field(..., description="IP address")
    type: str = Field(..., description="Endpoint type")
    description: Optional[str] = Field("", description="Optional description")

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    database_connected: bool

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Endpoint Compliance Monitor API",
        "version": "1.0.0",
        "docs": "/docs",
        "dashboard": "/dashboard"
    }

@app.get("/dashboard")
async def serve_dashboard():
    """Serve the HTML dashboard"""
    try:
        dashboard_path = "../frontend/index.html"
        if os.path.exists(dashboard_path):
            return FileResponse(dashboard_path)
        else:
            raise HTTPException(status_code=404, detail="Dashboard not found")
    except Exception as e:
        logger.error(f"Error serving dashboard: {e}")
        raise HTTPException(status_code=500, detail="Error serving dashboard")

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        summary = db_manager.get_compliance_summary()
        db_connected = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_connected = False
    
    return HealthCheck(
        status="healthy" if db_connected else "unhealthy",
        timestamp=datetime.now().isoformat(),
        database_connected=db_connected
    )

@app.post("/report", response_model=Dict[str, str])
async def submit_compliance_report(report: ComplianceReport):
    """Submit a compliance report from an agent"""
    try:
        # Validate and prepare report data
        report_data = report.dict()
        # Add timestamp if not provided
        if 'timestamp' not in report_data:
            report_data['timestamp'] = datetime.now().isoformat()
        # --- Compliance logic for imposed certificates ---
        imposed = db_manager.get_imposed_certificates()
        cert_results = {}
        for cert_id in imposed:
            cert_results[cert_id] = check_certificate(cert_id, report_data)
        report_data['details'] = str(cert_results)
        # Insert report into database
        success = db_manager.insert_compliance_report(report_data)
        if success:
            logger.info(f"Compliance report received for device {report.device_id}")
            return {
                "status": "success",
                "message": f"Compliance report submitted for device {report.device_id}",
                "device_id": report.device_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to store compliance report")
    except Exception as e:
        logger.error(f"Error processing compliance report: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/summary", response_model=ComplianceSummary)
async def get_compliance_summary():
    """Get overall compliance summary"""
    try:
        summary = db_manager.get_compliance_summary()
        return ComplianceSummary(**summary)
    except Exception as e:
        logger.error(f"Error getting compliance summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve compliance summary")

@app.get("/reports", response_model=List[Dict[str, Any]])
async def get_recent_reports(limit: int = 50):
    """Get recent compliance reports"""
    try:
        if limit > 100:  # Prevent excessive data retrieval
            limit = 100
        reports = db_manager.get_recent_reports(limit)
        return reports
    except Exception as e:
        logger.error(f"Error getting recent reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reports")

@app.get("/device/{device_id}", response_model=List[Dict[str, Any]])
async def get_device_history(device_id: str):
    """Get compliance history for a specific device"""
    try:
        history = db_manager.get_device_history(device_id)
        if not history:
            raise HTTPException(status_code=404, detail="Device not found")
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve device history")

@app.get("/devices", response_model=List[Dict[str, Any]])
async def get_all_devices():
    """Get list of all devices"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT device_id, hostname, first_seen, last_seen, total_reports
                FROM devices 
                ORDER BY last_seen DESC
            """)
            devices = [dict(row) for row in cursor.fetchall()]
            return devices
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve devices")

# New endpoints for the dashboard
@app.get("/api/compliance/summary")
async def get_compliance_summary_api():
    """Get compliance summary for dashboard"""
    try:
        summary = db_manager.get_compliance_summary()
        # Transform data for dashboard
        return {
            "total_endpoints": summary.get("total_devices", 0),
            "compliant_count": summary.get("compliant_devices", 0),
            "non_compliant_count": summary.get("total_devices", 0) - summary.get("compliant_devices", 0),
            "average_score": summary.get("compliance_rate", 0) * 100
        }
    except Exception as e:
        logger.error(f"Error fetching compliance summary: {e}")
        return {
            "total_endpoints": 0,
            "compliant_count": 0,
            "non_compliant_count": 0,
            "average_score": 0
        }

@app.get("/api/compliance/reports")
async def get_compliance_reports_api(limit: int = 10):
    """Get recent compliance reports for dashboard"""
    try:
        reports = db_manager.get_recent_reports(limit)
        return reports
    except Exception as e:
        logger.error(f"Error fetching compliance reports: {e}")
        return []

@app.post("/api/endpoints")
async def add_endpoint(endpoint: EndpointData):
    """Add a new endpoint to the system"""
    try:
        # For now, we'll just return success since we don't have an endpoints table
        # In a real implementation, you'd save this to a database
        logger.info(f"Adding endpoint: {endpoint.name} ({endpoint.hostname})")
        return {"message": "Endpoint added successfully", "endpoint": endpoint.dict()}
    except Exception as e:
        logger.error(f"Error adding endpoint: {e}")
        raise HTTPException(status_code=500, detail="Error adding endpoint")

@app.get("/api/certificates")
async def get_imposed_certificates():
    """Get all currently imposed compliance certificates"""
    try:
        imposed = db_manager.get_imposed_certificates()
        return {"imposed": imposed}
    except Exception as e:
        logger.error(f"Error fetching imposed certificates: {e}")
        raise HTTPException(status_code=500, detail="Error fetching imposed certificates")

@app.post("/api/certificates/{cert_id}")
async def impose_certificate(cert_id: str):
    """Impose a compliance certificate by ID"""
    try:
        success = db_manager.impose_certificate(cert_id)
        if success:
            return {"status": "success", "cert_id": cert_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to impose certificate")
    except Exception as e:
        logger.error(f"Error imposing certificate: {e}")
        raise HTTPException(status_code=500, detail="Error imposing certificate")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 