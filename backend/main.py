from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import os
from datetime import datetime, timedelta
import uuid
import secrets
from jose import JWTError, jwt
from passlib.context import CryptContext

# from db import db_manager
# from certificates import check_certificate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Authentication configuration
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_urlsafe(64))  # Increased to 64 bytes
ALGORITHM = "HS256"  # Using HMAC-SHA256 (secure algorithm)
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Reduced to 15 minutes for better security
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing with stronger settings
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Increased rounds for better security
)

# Security
security = HTTPBearer(auto_error=True)

# Default admin credentials (should be changed in production)
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "CarboncompliancEdev//v1"

# Store for active sessions and blacklisted tokens (in production, use Redis)
active_sessions = {}
blacklisted_tokens = set()

# Rate limiting for login attempts
login_attempts = {}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 300  # 5 minutes

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

class DeviceRegistration(BaseModel):
    device_id: str = Field(..., description="Unique device identifier")
    hostname: str = Field(..., description="Device hostname")
    ip_address: str = Field(..., description="IP address")
    platform: str = Field(..., description="Operating system platform")
    platform_version: str = Field(..., description="Platform version")
    architecture: str = Field(..., description="System architecture")
    first_seen: bool = Field(True, description="Whether this is the first time seeing this device")
    compliance_metrics: Optional[Dict[str, Any]] = Field(None, description="Initial compliance metrics")

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    database_connected: bool

class UserLogin(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    refresh_expires_in: int

class RefreshToken(BaseModel):
    refresh_token: str

class User(BaseModel):
    username: str
    is_active: bool = True
    roles: List[str] = ["admin"]
    permissions: List[str] = ["read", "write", "admin"]

class TokenPayload(BaseModel):
    sub: str
    exp: int
    iat: int
    jti: str  # JWT ID for token uniqueness
    roles: List[str]
    permissions: List[str]

# Authentication functions with enhanced security
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password with strong settings"""
    return pwd_context.hash(password)

def check_rate_limit(username: str) -> bool:
    """Check if user is rate limited"""
    now = datetime.utcnow()
    if username in login_attempts:
        attempts, last_attempt = login_attempts[username]
        if now - last_attempt < timedelta(seconds=LOCKOUT_DURATION):
            if attempts >= MAX_LOGIN_ATTEMPTS:
                return False
    return True

def record_login_attempt(username: str, success: bool):
    """Record login attempt for rate limiting"""
    now = datetime.utcnow()
    if username in login_attempts:
        attempts, last_attempt = login_attempts[username]
        if now - last_attempt < timedelta(seconds=LOCKOUT_DURATION):
            if success:
                login_attempts[username] = (0, now)
            else:
                login_attempts[username] = (attempts + 1, now)
        else:
            login_attempts[username] = (1 if not success else 0, now)
    else:
        login_attempts[username] = (1 if not success else 0, now)

def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user with rate limiting"""
    # Check rate limiting
    if not check_rate_limit(username):
        record_login_attempt(username, False)
        return None
    
    # Validate input
    if not username or not password:
        record_login_attempt(username, False)
        return None
    
    # Check credentials
    if username == DEFAULT_ADMIN_USERNAME and verify_password(password, get_password_hash(DEFAULT_ADMIN_PASSWORD)):
        record_login_attempt(username, True)
        return User(username=username)
    
    record_login_attempt(username, False)
    return None

def create_token_pair(data: dict, expires_delta: timedelta = None, refresh_expires_delta: timedelta = None):
    """Create JWT access and refresh tokens with enhanced security"""
    to_encode = data.copy()
    jti = secrets.token_urlsafe(32)  # Unique token ID
    
    # Access token
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token_data = {
        **to_encode,
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": jti,
        "type": "access"
    }
    
    # Refresh token
    if refresh_expires_delta:
        refresh_expire = datetime.utcnow() + refresh_expires_delta
    else:
        refresh_expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    refresh_token_data = {
        "sub": data.get("sub"),
        "exp": refresh_expire,
        "iat": datetime.utcnow(),
        "jti": jti,
        "type": "refresh"
    }
    
    # Encode tokens with secure algorithm
    access_token = jwt.encode(access_token_data, SECRET_KEY, algorithm=ALGORITHM)
    refresh_token = jwt.encode(refresh_token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    return access_token, refresh_token, jti

def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted"""
    return token in blacklisted_tokens

def blacklist_token(token: str):
    """Add token to blacklist"""
    blacklisted_tokens.add(token)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user with enhanced security"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode token with explicit algorithm specification
        payload = jwt.decode(
            credentials.credentials, 
            SECRET_KEY, 
            algorithms=[ALGORITHM],
            options={"verify_signature": True}
        )
        
        # Validate token structure
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        jti: str = payload.get("jti")
        
        if not username or not token_type or not jti:
            raise credentials_exception
        
        # Check if token is blacklisted
        if is_token_blacklisted(credentials.credentials):
            raise credentials_exception
        
        # Validate token type
        if token_type != "access":
            raise credentials_exception
        
        # Create user with roles and permissions
        user = User(
            username=username,
            roles=payload.get("roles", ["admin"]),
            permissions=payload.get("permissions", ["read", "write", "admin"])
        )
        
        if not user.is_active:
            raise credentials_exception
            
        return user
        
    except JWTError as e:
        logger.error(f"JWT validation error: {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise credentials_exception

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint - redirect to login"""
    return {
        "message": "Endpoint Compliance Monitor API",
        "version": "1.0.0",
        "docs": "/docs",
        "login": "/login",
        "dashboard": "/dashboard"
    }

@app.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Secure login endpoint with rate limiting and enhanced security"""
    try:
        # Input validation
        if not user_credentials.username or not user_credentials.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and password are required"
            )
        
        # Check rate limiting
        if not check_rate_limit(user_credentials.username):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many login attempts. Try again in {LOCKOUT_DURATION} seconds"
            )
        
        # Authenticate user
        user = authenticate_user(user_credentials.username, user_credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create secure token pair
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token, refresh_token, jti = create_token_pair(
            data={
                "sub": user.username,
                "roles": user.roles,
                "permissions": user.permissions
            },
            expires_delta=access_token_expires,
            refresh_expires_delta=refresh_token_expires
        )
        
        # Store session securely
        session_id = secrets.token_urlsafe(32)
        active_sessions[session_id] = {
            "username": user.username,
            "jti": jti,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "created": datetime.utcnow(),
            "access_expires": datetime.utcnow() + access_token_expires,
            "refresh_expires": datetime.utcnow() + refresh_token_expires
        }
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_expires_in": REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/refresh", response_model=Token)
async def refresh_token(refresh_token_data: RefreshToken):
    """Refresh access token using refresh token"""
    try:
        # Decode refresh token
        payload = jwt.decode(
            refresh_token_data.refresh_token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_signature": True}
        )
        
        # Validate refresh token
        token_type = payload.get("type")
        jti = payload.get("jti")
        username = payload.get("sub")
        
        if token_type != "refresh" or not jti or not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if refresh token is blacklisted
        if is_token_blacklisted(refresh_token_data.refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        # Create new token pair
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token, new_refresh_token, new_jti = create_token_pair(
            data={
                "sub": username,
                "roles": payload.get("roles", ["admin"]),
                "permissions": payload.get("permissions", ["read", "write", "admin"])
            },
            expires_delta=access_token_expires,
            refresh_expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        # Blacklist old refresh token
        blacklist_token(refresh_token_data.refresh_token)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_expires_in": REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        }
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/logout")
async def logout(current_user: User = Depends(get_current_user), credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Secure logout endpoint that blacklists tokens"""
    try:
        # Blacklist the current token
        blacklist_token(credentials.credentials)
        
        # Clean up session
        for session_id, session_data in list(active_sessions.items()):
            if session_data.get("username") == current_user.username:
                del active_sessions[session_id]
        
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/auth/check")
async def check_auth(current_user: User = Depends(get_current_user)):
    """Check if user is authenticated with enhanced security"""
    return {
        "authenticated": True,
        "username": current_user.username,
        "roles": current_user.roles,
        "permissions": current_user.permissions
    }

@app.get("/auth/security-info")
async def get_security_info():
    """Get security information for the frontend"""
    return {
        "token_expiry_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
        "refresh_token_expiry_days": REFRESH_TOKEN_EXPIRE_DAYS,
        "max_login_attempts": MAX_LOGIN_ATTEMPTS,
        "lockout_duration_seconds": LOCKOUT_DURATION,
        "algorithm": ALGORITHM
    }

@app.get("/login")
async def serve_login():
    """Serve the login page"""
    try:
        login_path = "../frontend/login.html"
        if os.path.exists(login_path):
            return FileResponse(login_path)
        else:
            raise HTTPException(status_code=404, detail="Login page not found")
    except Exception as e:
        logger.error(f"Error serving login page: {e}")
        raise HTTPException(status_code=500, detail="Error serving login page")

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

@app.get("/download-agent")
async def serve_download_page():
    """Serve the agent download page"""
    try:
        download_path = "../frontend/download.html"
        if os.path.exists(download_path):
            return FileResponse(download_path)
        else:
            raise HTTPException(status_code=404, detail="Download page not found")
    except Exception as e:
        logger.error(f"Error serving download page: {e}")
        raise HTTPException(status_code=500, detail="Error serving download page")

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

@app.post("/api/register-device")
async def register_device(device: DeviceRegistration):
    """Register a new device with the dashboard"""
    try:
        # Log device registration with compliance metrics
        if device.compliance_metrics:
            compliance_score = device.compliance_metrics.get('compliance_score', 0)
            is_compliant = device.compliance_metrics.get('is_compliant', False)
            logger.info(f"Registered device: {device.device_id} ({device.hostname}) - {device.platform} {device.platform_version} - Compliance Score: {compliance_score:.1f}% - Compliant: {is_compliant}")
        else:
            logger.info(f"Registered device: {device.device_id} ({device.hostname}) - {device.platform} {device.platform_version}")
        
        # In a real implementation, this would save to a database
        # For now, we'll just return success
        return {
            "message": "Device registered successfully",
            "device_id": device.device_id,
            "hostname": device.hostname,
            "status": "active",
            "compliance_metrics": device.compliance_metrics
        }
    except Exception as e:
        logger.error(f"Error registering device: {e}")
        raise HTTPException(status_code=500, detail="Failed to register device")

# In-memory storage for imposed certificates (in production, use database)
imposed_certificates = set()

@app.get("/api/certificates")
async def get_imposed_certificates():
    """Get all currently imposed compliance certificates"""
    try:
        return {"imposed": list(imposed_certificates)}
    except Exception as e:
        logger.error(f"Error fetching imposed certificates: {e}")
        raise HTTPException(status_code=500, detail="Error fetching imposed certificates")

@app.post("/api/certificates/{cert_id}")
async def impose_certificate(cert_id: str):
    """Impose a compliance certificate by ID"""
    try:
        imposed_certificates.add(cert_id)
        logger.info(f"Certificate {cert_id} imposed successfully")
        return {"status": "success", "cert_id": cert_id, "action": "imposed"}
    except Exception as e:
        logger.error(f"Error imposing certificate: {e}")
        raise HTTPException(status_code=500, detail="Error imposing certificate")

@app.delete("/api/certificates/{cert_id}")
async def unimpose_certificate(cert_id: str):
    """Unimpose a compliance certificate by ID"""
    try:
        imposed_certificates.discard(cert_id)
        logger.info(f"Certificate {cert_id} unimposed successfully")
        return {"status": "success", "cert_id": cert_id, "action": "unimposed"}
    except Exception as e:
        logger.error(f"Error unimpressing certificate: {e}")
        raise HTTPException(status_code=500, detail="Error unimpressing certificate")

@app.get("/api/download/{os_type}")
async def get_download_info(os_type: str):
    """Get download information for agent binaries"""
    download_info = {
        "macos": {
            "binary_name": "carboncompliance-agent-macos",
            "download_url": "http://localhost:8000/downloads/carboncompliance-agent-macos",
            "instructions": "chmod +x carboncompliance-agent-macos && ./carboncompliance-agent-macos --api-url=http://localhost:8000"
        },
        "linux": {
            "binary_name": "carboncompliance-agent-linux", 
            "download_url": "http://localhost:8000/downloads/carboncompliance-agent-linux",
            "instructions": "chmod +x carboncompliance-agent-linux && ./carboncompliance-agent-linux --api-url=http://localhost:8000"
        },
        "windows": {
            "binary_name": "carboncompliance-agent-windows.exe",
            "download_url": "http://localhost:8000/downloads/carboncompliance-agent-windows.exe", 
            "instructions": ".\\carboncompliance-agent-windows.exe --api-url=http://localhost:8000"
        }
    }
    
    if os_type not in download_info:
        raise HTTPException(status_code=400, detail="Unsupported OS type")
    
    return download_info[os_type]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 