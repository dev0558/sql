#!/usr/bin/env python3
"""
NexusHR - Enterprise Human Resources Management System
Employee Directory Search Module
"""

import os
import subprocess
from flask import Flask, render_template_string, request

app = Flask(__name__)

# Database configuration from environment
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'nexushr_admin')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME = os.environ.get('DB_NAME', 'nexushr')


def sanitize_input(user_input):
    """
    Sanitize user input by escaping single quotes.
    Standard SQL injection prevention technique.
    """
    if user_input is None:
        return ''
    # Escape single quotes by doubling them
    return user_input.replace("'", "''")


def execute_query(query_input):
    """
    Execute database query using psql command-line interface.
    This method provides direct access to PostgreSQL's powerful CLI features.
    """
    sanitized = sanitize_input(query_input)

    # Build psql command with the search query
    psql_cmd = (
        f'PGPASSWORD="{DB_PASSWORD}" psql -h {DB_HOST} -U {DB_USER} -d {DB_NAME} '
        f'-t -A -F "," '
        f"-c \"SET standard_conforming_strings=off; SELECT id, name, department, position, email FROM employees WHERE name ILIKE '%{sanitized}%' ORDER BY name\""
    )

    try:
        result = subprocess.run(
            psql_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, 'PGPASSWORD': DB_PASSWORD}
        )

        if result.returncode != 0:
            return None, "Database query failed. Please try again."

        return result.stdout.strip(), None
    except subprocess.TimeoutExpired:
        return None, "Query timeout. Please simplify your search."
    except Exception as e:
        return None, "An error occurred while processing your request."


def execute_department_query():
    """Execute query to get department statistics."""
    psql_cmd = (
        f'PGPASSWORD="{DB_PASSWORD}" psql -h {DB_HOST} -U {DB_USER} -d {DB_NAME} '
        f'-t -A -F "," '
        f'-c "SELECT department, COUNT(*) as count, ROUND(AVG(salary)::numeric, 0) as avg_salary FROM employees GROUP BY department ORDER BY count DESC"'
    )

    try:
        result = subprocess.run(
            psql_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, 'PGPASSWORD': DB_PASSWORD}
        )

        if result.returncode != 0:
            return []

        departments = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split(',')
                if len(parts) >= 3:
                    departments.append({
                        'name': parts[0],
                        'count': parts[1],
                        'avg_salary': f"${int(parts[2]):,}"
                    })
        return departments
    except:
        return []


def parse_results(raw_output):
    """Parse CSV output from psql into structured data."""
    if not raw_output:
        return []

    employees = []
    for line in raw_output.strip().split('\n'):
        if line:
            parts = line.split(',')
            if len(parts) >= 5:
                employees.append({
                    'id': parts[0],
                    'name': parts[1],
                    'department': parts[2],
                    'position': parts[3],
                    'email': parts[4]
                })
    return employees


# Base CSS styles
BASE_STYLES = '''
    :root {
        --primary-50: #eff6ff;
        --primary-100: #dbeafe;
        --primary-200: #bfdbfe;
        --primary-500: #3b82f6;
        --primary-600: #2563eb;
        --primary-700: #1d4ed8;
        --primary-800: #1e40af;
        --primary-900: #1e3a8a;
        --gray-50: #f9fafb;
        --gray-100: #f3f4f6;
        --gray-200: #e5e7eb;
        --gray-300: #d1d5db;
        --gray-400: #9ca3af;
        --gray-500: #6b7280;
        --gray-600: #4b5563;
        --gray-700: #374151;
        --gray-800: #1f2937;
        --gray-900: #111827;
        --success-500: #22c55e;
        --success-100: #dcfce7;
        --warning-500: #f59e0b;
        --warning-100: #fef3c7;
        --danger-500: #ef4444;
        --danger-100: #fee2e2;
    }

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
        background-color: #f1f5f9;
        color: var(--gray-800);
        line-height: 1.5;
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* Header */
    .header {
        background: white;
        border-bottom: 1px solid var(--gray-200);
        position: sticky;
        top: 0;
        z-index: 100;
    }

    .header-inner {
        max-width: 1440px;
        margin: 0 auto;
        padding: 0 2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 64px;
    }

    .logo {
        display: flex;
        align-items: center;
        gap: 10px;
        text-decoration: none;
    }

    .logo-mark {
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-700) 100%);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }

    .logo-mark svg {
        width: 20px;
        height: 20px;
        fill: white;
    }

    .logo-type {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--gray-900);
        letter-spacing: -0.025em;
    }

    .logo-type span {
        color: var(--primary-600);
    }

    .nav {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .nav-link {
        padding: 0.5rem 1rem;
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--gray-600);
        text-decoration: none;
        border-radius: 6px;
        transition: all 0.15s ease;
    }

    .nav-link:hover {
        color: var(--gray-900);
        background: var(--gray-100);
    }

    .nav-link.active {
        color: var(--primary-700);
        background: var(--primary-50);
    }

    .user-menu {
        display: flex;
        align-items: center;
        gap: 12px;
        padding-left: 1.5rem;
        border-left: 1px solid var(--gray-200);
        margin-left: 1rem;
    }

    .user-avatar {
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, var(--primary-500) 0%, #8b5cf6 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        font-size: 0.8rem;
    }

    .user-details {
        display: flex;
        flex-direction: column;
    }

    .user-name {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--gray-900);
    }

    .user-role {
        font-size: 0.75rem;
        color: var(--gray-500);
    }

    /* Main Content */
    .main {
        flex: 1;
        max-width: 1440px;
        margin: 0 auto;
        padding: 2rem;
        width: 100%;
    }

    /* Page Header */
    .page-header {
        margin-bottom: 1.5rem;
    }

    .page-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--gray-900);
        letter-spacing: -0.025em;
    }

    .page-subtitle {
        font-size: 0.875rem;
        color: var(--gray-500);
        margin-top: 0.25rem;
    }

    /* Cards */
    .card {
        background: white;
        border-radius: 12px;
        border: 1px solid var(--gray-200);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }

    .card-header {
        padding: 1rem 1.5rem;
        border-bottom: 1px solid var(--gray-100);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .card-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--gray-900);
    }

    .card-body {
        padding: 1.5rem;
    }

    /* Search Form */
    .search-form {
        display: flex;
        gap: 0.75rem;
    }

    .input-group {
        flex: 1;
        position: relative;
    }

    .input-icon {
        position: absolute;
        left: 14px;
        top: 50%;
        transform: translateY(-50%);
        color: var(--gray-400);
        pointer-events: none;
    }

    .input-icon svg {
        width: 18px;
        height: 18px;
    }

    .form-input {
        width: 100%;
        padding: 0.625rem 1rem 0.625rem 2.75rem;
        font-size: 0.875rem;
        font-family: inherit;
        border: 1px solid var(--gray-300);
        border-radius: 8px;
        background: white;
        color: var(--gray-900);
        transition: all 0.15s ease;
    }

    .form-input:focus {
        outline: none;
        border-color: var(--primary-500);
        box-shadow: 0 0 0 3px var(--primary-100);
    }

    .form-input::placeholder {
        color: var(--gray-400);
    }

    .btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        padding: 0.625rem 1.25rem;
        font-size: 0.875rem;
        font-weight: 500;
        font-family: inherit;
        border-radius: 8px;
        border: none;
        cursor: pointer;
        transition: all 0.15s ease;
        text-decoration: none;
    }

    .btn svg {
        width: 16px;
        height: 16px;
    }

    .btn-primary {
        background: var(--primary-600);
        color: white;
    }

    .btn-primary:hover {
        background: var(--primary-700);
    }

    .btn-secondary {
        background: white;
        color: var(--gray-700);
        border: 1px solid var(--gray-300);
    }

    .btn-secondary:hover {
        background: var(--gray-50);
        border-color: var(--gray-400);
    }

    /* Table */
    .table-container {
        overflow-x: auto;
    }

    .table {
        width: 100%;
        border-collapse: collapse;
    }

    .table th {
        text-align: left;
        padding: 0.75rem 1.5rem;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--gray-500);
        background: var(--gray-50);
        border-bottom: 1px solid var(--gray-200);
    }

    .table td {
        padding: 1rem 1.5rem;
        font-size: 0.875rem;
        color: var(--gray-700);
        border-bottom: 1px solid var(--gray-100);
        vertical-align: middle;
    }

    .table tbody tr:hover {
        background: var(--gray-50);
    }

    .table tbody tr:last-child td {
        border-bottom: none;
    }

    .employee-cell {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .employee-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: var(--primary-100);
        color: var(--primary-700);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.8rem;
        flex-shrink: 0;
    }

    .employee-info {
        display: flex;
        flex-direction: column;
    }

    .employee-name {
        font-weight: 600;
        color: var(--gray-900);
    }

    .employee-id {
        font-size: 0.75rem;
        color: var(--gray-500);
    }

    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.625rem;
        font-size: 0.75rem;
        font-weight: 500;
        border-radius: 9999px;
    }

    .badge-blue {
        background: var(--primary-100);
        color: var(--primary-800);
    }

    .badge-green {
        background: var(--success-100);
        color: #166534;
    }

    .badge-yellow {
        background: var(--warning-100);
        color: #92400e;
    }

    .badge-purple {
        background: #f3e8ff;
        color: #6b21a8;
    }

    .badge-gray {
        background: var(--gray-100);
        color: var(--gray-700);
    }

    .email-link {
        color: var(--primary-600);
        text-decoration: none;
    }

    .email-link:hover {
        text-decoration: underline;
    }

    /* Empty State */
    .empty-state {
        padding: 4rem 2rem;
        text-align: center;
    }

    .empty-icon {
        width: 64px;
        height: 64px;
        margin: 0 auto 1rem;
        background: var(--gray-100);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .empty-icon svg {
        width: 28px;
        height: 28px;
        color: var(--gray-400);
    }

    .empty-title {
        font-size: 0.9375rem;
        font-weight: 600;
        color: var(--gray-900);
        margin-bottom: 0.25rem;
    }

    .empty-text {
        font-size: 0.875rem;
        color: var(--gray-500);
    }

    /* Stats Grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .stat-card {
        background: white;
        border: 1px solid var(--gray-200);
        border-radius: 12px;
        padding: 1.25rem;
        display: flex;
        align-items: flex-start;
        gap: 1rem;
    }

    .stat-icon {
        width: 44px;
        height: 44px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }

    .stat-icon svg {
        width: 22px;
        height: 22px;
    }

    .stat-icon-blue {
        background: var(--primary-100);
        color: var(--primary-600);
    }

    .stat-icon-green {
        background: var(--success-100);
        color: var(--success-500);
    }

    .stat-icon-yellow {
        background: var(--warning-100);
        color: var(--warning-500);
    }

    .stat-icon-purple {
        background: #f3e8ff;
        color: #9333ea;
    }

    .stat-content {
        flex: 1;
    }

    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--gray-900);
        letter-spacing: -0.025em;
    }

    .stat-label {
        font-size: 0.8125rem;
        color: var(--gray-500);
        margin-top: 0.125rem;
    }

    /* Department Cards */
    .dept-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 1rem;
    }

    .dept-card {
        background: white;
        border: 1px solid var(--gray-200);
        border-radius: 12px;
        padding: 1.5rem;
        transition: all 0.15s ease;
    }

    .dept-card:hover {
        border-color: var(--primary-200);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }

    .dept-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
    }

    .dept-name {
        font-size: 1rem;
        font-weight: 600;
        color: var(--gray-900);
    }

    .dept-stats {
        display: flex;
        gap: 1.5rem;
    }

    .dept-stat {
        display: flex;
        flex-direction: column;
    }

    .dept-stat-value {
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--gray-900);
    }

    .dept-stat-label {
        font-size: 0.75rem;
        color: var(--gray-500);
    }

    /* Settings */
    .settings-section {
        margin-bottom: 2rem;
    }

    .settings-section:last-child {
        margin-bottom: 0;
    }

    .settings-title {
        font-size: 0.9375rem;
        font-weight: 600;
        color: var(--gray-900);
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--gray-200);
    }

    .settings-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 0;
        border-bottom: 1px solid var(--gray-100);
    }

    .settings-row:last-child {
        border-bottom: none;
    }

    .settings-info {
        flex: 1;
    }

    .settings-label {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--gray-900);
    }

    .settings-desc {
        font-size: 0.8125rem;
        color: var(--gray-500);
        margin-top: 0.125rem;
    }

    .settings-value {
        font-size: 0.875rem;
        color: var(--gray-600);
        font-family: 'SF Mono', 'Fira Code', monospace;
        background: var(--gray-100);
        padding: 0.375rem 0.75rem;
        border-radius: 6px;
    }

    /* Alert */
    .alert {
        padding: 0.875rem 1rem;
        border-radius: 8px;
        font-size: 0.875rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .alert svg {
        width: 18px;
        height: 18px;
        flex-shrink: 0;
    }

    .alert-error {
        background: var(--danger-100);
        color: #b91c1c;
        border: 1px solid #fecaca;
    }

    .alert-info {
        background: var(--primary-50);
        color: var(--primary-800);
        border: 1px solid var(--primary-200);
    }

    /* Footer */
    .footer {
        background: white;
        border-top: 1px solid var(--gray-200);
        padding: 1rem 2rem;
        margin-top: auto;
    }

    .footer-inner {
        max-width: 1440px;
        margin: 0 auto;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .footer-left {
        display: flex;
        align-items: center;
        gap: 1.5rem;
    }

    .footer-copy {
        font-size: 0.8125rem;
        color: var(--gray-500);
    }

    .footer-links {
        display: flex;
        gap: 1rem;
    }

    .footer-link {
        font-size: 0.8125rem;
        color: var(--gray-500);
        text-decoration: none;
    }

    .footer-link:hover {
        color: var(--gray-700);
    }

    .footer-tech {
        font-size: 0.75rem;
        color: var(--gray-400);
    }

    /* Responsive */
    @media (max-width: 768px) {
        .header-inner {
            padding: 0 1rem;
        }

        .nav {
            display: none;
        }

        .user-menu {
            border: none;
            padding-left: 0;
            margin-left: 0;
        }

        .user-details {
            display: none;
        }

        .main {
            padding: 1rem;
        }

        .search-form {
            flex-direction: column;
        }

        .footer-inner {
            flex-direction: column;
            gap: 0.75rem;
            text-align: center;
        }

        .footer-left {
            flex-direction: column;
            gap: 0.5rem;
        }
    }
'''

# Base HTML template
def get_base_template(title, active_page, content):
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - NexusHR</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>{BASE_STYLES}</style>
</head>
<body>
    <header class="header">
        <div class="header-inner">
            <a href="/" class="logo">
                <div class="logo-mark">
                    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                    </svg>
                </div>
                <span class="logo-type">Nexus<span>HR</span></span>
            </a>

            <nav class="nav">
                <a href="/" class="nav-link {'active' if active_page == 'directory' else ''}">Employee Directory</a>
                <a href="/departments" class="nav-link {'active' if active_page == 'departments' else ''}">Departments</a>
                <a href="/reports" class="nav-link {'active' if active_page == 'reports' else ''}">Reports</a>
                <a href="/settings" class="nav-link {'active' if active_page == 'settings' else ''}">Settings</a>
            </nav>

            <div class="user-menu">
                <div class="user-details">
                    <span class="user-name">Admin User</span>
                    <span class="user-role">HR Manager</span>
                </div>
                <div class="user-avatar">AU</div>
            </div>
        </div>
    </header>

    <main class="main">
        {content}
    </main>

    <footer class="footer">
        <div class="footer-inner">
            <div class="footer-left">
                <span class="footer-copy">2024 NexusHR Enterprise</span>
                <div class="footer-links">
                    <a href="#" class="footer-link">Privacy</a>
                    <a href="#" class="footer-link">Terms</a>
                    <a href="#" class="footer-link">Support</a>
                </div>
            </div>
            <span class="footer-tech">PostgreSQL 16.6 | psql CLI Backend | v2.4.1</span>
        </div>
    </footer>
</body>
</html>
'''


def get_initials(name):
    """Get initials from a name."""
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper()


def get_dept_color(dept):
    """Get badge color class for department."""
    colors = {
        'Engineering': 'badge-blue',
        'Marketing': 'badge-purple',
        'Finance': 'badge-green',
        'Human Resources': 'badge-yellow',
        'Sales': 'badge-green',
        'Legal': 'badge-gray',
        'Operations': 'badge-yellow'
    }
    return colors.get(dept, 'badge-gray')


@app.route('/')
def index():
    """Main employee directory search page."""
    search_query = request.args.get('q', '').strip()
    employees = []
    error = None

    if search_query:
        raw_output, error = execute_query(search_query)
        if raw_output:
            employees = parse_results(raw_output)

    error_html = ''
    if error:
        error_html = f'''
        <div class="alert alert-error">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            {error}
        </div>
        '''

    if employees:
        rows = ''
        for emp in employees:
            initials = get_initials(emp['name'])
            badge_class = get_dept_color(emp['department'])
            rows += f'''
            <tr>
                <td>
                    <div class="employee-cell">
                        <div class="employee-avatar">{initials}</div>
                        <div class="employee-info">
                            <span class="employee-name">{emp['name']}</span>
                            <span class="employee-id">ID: {emp['id']}</span>
                        </div>
                    </div>
                </td>
                <td><span class="badge {badge_class}">{emp['department']}</span></td>
                <td>{emp['position']}</td>
                <td><a href="mailto:{emp['email']}" class="email-link">{emp['email']}</a></td>
            </tr>
            '''

        results_html = f'''
        <div class="table-container">
            <table class="table">
                <thead>
                    <tr>
                        <th>Employee</th>
                        <th>Department</th>
                        <th>Position</th>
                        <th>Email</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        '''
    else:
        if search_query:
            results_html = '''
            <div class="empty-state">
                <div class="empty-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"/>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                    </svg>
                </div>
                <h3 class="empty-title">No results found</h3>
                <p class="empty-text">Try adjusting your search terms or filters.</p>
            </div>
            '''
        else:
            results_html = '''
            <div class="empty-state">
                <div class="empty-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                        <circle cx="9" cy="7" r="4"/>
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                    </svg>
                </div>
                <h3 class="empty-title">Search employees</h3>
                <p class="empty-text">Enter a name or department to find employees.</p>
            </div>
            '''

    content = f'''
    <div class="page-header">
        <h1 class="page-title">Employee Directory</h1>
        <p class="page-subtitle">Search and browse employee records</p>
    </div>

    <div class="card" style="margin-bottom: 1.5rem;">
        <div class="card-body">
            <form method="GET" action="/" class="search-form">
                <div class="input-group">
                    <span class="input-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"/>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                        </svg>
                    </span>
                    <input type="text" name="q" class="form-input" placeholder="Search by name or department..." value="{search_query}" autocomplete="off">
                </div>
                <button type="submit" class="btn btn-primary">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"/>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                    </svg>
                    Search
                </button>
            </form>
        </div>
    </div>

    {error_html}

    <div class="card">
        <div class="card-header">
            <span class="card-title">Results</span>
            <span style="font-size: 0.8125rem; color: var(--gray-500);">{len(employees)} employee(s)</span>
        </div>
        {results_html}
    </div>
    '''

    return get_base_template('Employee Directory', 'directory', content)


@app.route('/departments')
def departments():
    """Department overview page."""
    dept_data = execute_department_query()

    dept_cards = ''
    for dept in dept_data:
        dept_cards += f'''
        <div class="dept-card">
            <div class="dept-header">
                <span class="dept-name">{dept['name']}</span>
            </div>
            <div class="dept-stats">
                <div class="dept-stat">
                    <span class="dept-stat-value">{dept['count']}</span>
                    <span class="dept-stat-label">Employees</span>
                </div>
                <div class="dept-stat">
                    <span class="dept-stat-value">{dept['avg_salary']}</span>
                    <span class="dept-stat-label">Avg. Salary</span>
                </div>
            </div>
        </div>
        '''

    content = f'''
    <div class="page-header">
        <h1 class="page-title">Departments</h1>
        <p class="page-subtitle">Overview of company departments</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-icon stat-icon-blue">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
            </div>
            <div class="stat-content">
                <div class="stat-value">10</div>
                <div class="stat-label">Total Employees</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon stat-icon-purple">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                    <line x1="3" y1="9" x2="21" y2="9"/>
                    <line x1="9" y1="21" x2="9" y2="9"/>
                </svg>
            </div>
            <div class="stat-content">
                <div class="stat-value">{len(dept_data)}</div>
                <div class="stat-label">Departments</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon stat-icon-green">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="12" y1="1" x2="12" y2="23"/>
                    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                </svg>
            </div>
            <div class="stat-content">
                <div class="stat-value">$116,800</div>
                <div class="stat-label">Avg. Salary</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon stat-icon-yellow">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                </svg>
            </div>
            <div class="stat-content">
                <div class="stat-value">+12%</div>
                <div class="stat-label">Growth YoY</div>
            </div>
        </div>
    </div>

    <div class="card">
        <div class="card-header">
            <span class="card-title">All Departments</span>
        </div>
        <div class="card-body">
            <div class="dept-grid">
                {dept_cards}
            </div>
        </div>
    </div>
    '''

    return get_base_template('Departments', 'departments', content)


@app.route('/reports')
def reports():
    """Reports page."""
    content = '''
    <div class="page-header">
        <h1 class="page-title">Reports</h1>
        <p class="page-subtitle">Generate and view HR reports</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-icon stat-icon-blue">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                    <polyline points="10 9 9 9 8 9"/>
                </svg>
            </div>
            <div class="stat-content">
                <div class="stat-value">24</div>
                <div class="stat-label">Reports Generated</div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon stat-icon-green">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                    <line x1="16" y1="2" x2="16" y2="6"/>
                    <line x1="8" y1="2" x2="8" y2="6"/>
                    <line x1="3" y1="10" x2="21" y2="10"/>
                </svg>
            </div>
            <div class="stat-content">
                <div class="stat-value">Q4 2024</div>
                <div class="stat-label">Current Period</div>
            </div>
        </div>
    </div>

    <div class="card">
        <div class="card-header">
            <span class="card-title">Available Reports</span>
            <button class="btn btn-secondary" style="font-size: 0.8125rem; padding: 0.5rem 0.875rem;">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width: 14px; height: 14px;">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                Export All
            </button>
        </div>
        <div class="table-container">
            <table class="table">
                <thead>
                    <tr>
                        <th>Report Name</th>
                        <th>Type</th>
                        <th>Last Generated</th>
                        <th>Status</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="font-weight: 500;">Headcount Summary</td>
                        <td><span class="badge badge-blue">Workforce</span></td>
                        <td>Dec 15, 2024</td>
                        <td><span class="badge badge-green">Ready</span></td>
                        <td><a href="#" class="email-link">Download</a></td>
                    </tr>
                    <tr>
                        <td style="font-weight: 500;">Salary Distribution</td>
                        <td><span class="badge badge-purple">Compensation</span></td>
                        <td>Dec 10, 2024</td>
                        <td><span class="badge badge-green">Ready</span></td>
                        <td><a href="#" class="email-link">Download</a></td>
                    </tr>
                    <tr>
                        <td style="font-weight: 500;">Department Analysis</td>
                        <td><span class="badge badge-blue">Workforce</span></td>
                        <td>Dec 8, 2024</td>
                        <td><span class="badge badge-green">Ready</span></td>
                        <td><a href="#" class="email-link">Download</a></td>
                    </tr>
                    <tr>
                        <td style="font-weight: 500;">Turnover Report</td>
                        <td><span class="badge badge-yellow">Retention</span></td>
                        <td>Dec 1, 2024</td>
                        <td><span class="badge badge-green">Ready</span></td>
                        <td><a href="#" class="email-link">Download</a></td>
                    </tr>
                    <tr>
                        <td style="font-weight: 500;">Benefits Enrollment</td>
                        <td><span class="badge badge-gray">Benefits</span></td>
                        <td>Nov 30, 2024</td>
                        <td><span class="badge badge-green">Ready</span></td>
                        <td><a href="#" class="email-link">Download</a></td>
                    </tr>
                    <tr style="opacity: 0.6;">
                        <td style="font-weight: 500;">HR Confidential Records</td>
                        <td><span class="badge" style="background: var(--danger-100); color: #b91c1c;">Restricted</span></td>
                        <td>Dec 20, 2024</td>
                        <td><span class="badge" style="background: var(--danger-100); color: #b91c1c;">Locked</span></td>
                        <td><span style="color: var(--gray-400); font-size: 0.8125rem;">Access Denied</span></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <div class="alert alert-info" style="margin-top: 1.5rem;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
        Some reports require elevated database privileges. Contact your administrator if you need access to restricted data tables.
    </div>
    '''

    return get_base_template('Reports', 'reports', content)


@app.route('/settings')
def settings():
    """Settings page."""
    content = '''
    <div class="page-header">
        <h1 class="page-title">Settings</h1>
        <p class="page-subtitle">System configuration and preferences</p>
    </div>

    <div class="card">
        <div class="card-body">
            <div class="settings-section">
                <h3 class="settings-title">Database Connection</h3>
                <div class="settings-row">
                    <div class="settings-info">
                        <div class="settings-label">Host</div>
                        <div class="settings-desc">Database server address</div>
                    </div>
                    <span class="settings-value">postgres:5432</span>
                </div>
                <div class="settings-row">
                    <div class="settings-info">
                        <div class="settings-label">Database</div>
                        <div class="settings-desc">Active database name</div>
                    </div>
                    <span class="settings-value">nexushr</span>
                </div>
                <div class="settings-row">
                    <div class="settings-info">
                        <div class="settings-label">Connection Method</div>
                        <div class="settings-desc">Database interface protocol</div>
                    </div>
                    <span class="settings-value">psql CLI</span>
                </div>
            </div>

            <div class="settings-section">
                <h3 class="settings-title">Application</h3>
                <div class="settings-row">
                    <div class="settings-info">
                        <div class="settings-label">Version</div>
                        <div class="settings-desc">Current application version</div>
                    </div>
                    <span class="settings-value">2.4.1</span>
                </div>
                <div class="settings-row">
                    <div class="settings-info">
                        <div class="settings-label">Environment</div>
                        <div class="settings-desc">Deployment environment</div>
                    </div>
                    <span class="settings-value">Production</span>
                </div>
                <div class="settings-row">
                    <div class="settings-info">
                        <div class="settings-label">Query Mode</div>
                        <div class="settings-desc">How queries are executed</div>
                    </div>
                    <span class="settings-value">Shell Subprocess</span>
                </div>
            </div>

            <div class="settings-section">
                <h3 class="settings-title">Security</h3>
                <div class="settings-row">
                    <div class="settings-info">
                        <div class="settings-label">Input Sanitization</div>
                        <div class="settings-desc">Quote escaping for user input</div>
                    </div>
                    <span class="settings-value">Enabled</span>
                </div>
                <div class="settings-row">
                    <div class="settings-info">
                        <div class="settings-label">Session Timeout</div>
                        <div class="settings-desc">Automatic logout after inactivity</div>
                    </div>
                    <span class="settings-value">30 minutes</span>
                </div>
            </div>

            <div class="settings-section">
                <h3 class="settings-title">Database Schema</h3>
                <div class="settings-row">
                    <div class="settings-info">
                        <div class="settings-label">Public Tables</div>
                        <div class="settings-desc">Tables accessible via search interface</div>
                    </div>
                    <span class="settings-value">employees</span>
                </div>
                <div class="settings-row">
                    <div class="settings-info">
                        <div class="settings-label">Restricted Tables</div>
                        <div class="settings-desc">Tables with limited access permissions</div>
                    </div>
                    <span class="settings-value" style="color: #b91c1c;">hr_secrets</span>
                </div>
                <div class="settings-row">
                    <div class="settings-info">
                        <div class="settings-label">Total Records</div>
                        <div class="settings-desc">Combined row count across all tables</div>
                    </div>
                    <span class="settings-value">16</span>
                </div>
            </div>
        </div>
    </div>
    '''

    return get_base_template('Settings', 'settings', content)


@app.route('/health')
def health():
    """Health check endpoint."""
    return {'status': 'healthy', 'service': 'nexushr-web'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
