#!/usr/bin/env python3
"""
NexusHR - Enterprise Human Resources Management System
Employee Directory Search Module
"""

import os
import subprocess
import re
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
        f"-c \"SELECT id, name, department, position, email FROM employees WHERE name ILIKE '%{sanitized}%' OR department ILIKE '%{sanitized}%' ORDER BY name\""
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


# Base CSS styles shared across all pages
BASE_STYLES = '''
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    --primary: #6366f1;
    --primary-dark: #4f46e5;
    --secondary: #0ea5e9;
    --accent: #f59e0b;
    --bg-dark: #0f172a;
    --bg-darker: #020617;
    --bg-card: #1e293b;
    --bg-card-hover: #334155;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --border: #334155;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
}

body {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg-darker);
    color: var(--text-primary);
    line-height: 1.6;
    min-height: 100vh;
}

.navbar {
    background: linear-gradient(180deg, var(--bg-dark) 0%, rgba(15,23,42,0.95) 100%);
    border-bottom: 1px solid var(--border);
    padding: 0 2rem;
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(10px);
}

.nav-container {
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 64px;
}

.logo {
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
}

.logo-icon {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.logo-icon svg {
    width: 20px;
    height: 20px;
    fill: white;
}

.logo span {
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.nav-links {
    display: flex;
    gap: 0.5rem;
    list-style: none;
}

.nav-links a {
    color: var(--text-secondary);
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.9rem;
    font-weight: 500;
    transition: all 0.2s;
}

.nav-links a:hover {
    color: var(--text-primary);
    background: var(--bg-card);
}

.nav-links a.active {
    color: var(--primary);
    background: rgba(99, 102, 241, 0.1);
}

.nav-user {
    display: flex;
    align-items: center;
    gap: 12px;
}

.user-avatar {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, var(--primary) 0%, #8b5cf6 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.85rem;
}

.user-info {
    text-align: right;
}

.user-name {
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-primary);
}

.user-role {
    font-size: 0.75rem;
    color: var(--text-muted);
}

.main-content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
}

.page-header {
    margin-bottom: 2rem;
}

.page-header h1 {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    background: linear-gradient(135deg, var(--text-primary) 0%, var(--text-secondary) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.page-header p {
    color: var(--text-muted);
    font-size: 1rem;
}

.card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
}

.card-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text-primary);
}

.search-form {
    display: flex;
    gap: 1rem;
    align-items: flex-end;
}

.form-group {
    flex: 1;
}

.form-label {
    display: block;
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
}

.form-input {
    width: 100%;
    padding: 0.75rem 1rem;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.95rem;
    font-family: inherit;
    background: var(--bg-darker);
    color: var(--text-primary);
    transition: all 0.2s;
}

.form-input:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
}

.form-input::placeholder {
    color: var(--text-muted);
}

.btn {
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.9rem;
    font-family: inherit;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
}

.btn-primary {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
    color: white;
}

.btn-primary:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.btn svg {
    width: 18px;
    height: 18px;
}

.data-table {
    width: 100%;
    border-collapse: collapse;
}

.data-table th {
    text-align: left;
    padding: 0.75rem 1rem;
    background: var(--bg-darker);
    font-weight: 600;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    border-bottom: 1px solid var(--border);
}

.data-table td {
    padding: 1rem;
    border-bottom: 1px solid var(--border);
    font-size: 0.9rem;
}

.data-table tr:hover {
    background: var(--bg-card-hover);
}

.data-table tr:last-child td {
    border-bottom: none;
}

.badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}

.badge-primary {
    background: rgba(99, 102, 241, 0.2);
    color: var(--primary);
}

.badge-success {
    background: rgba(16, 185, 129, 0.2);
    color: var(--success);
}

.badge-warning {
    background: rgba(245, 158, 11, 0.2);
    color: var(--warning);
}

.badge-danger {
    background: rgba(239, 68, 68, 0.2);
    color: var(--danger);
}

.empty-state {
    padding: 4rem 2rem;
    text-align: center;
}

.empty-icon {
    width: 80px;
    height: 80px;
    margin: 0 auto 1.5rem;
    background: var(--bg-darker);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.empty-icon svg {
    width: 40px;
    height: 40px;
    fill: var(--text-muted);
}

.empty-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}

.empty-text {
    color: var(--text-muted);
}

.alert {
    padding: 1rem 1.5rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.alert-error {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #fca5a5;
}

.alert-warning {
    background: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.3);
    color: #fcd34d;
}

.alert-info {
    background: rgba(14, 165, 233, 0.1);
    border: 1px solid rgba(14, 165, 233, 0.3);
    color: #7dd3fc;
}

.alert-success {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #6ee7b7;
}

.grid {
    display: grid;
    gap: 1.5rem;
}

.grid-2 {
    grid-template-columns: repeat(2, 1fr);
}

.grid-3 {
    grid-template-columns: repeat(3, 1fr);
}

.grid-4 {
    grid-template-columns: repeat(4, 1fr);
}

@media (max-width: 1024px) {
    .grid-4 { grid-template-columns: repeat(2, 1fr); }
    .grid-3 { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 640px) {
    .grid-4, .grid-3, .grid-2 { grid-template-columns: 1fr; }
    .search-form { flex-direction: column; }
    .nav-links { display: none; }
}

.stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
}

.stat-card .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 1rem;
}

.stat-card .stat-icon svg {
    width: 24px;
    height: 24px;
}

.stat-card .stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-primary);
}

.stat-card .stat-label {
    color: var(--text-muted);
    font-size: 0.875rem;
}

.info-list {
    list-style: none;
}

.info-list li {
    display: flex;
    justify-content: space-between;
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border);
}

.info-list li:last-child {
    border-bottom: none;
}

.info-list .label {
    color: var(--text-muted);
}

.info-list .value {
    color: var(--text-primary);
    font-weight: 500;
}

.activity-item {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem 0;
    border-bottom: 1px solid var(--border);
}

.activity-item:last-child {
    border-bottom: none;
}

.activity-icon {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.activity-icon svg {
    width: 20px;
    height: 20px;
}

.activity-content {
    flex: 1;
}

.activity-title {
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
}

.activity-desc {
    font-size: 0.85rem;
    color: var(--text-muted);
}

.activity-time {
    font-size: 0.75rem;
    color: var(--text-muted);
}

.footer {
    background: var(--bg-dark);
    border-top: 1px solid var(--border);
    padding: 1.5rem 2rem;
    margin-top: 3rem;
}

.footer-container {
    max-width: 1400px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
}

.footer-left {
    display: flex;
    align-items: center;
    gap: 2rem;
}

.footer-copyright {
    font-size: 0.875rem;
    color: var(--text-muted);
}

.footer-links {
    display: flex;
    gap: 1.5rem;
    list-style: none;
}

.footer-links a {
    color: var(--text-muted);
    text-decoration: none;
    font-size: 0.875rem;
    transition: color 0.2s;
}

.footer-links a:hover {
    color: var(--text-primary);
}

.footer-tech {
    font-size: 0.8rem;
    color: var(--text-muted);
}

.progress-bar {
    height: 8px;
    background: var(--bg-darker);
    border-radius: 4px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s ease;
}

.chart-placeholder {
    height: 200px;
    background: var(--bg-darker);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
}
'''

# Navigation template
NAV_TEMPLATE = '''
<nav class="navbar">
    <div class="nav-container">
        <a href="/" class="logo">
            <div class="logo-icon">
                <svg viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
            </div>
            Nexus<span>HR</span>
        </a>
        <ul class="nav-links">
            <li><a href="/" class="{{ 'active' if active_page == 'directory' else '' }}">Directory</a></li>
            <li><a href="/departments" class="{{ 'active' if active_page == 'departments' else '' }}">Departments</a></li>
            <li><a href="/analytics" class="{{ 'active' if active_page == 'analytics' else '' }}">Analytics</a></li>
            <li><a href="/about" class="{{ 'active' if active_page == 'about' else '' }}">About</a></li>
        </ul>
        <div class="nav-user">
            <div class="user-info">
                <div class="user-name">Alex Chen</div>
                <div class="user-role">HR Manager</div>
            </div>
            <div class="user-avatar">AC</div>
        </div>
    </div>
</nav>
'''

# Footer template
FOOTER_TEMPLATE = '''
<footer class="footer">
    <div class="footer-container">
        <div class="footer-left">
            <span class="footer-copyright">&copy; 2024 NexusHR Enterprise. All rights reserved.</span>
            <ul class="footer-links">
                <li><a href="#">Privacy</a></li>
                <li><a href="#">Terms</a></li>
                <li><a href="#">Support</a></li>
            </ul>
        </div>
        <div class="footer-tech">
            Powered by PostgreSQL
        </div>
    </div>
</footer>
'''

# Main Directory Page
DIRECTORY_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NexusHR - Employee Directory</title>
    <style>''' + BASE_STYLES + '''</style>
</head>
<body>
    ''' + NAV_TEMPLATE + '''

    <main class="main-content">
        <div class="page-header">
            <h1>Employee Directory</h1>
            <p>Search and browse employee records across all departments.</p>
        </div>

        <div class="card">
            <form method="GET" action="/" class="search-form">
                <div class="form-group">
                    <label for="search" class="form-label">Search Employees</label>
                    <input type="text" id="search" name="q" class="form-input"
                           placeholder="Enter employee name or department..."
                           value="{{ search_query }}" autocomplete="off">
                </div>
                <button type="submit" class="btn btn-primary">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
                    Search
                </button>
            </form>
        </div>

        {% if error %}
        <div class="alert alert-error">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
            {{ error }}
        </div>
        {% endif %}

        <div class="card">
            <div class="card-header">
                <span class="card-title">Search Results</span>
                <span class="badge badge-primary">{{ employees|length }} found</span>
            </div>

            {% if employees %}
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Employee</th>
                        <th>Department</th>
                        <th>Position</th>
                        <th>Contact</th>
                    </tr>
                </thead>
                <tbody>
                    {% for emp in employees %}
                    <tr>
                        <td>
                            <strong>{{ emp.name }}</strong>
                            <div style="color: var(--text-muted); font-size: 0.8rem;">ID: {{ emp.id }}</div>
                        </td>
                        <td><span class="badge badge-primary">{{ emp.department }}</span></td>
                        <td>{{ emp.position }}</td>
                        <td><a href="mailto:{{ emp.email }}" style="color: var(--secondary);">{{ emp.email }}</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty-state">
                <div class="empty-icon">
                    <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
                </div>
                <h3 class="empty-title">{% if search_query %}No employees found{% else %}Start Your Search{% endif %}</h3>
                <p class="empty-text">{% if search_query %}Try a different search term.{% else %}Enter a name or department to search the employee database.{% endif %}</p>
            </div>
            {% endif %}
        </div>
    </main>

    ''' + FOOTER_TEMPLATE + '''
</body>
</html>
'''

# Departments Page
DEPARTMENTS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NexusHR - Departments</title>
    <style>''' + BASE_STYLES + '''</style>
</head>
<body>
    ''' + NAV_TEMPLATE + '''

    <main class="main-content">
        <div class="page-header">
            <h1>Departments</h1>
            <p>Organization structure and team overview.</p>
        </div>

        <div class="grid grid-4">
            <div class="stat-card">
                <div class="stat-icon" style="background: rgba(99, 102, 241, 0.2);">
                    <svg fill="var(--primary)" viewBox="0 0 24 24"><path d="M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10zm-2-8h-2v2h2v-2zm0 4h-2v2h2v-2z"/></svg>
                </div>
                <div class="stat-value">7</div>
                <div class="stat-label">Departments</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon" style="background: rgba(14, 165, 233, 0.2);">
                    <svg fill="var(--secondary)" viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>
                </div>
                <div class="stat-value">10</div>
                <div class="stat-label">Total Employees</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon" style="background: rgba(16, 185, 129, 0.2);">
                    <svg fill="var(--success)" viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg>
                </div>
                <div class="stat-value">$1.1M</div>
                <div class="stat-label">Annual Payroll</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon" style="background: rgba(245, 158, 11, 0.2);">
                    <svg fill="var(--warning)" viewBox="0 0 24 24"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>
                </div>
                <div class="stat-value">3.2</div>
                <div class="stat-label">Avg. Tenure (yrs)</div>
            </div>
        </div>

        <div class="grid grid-2">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Department List</span>
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Department</th>
                            <th>Head Count</th>
                            <th>Budget Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Engineering</strong></td>
                            <td>4</td>
                            <td><span class="badge badge-success">On Track</span></td>
                        </tr>
                        <tr>
                            <td><strong>Marketing</strong></td>
                            <td>1</td>
                            <td><span class="badge badge-success">On Track</span></td>
                        </tr>
                        <tr>
                            <td><strong>Finance</strong></td>
                            <td>1</td>
                            <td><span class="badge badge-success">On Track</span></td>
                        </tr>
                        <tr>
                            <td><strong>Human Resources</strong></td>
                            <td>1</td>
                            <td><span class="badge badge-warning">Review</span></td>
                        </tr>
                        <tr>
                            <td><strong>Sales</strong></td>
                            <td>1</td>
                            <td><span class="badge badge-success">On Track</span></td>
                        </tr>
                        <tr>
                            <td><strong>Legal</strong></td>
                            <td>1</td>
                            <td><span class="badge badge-success">On Track</span></td>
                        </tr>
                        <tr>
                            <td><strong>Operations</strong></td>
                            <td>1</td>
                            <td><span class="badge badge-success">On Track</span></td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="card">
                <div class="card-header">
                    <span class="card-title">Recent Activity</span>
                </div>
                <div class="activity-item">
                    <div class="activity-icon" style="background: rgba(16, 185, 129, 0.2);">
                        <svg fill="var(--success)" viewBox="0 0 24 24"><path d="M15 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm-9-2V7H4v3H1v2h3v3h2v-3h3v-2H6zm9 4c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
                    </div>
                    <div class="activity-content">
                        <div class="activity-title">New hire: David Wilson</div>
                        <div class="activity-desc">Frontend Developer - Engineering</div>
                    </div>
                    <div class="activity-time">2 days ago</div>
                </div>
                <div class="activity-item">
                    <div class="activity-icon" style="background: rgba(99, 102, 241, 0.2);">
                        <svg fill="var(--primary)" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                    </div>
                    <div class="activity-content">
                        <div class="activity-title">Promotion: James Chen</div>
                        <div class="activity-desc">Promoted to DevOps Lead</div>
                    </div>
                    <div class="activity-time">1 week ago</div>
                </div>
                <div class="activity-item">
                    <div class="activity-icon" style="background: rgba(245, 158, 11, 0.2);">
                        <svg fill="var(--warning)" viewBox="0 0 24 24"><path d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
                    </div>
                    <div class="activity-content">
                        <div class="activity-title">Policy Update</div>
                        <div class="activity-desc">Remote work policy revised</div>
                    </div>
                    <div class="activity-time">2 weeks ago</div>
                </div>
            </div>
        </div>
    </main>

    ''' + FOOTER_TEMPLATE + '''
</body>
</html>
'''

# Analytics Page
ANALYTICS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NexusHR - Analytics</title>
    <style>''' + BASE_STYLES + '''</style>
</head>
<body>
    ''' + NAV_TEMPLATE + '''

    <main class="main-content">
        <div class="page-header">
            <h1>HR Analytics</h1>
            <p>Workforce insights and performance metrics.</p>
        </div>

        <div class="grid grid-4">
            <div class="stat-card">
                <div class="stat-icon" style="background: rgba(16, 185, 129, 0.2);">
                    <svg fill="var(--success)" viewBox="0 0 24 24"><path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z"/></svg>
                </div>
                <div class="stat-value">94%</div>
                <div class="stat-label">Retention Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon" style="background: rgba(99, 102, 241, 0.2);">
                    <svg fill="var(--primary)" viewBox="0 0 24 24"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z"/></svg>
                </div>
                <div class="stat-value">4.2</div>
                <div class="stat-label">Satisfaction Score</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon" style="background: rgba(14, 165, 233, 0.2);">
                    <svg fill="var(--secondary)" viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg>
                </div>
                <div class="stat-value">23</div>
                <div class="stat-label">Avg. Days to Hire</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon" style="background: rgba(245, 158, 11, 0.2);">
                    <svg fill="var(--warning)" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
                </div>
                <div class="stat-value">2</div>
                <div class="stat-label">Open Positions</div>
            </div>
        </div>

        <div class="grid grid-2">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Department Headcount</span>
                </div>
                <div style="padding: 1rem 0;">
                    <div style="margin-bottom: 1.5rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span>Engineering</span>
                            <span style="color: var(--text-muted);">4 employees</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 40%; background: var(--primary);"></div>
                        </div>
                    </div>
                    <div style="margin-bottom: 1.5rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span>Marketing</span>
                            <span style="color: var(--text-muted);">1 employee</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 10%; background: var(--secondary);"></div>
                        </div>
                    </div>
                    <div style="margin-bottom: 1.5rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span>Finance</span>
                            <span style="color: var(--text-muted);">1 employee</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 10%; background: var(--success);"></div>
                        </div>
                    </div>
                    <div style="margin-bottom: 1.5rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span>Other</span>
                            <span style="color: var(--text-muted);">4 employees</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 40%; background: var(--warning);"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <span class="card-title">Salary Distribution</span>
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Range</th>
                            <th>Count</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>$80K - $100K</td>
                            <td>3</td>
                            <td>30%</td>
                        </tr>
                        <tr>
                            <td>$100K - $120K</td>
                            <td>3</td>
                            <td>30%</td>
                        </tr>
                        <tr>
                            <td>$120K - $140K</td>
                            <td>2</td>
                            <td>20%</td>
                        </tr>
                        <tr>
                            <td>$140K+</td>
                            <td>2</td>
                            <td>20%</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <span class="card-title">Quarterly Hiring Trends</span>
            </div>
            <div class="chart-placeholder">
                <span>Chart visualization would appear here</span>
            </div>
        </div>
    </main>

    ''' + FOOTER_TEMPLATE + '''
</body>
</html>
'''

# About Page
ABOUT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NexusHR - About</title>
    <style>''' + BASE_STYLES + '''</style>
</head>
<body>
    ''' + NAV_TEMPLATE + '''

    <main class="main-content">
        <div class="page-header">
            <h1>About NexusHR</h1>
            <p>Enterprise Human Resources Management System</p>
        </div>

        <div class="grid grid-2">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">System Information</span>
                </div>
                <ul class="info-list">
                    <li>
                        <span class="label">Version</span>
                        <span class="value">2.1.0</span>
                    </li>
                    <li>
                        <span class="label">Release Date</span>
                        <span class="value">December 2024</span>
                    </li>
                    <li>
                        <span class="label">License</span>
                        <span class="value">Enterprise</span>
                    </li>
                    <li>
                        <span class="label">Environment</span>
                        <span class="value">Production</span>
                    </li>
                </ul>
            </div>

            <div class="card">
                <div class="card-header">
                    <span class="card-title">Technical Stack</span>
                </div>
                <ul class="info-list">
                    <li>
                        <span class="label">Backend</span>
                        <span class="value">Python / Flask</span>
                    </li>
                    <li>
                        <span class="label">Database</span>
                        <span class="value">PostgreSQL 16</span>
                    </li>
                    <li>
                        <span class="label">Server</span>
                        <span class="value">Gunicorn</span>
                    </li>
                    <li>
                        <span class="label">Container</span>
                        <span class="value">Docker</span>
                    </li>
                </ul>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <span class="card-title">Features</span>
            </div>
            <div class="grid grid-3" style="padding-top: 1rem;">
                <div style="text-align: center; padding: 1rem;">
                    <div style="width: 60px; height: 60px; background: rgba(99, 102, 241, 0.2); border-radius: 12px; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem;">
                        <svg width="28" height="28" fill="var(--primary)" viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
                    </div>
                    <h4 style="margin-bottom: 0.5rem;">Employee Search</h4>
                    <p style="color: var(--text-muted); font-size: 0.9rem;">Quick search across all employee records</p>
                </div>
                <div style="text-align: center; padding: 1rem;">
                    <div style="width: 60px; height: 60px; background: rgba(14, 165, 233, 0.2); border-radius: 12px; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem;">
                        <svg width="28" height="28" fill="var(--secondary)" viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg>
                    </div>
                    <h4 style="margin-bottom: 0.5rem;">Analytics</h4>
                    <p style="color: var(--text-muted); font-size: 0.9rem;">Workforce insights and reporting</p>
                </div>
                <div style="text-align: center; padding: 1rem;">
                    <div style="width: 60px; height: 60px; background: rgba(16, 185, 129, 0.2); border-radius: 12px; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem;">
                        <svg width="28" height="28" fill="var(--success)" viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/></svg>
                    </div>
                    <h4 style="margin-bottom: 0.5rem;">Secure</h4>
                    <p style="color: var(--text-muted); font-size: 0.9rem;">Enterprise-grade data protection</p>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <span class="card-title">Support</span>
            </div>
            <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                For technical support or questions about NexusHR, please contact your system administrator.
            </p>
            <ul class="info-list">
                <li>
                    <span class="label">Documentation</span>
                    <span class="value">docs.nexushr.local</span>
                </li>
                <li>
                    <span class="label">Support Portal</span>
                    <span class="value">support.nexushr.local</span>
                </li>
                <li>
                    <span class="label">Status Page</span>
                    <span class="value">status.nexushr.local</span>
                </li>
            </ul>
        </div>
    </main>

    ''' + FOOTER_TEMPLATE + '''
</body>
</html>
'''


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

    return render_template_string(
        DIRECTORY_TEMPLATE,
        search_query=search_query,
        employees=employees,
        error=error,
        active_page='directory'
    )


@app.route('/departments')
def departments():
    """Departments overview page."""
    return render_template_string(DEPARTMENTS_TEMPLATE, active_page='departments')


@app.route('/analytics')
def analytics():
    """Analytics dashboard page."""
    return render_template_string(ANALYTICS_TEMPLATE, active_page='analytics')


@app.route('/about')
def about():
    """About page."""
    return render_template_string(ABOUT_TEMPLATE, active_page='about')


@app.route('/health')
def health():
    """Health check endpoint."""
    return {'status': 'healthy', 'service': 'nexushr-web'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
