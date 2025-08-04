import platform
import subprocess
import re
import os

def check_disk_encryption():
    try:
        if platform.system() == 'Darwin':
            out = subprocess.check_output(['fdesetup', 'status']).decode()
            return 'On' in out or 'FileVault is On' in out
        elif platform.system() == 'Linux':
            # Check for LUKS encrypted root
            out = subprocess.check_output(['lsblk', '-o', 'NAME,TYPE,MOUNTPOINT']).decode()
            return any('crypt' in line for line in out.splitlines())
        else:
            return None
    except Exception:
        return None

def check_os_updates():
    try:
        if platform.system() == 'Darwin':
            out = subprocess.check_output(['softwareupdate', '-l']).decode()
            return 'No new software available' in out
        elif platform.system() == 'Linux':
            # Try apt
            try:
                out = subprocess.check_output(['apt', 'list', '--upgradable']).decode()
                return len([l for l in out.splitlines() if '/' in l and 'upgradable' in l]) == 0
            except Exception:
                # Try yum
                out = subprocess.check_output(['yum', 'check-update']).decode()
                return out.strip() == ''
        else:
            return None
    except Exception:
        return None

def check_access_control():
    try:
        if platform.system() == 'Darwin':
            out = subprocess.check_output(['dscl', '.', '-read', '/Groups/admin', 'GroupMembership']).decode()
            users = out.split(':')[-1].strip().split()
            return len(users) <= 2  # root + 1 admin
        elif platform.system() == 'Linux':
            out = subprocess.check_output(['getent', 'group', 'sudo']).decode()
            users = out.split(':')[-1].strip().split(',')
            return len([u for u in users if u]) <= 2
        else:
            return None
    except Exception:
        return None

def check_firewall():
    try:
        if platform.system() == 'Darwin':
            out = subprocess.check_output(['/usr/libexec/ApplicationFirewall/socketfilterfw', '--getglobalstate']).decode()
            return 'enabled' in out.lower()
        elif platform.system() == 'Linux':
            out = subprocess.check_output(['ufw', 'status']).decode()
            return 'active' in out.lower()
        else:
            return None
    except Exception:
        return None

def check_auto_updates():
    try:
        if platform.system() == 'Darwin':
            out = subprocess.check_output(['defaults', 'read', '/Library/Preferences/com.apple.SoftwareUpdate', 'AutomaticCheckEnabled']).decode().strip()
            return out == '1'
        elif platform.system() == 'Linux':
            out = subprocess.check_output(['systemctl', 'is-enabled', 'unattended-upgrades']).decode().strip()
            return out == 'enabled'
        else:
            return None
    except Exception:
        return None

def check_password_policy():
    try:
        if platform.system() == 'Darwin':
            out = subprocess.check_output(['pwpolicy', 'getaccountpolicies'], stderr=subprocess.STDOUT).decode()
            minlen = re.search(r'minLength\s*=\s*"?(\d+)"?', out)
            minlen = int(minlen.group(1)) if minlen else 0
            return minlen >= 8
        elif platform.system() == 'Linux':
            with open('/etc/login.defs') as f:
                content = f.read()
            minlen = re.search(r'PASS_MIN_LEN\s+(\d+)', content)
            minlen = int(minlen.group(1)) if minlen else 0
            return minlen >= 8
        else:
            return None
    except Exception:
        return None

def check_logging():
    try:
        if platform.system() == 'Linux':
            out = subprocess.check_output(['systemctl', 'is-active', 'rsyslog']).decode().strip()
            return out == 'active'
        elif platform.system() == 'Darwin':
            # macOS uses syslogd
            out = subprocess.check_output(['pgrep', 'syslogd']).decode().strip()
            return bool(out)
        else:
            return None
    except Exception:
        return None

def check_uptime():
    try:
        out = subprocess.check_output(['uptime', '-p']).decode().strip()
        return out
    except Exception:
        return None

def check_auditd():
    try:
        if platform.system() == 'Linux':
            out = subprocess.check_output(['systemctl', 'is-active', 'auditd']).decode().strip()
            return out == 'active'
        elif platform.system() == 'Darwin':
            # macOS auditd is always running
            out = subprocess.check_output(['pgrep', 'auditd']).decode().strip()
            return bool(out)
        else:
            return None
    except Exception:
        return None

def check_antivirus():
    try:
        out = subprocess.check_output(['ps', 'aux']).decode()
        return any(av in out for av in ['clamd', 'avast', 'sophos', 'mcafee', 'symantec', 'bitdefender'])
    except Exception:
        return None

def check_screen_lock():
    try:
        if platform.system() == 'Darwin':
            out = subprocess.check_output(['defaults', 'read', 'com.apple.screensaver', 'askForPassword']).decode().strip()
            return out == '1'
        elif platform.system() == 'Linux':
            # Try gsettings for GNOME
            out = subprocess.check_output(['gsettings', 'get', 'org.gnome.desktop.screensaver', 'lock-enabled']).decode().strip()
            return out == 'true'
        else:
            return None
    except Exception:
        return None

def check_fips_mode():
    try:
        if os.path.exists('/proc/sys/crypto/fips_enabled'):
            with open('/proc/sys/crypto/fips_enabled') as f:
                return f.read().strip() == '1'
        elif platform.system() == 'Linux':
            out = subprocess.check_output(['sysctl', 'crypto.fips_enabled']).decode()
            return '1' in out
        else:
            return None
    except Exception:
        return None

def check_large_home_dirs():
    try:
        out = subprocess.check_output(['du', '-sh', '/home/*']).decode()
        # If any home dir > 10G, flag as not minimized
        for line in out.splitlines():
            size = line.split()[0]
            if size.endswith('G') and float(size[:-1]) > 10:
                return False
        return True
    except Exception:
        return None

def check_cis_benchmarks(report_data):
    results = {}
    results['password_min_length'] = check_password_policy()
    results['firewall_enabled'] = check_firewall()
    results['auto_updates_enabled'] = check_auto_updates()
    return results

def check_iso27001(report_data):
    results = {}
    results['disk_encryption'] = check_disk_encryption()
    results['os_updates'] = check_os_updates()
    results['access_control'] = check_access_control()
    return results

def check_soc2(report_data):
    results = {}
    results['logging_enabled'] = check_logging()
    results['availability'] = check_uptime()
    return results

def check_hipaa(report_data):
    results = {}
    results['disk_encryption'] = check_disk_encryption()
    results['audit_logs'] = check_auditd()
    return results

def check_pci_dss(report_data):
    results = {}
    results['disk_encryption'] = check_disk_encryption()
    results['firewall_enabled'] = check_firewall()
    results['antivirus_installed'] = check_antivirus()
    return results

def check_nist_800_53(report_data):
    results = {}
    results['os_updates'] = check_os_updates()
    results['access_control'] = check_access_control()
    results['screen_lock'] = check_screen_lock()
    return results

def check_gdpr(report_data):
    results = {}
    results['disk_encryption'] = check_disk_encryption()
    results['data_minimization'] = check_large_home_dirs()
    return results

def check_fedramp(report_data):
    results = {}
    results['disk_encryption'] = check_disk_encryption()
    results['os_updates'] = check_os_updates()
    results['fips_mode'] = check_fips_mode()
    return results

def check_certificate(cert_id, report_data):
    if cert_id == 'cis':
        return check_cis_benchmarks(report_data)
    if cert_id == 'iso27001':
        return check_iso27001(report_data)
    if cert_id == 'soc2':
        return check_soc2(report_data)
    if cert_id == 'hipaa':
        return check_hipaa(report_data)
    if cert_id == 'pci':
        return check_pci_dss(report_data)
    if cert_id == 'nist':
        return check_nist_800_53(report_data)
    if cert_id == 'gdpr':
        return check_gdpr(report_data)
    if cert_id == 'fedramp':
        return check_fedramp(report_data)
    return {}