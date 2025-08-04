// CarbonSync Endpoint Compliance Monitor Dashboard JavaScript

class ComplianceDashboard {
    constructor() {
        this.apiUrl = 'http://localhost:8000';
        this.autoRefreshInterval = null;
        this.charts = {};
        this.lastUpdate = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadApiUrlFromStorage();
        this.initParticleAnimation();
        this.refreshData();
        this.startAutoRefresh();
        this.updateLastUpdated();
    }

    setupEventListeners() {
        // Auto refresh toggle
        document.getElementById('auto-refresh').addEventListener('change', (e) => {
            if (e.target.checked) {
                this.startAutoRefresh();
            } else {
                this.stopAutoRefresh();
            }
        });

        // API URL input
        document.getElementById('api-url').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.updateApiUrl();
            }
        });

        // Modal close events
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target.id);
            }
        });
    }

    initParticleAnimation() {
        const bg = document.getElementById('bgParticles');
        const totalParticles = 120;
        
        for (let i = 0; i < totalParticles; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle ' + (Math.random() > 0.5 ? 'green' : 'yellow');
            particle.style.left = Math.random() * 100 + 'vw';
            particle.style.bottom = Math.random() * 100 + 'vh';
            particle.style.animationDelay = (Math.random() * -12) + 's';
            particle.style.animationDuration = (10 + Math.random() * 8) + 's';
            bg.appendChild(particle);
        }
    }

    loadApiUrlFromStorage() {
        const savedUrl = localStorage.getItem('compliance-api-url');
        if (savedUrl) {
            this.apiUrl = savedUrl;
            document.getElementById('api-url').value = savedUrl;
        }
    }

    updateApiUrl() {
        const newUrl = document.getElementById('api-url').value.trim();
        if (newUrl) {
            this.apiUrl = newUrl;
            localStorage.setItem('compliance-api-url', newUrl);
            this.refreshData();
            this.showNotification('API URL updated successfully', 'success');
        }
    }

    async fetchApiData(endpoint) {
        try {
            const response = await fetch(`${this.apiUrl}${endpoint}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                timeout: 10000
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`Error fetching ${endpoint}:`, error);
            throw error;
        }
    }

    async refreshData() {
        try {
            this.showLoading(true);
            
            // Fetch all data in parallel
            const [summary, recentReports, devices] = await Promise.all([
                this.fetchApiData('/summary'),
                this.fetchApiData('/reports?limit=20'),
                this.fetchApiData('/devices')
            ]);

            this.updateMetrics(summary);
            this.updateCharts(summary);
            this.updateNonCompliantTable(summary.non_compliant_devices);
            this.updateRecentReportsTable(recentReports);
            this.updateDevicesTable(devices);
            this.updateLastUpdated();

            this.showLoading(false);
        } catch (error) {
            this.showLoading(false);
            this.showNotification('Failed to load data. Please check the API URL and try again.', 'error');
            console.error('Error refreshing data:', error);
        }
    }

    updateMetrics(summary) {
        document.getElementById('total-devices').textContent = summary.total_devices;
        document.getElementById('compliant-devices').textContent = summary.compliant_devices;
        document.getElementById('non-compliant-devices').textContent = 
            summary.total_devices - summary.compliant_devices;
        document.getElementById('compliance-rate').textContent = `${summary.compliance_rate}%`;
    }

    updateCharts(summary) {
        this.updateComplianceGauge(summary.compliance_rate);
        this.updateDeviceDistribution(summary);
    }

    updateComplianceGauge(complianceRate) {
        const ctx = document.getElementById('complianceGauge');
        
        if (this.charts.complianceGauge) {
            this.charts.complianceGauge.destroy();
        }

        this.charts.complianceGauge = new Chart(ctx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [complianceRate, 100 - complianceRate],
                    backgroundColor: [
                        this.getComplianceColor(complianceRate),
                        '#333'
                    ],
                    borderWidth: 0,
                    cutout: '70%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false
                    }
                },
                elements: {
                    arc: {
                        borderWidth: 0
                    }
                }
            }
        });

        // Add center text
        const centerText = {
            id: 'centerText',
            afterDatasetsDraw(chart) {
                const { ctx, chartArea: { left, right, top, bottom, width, height } } = chart;
                ctx.save();
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.font = 'bold 24px Inter';
                ctx.fillStyle = '#ffe066';
                ctx.fillText(`${complianceRate}%`, left + width / 2, top + height / 2);
                ctx.font = '14px Inter';
                ctx.fillStyle = '#b3b3b3';
                ctx.fillText('Compliance', left + width / 2, top + height / 2 + 25);
                ctx.restore();
            }
        };

        this.charts.complianceGauge.options.plugins.centerText = centerText;
    }

    updateDeviceDistribution(summary) {
        const ctx = document.getElementById('deviceDistribution');
        
        if (this.charts.deviceDistribution) {
            this.charts.deviceDistribution.destroy();
        }

        const compliantCount = summary.compliant_devices;
        const nonCompliantCount = summary.total_devices - summary.compliant_devices;

        this.charts.deviceDistribution = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['Compliant', 'Non-Compliant'],
                datasets: [{
                    data: [compliantCount, nonCompliantCount],
                    backgroundColor: ['#1db954', '#e74a3b'],
                    borderWidth: 2,
                    borderColor: '#232323'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            color: '#fff',
                            font: {
                                family: 'Inter'
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: '#232323',
                        titleColor: '#1db954',
                        bodyColor: '#fff',
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    updateNonCompliantTable(nonCompliantDevices) {
        const tbody = document.getElementById('non-compliant-tbody');
        
        if (!nonCompliantDevices || nonCompliantDevices.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center" style="color: #1db954;">🎉 All devices are compliant!</td></tr>';
            return;
        }

        tbody.innerHTML = nonCompliantDevices.map(device => `
            <tr class="fade-in">
                <td><strong>${device.hostname}</strong></td>
                <td>
                    <div class="progress">
                        <div class="progress-bar bg-danger" style="width: ${device.compliance_score}%">
                            ${device.compliance_score}%
                        </div>
                    </div>
                </td>
                <td>${this.formatTimestamp(device.timestamp)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-info" onclick="showDeviceDetails('${device.device_id}')">
                        <i class="fas fa-info-circle"></i> Details
                    </button>
                </td>
            </tr>
        `).join('');
    }

    updateRecentReportsTable(reports) {
        const tbody = document.getElementById('recent-reports-tbody');
        
        if (!reports || reports.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">No recent reports available.</td></tr>';
            return;
        }

        tbody.innerHTML = reports.map(report => `
            <tr class="fade-in">
                <td><strong>${report.hostname}</strong></td>
                <td>
                    <div class="progress">
                        <div class="progress-bar ${report.is_compliant ? 'bg-success' : 'bg-danger'}" 
                             style="width: ${report.compliance_score}%">
                            ${report.compliance_score}%
                        </div>
                    </div>
                </td>
                <td>
                    <span class="badge ${report.is_compliant ? 'badge-compliant' : 'badge-non-compliant'}">
                        ${report.is_compliant ? '✅ Compliant' : '❌ Non-Compliant'}
                    </span>
                </td>
                <td>${this.formatTimestamp(report.timestamp)}</td>
            </tr>
        `).join('');
    }

    updateDevicesTable(devices) {
        const tbody = document.getElementById('devices-tbody');
        const section = document.getElementById('device-details-section');
        
        if (!devices || devices.length === 0) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';
        tbody.innerHTML = devices.map(device => `
            <tr class="fade-in">
                <td><strong>${device.hostname}</strong></td>
                <td>${device.total_reports}</td>
                <td>${this.formatTimestamp(device.last_seen)}</td>
            </tr>
        `).join('');
    }

    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString();
    }

    getComplianceColor(rate) {
        if (rate >= 90) return '#1db954'; // Green
        if (rate >= 70) return '#ffe066'; // Yellow
        return '#e74a3b'; // Red
    }

    showLoading(show) {
        const modal = document.getElementById('loadingModal');
        if (show) {
            modal.classList.add('active');
        } else {
            modal.classList.remove('active');
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            color: #fff;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            animation: slideIn 0.3s ease;
        `;
        
        // Set background color based on type
        switch(type) {
            case 'success':
                notification.style.background = '#1db954';
                break;
            case 'error':
                notification.style.background = '#e74a3b';
                break;
            case 'warning':
                notification.style.background = '#ffe066';
                notification.style.color = '#191414';
                break;
            default:
                notification.style.background = '#36b9cc';
        }
        
        notification.innerHTML = `
            ${message}
            <button onclick="this.parentElement.remove()" style="
                background: none;
                border: none;
                color: inherit;
                font-size: 1.2rem;
                cursor: pointer;
                margin-left: 1rem;
                opacity: 0.7;
            ">&times;</button>
        `;

        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }

    updateLastUpdated() {
        this.lastUpdate = new Date();
    }

    startAutoRefresh() {
        this.stopAutoRefresh();
        this.autoRefreshInterval = setInterval(() => {
            this.refreshData();
        }, 60000); // 60 seconds
    }

    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
        }
    }
}

// Global functions for HTML onclick handlers
function updateApiUrl() {
    dashboard.updateApiUrl();
}

function refreshData() {
    dashboard.refreshData();
}

async function showDeviceDetails(deviceId) {
    try {
        const response = await fetch(`${dashboard.apiUrl}/device/${deviceId}`);
        const history = await response.json();
        
        if (history.length > 0) {
            const device = history[0];
            const details = JSON.parse(device.details || '{}');
            
            const modal = document.getElementById('deviceModal');
            const title = document.getElementById('deviceModalTitle');
            const content = document.getElementById('deviceModalContent');
            
            title.textContent = `Device Details: ${device.hostname}`;
            
            content.innerHTML = `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 2rem;">
                    <div>
                        <h4 style="color: #1db954; margin-bottom: 1rem;">System Information</h4>
                        <p><strong>OS Type:</strong> ${details.os_type || 'Unknown'}</p>
                        <p><strong>OS Version:</strong> ${details.os_version || 'Unknown'}</p>
                        <p><strong>Device ID:</strong> ${device.device_id}</p>
                    </div>
                    <div>
                        <h4 style="color: #1db954; margin-bottom: 1rem;">Compliance Status</h4>
                        <p><strong>Disk Encryption:</strong> ${device.disk_encryption_status}</p>
                        <p><strong>OS Updates:</strong> ${device.os_updates_status}</p>
                        <p><strong>Compliance Score:</strong> ${device.compliance_score}%</p>
                    </div>
                </div>
                <hr style="border: 1px solid #333; margin: 2rem 0;">
                <h4 style="color: #1db954; margin-bottom: 1rem;">Compliance History</h4>
                <div style="max-height: 300px; overflow-y: auto;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #191414;">
                                <th style="padding: 0.5rem; text-align: left; color: #1db954;">Date</th>
                                <th style="padding: 0.5rem; text-align: left; color: #1db954;">Score</th>
                                <th style="padding: 0.5rem; text-align: left; color: #1db954;">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${history.slice(0, 10).map(h => `
                                <tr style="border-bottom: 1px solid #333;">
                                    <td style="padding: 0.5rem;">${dashboard.formatTimestamp(h.timestamp)}</td>
                                    <td style="padding: 0.5rem;">${h.compliance_score}%</td>
                                    <td style="padding: 0.5rem;">
                                        <span class="badge ${h.is_compliant ? 'badge-compliant' : 'badge-non-compliant'}">
                                            ${h.is_compliant ? 'Compliant' : 'Non-Compliant'}
                                        </span>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
            
            modal.classList.add('active');
        }
    } catch (error) {
        dashboard.showNotification('Failed to load device details', 'error');
    }
}

function closeDeviceModal() {
    dashboard.closeModal('deviceModal');
}

// Initialize dashboard when DOM is loaded
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new ComplianceDashboard();
});

// Handle page visibility changes for better performance
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        dashboard.stopAutoRefresh();
    } else {
        if (document.getElementById('auto-refresh').checked) {
            dashboard.startAutoRefresh();
        }
    }
});

// Add CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style); 