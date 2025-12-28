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


# HTML Template with professional enterprise styling
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NexusHR - Employee Directory</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f8fafc;
            color: #1e293b;
            line-height: 1.6;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* Navigation */
        .navbar {
            background: linear-gradient(135deg, #1e3a5f 0%, #0f2644 100%);
            padding: 0 2rem;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }

        .nav-container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            height: 70px;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
        }

        .logo-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .logo-icon svg {
            width: 24px;
            height: 24px;
            fill: white;
        }

        .logo-text {
            font-size: 1.5rem;
            font-weight: 700;
            color: white;
            letter-spacing: -0.5px;
        }

        .logo-text span {
            color: #60a5fa;
        }

        .nav-links {
            display: flex;
            gap: 2rem;
            list-style: none;
        }

        .nav-links a {
            color: #cbd5e1;
            text-decoration: none;
            font-weight: 500;
            font-size: 0.95rem;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            transition: all 0.2s ease;
        }

        .nav-links a:hover,
        .nav-links a.active {
            color: white;
            background: rgba(255, 255, 255, 0.1);
        }

        .nav-user {
            display: flex;
            align-items: center;
            gap: 12px;
            color: white;
        }

        .user-avatar {
            width: 38px;
            height: 38px;
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.9rem;
        }

        .user-info {
            text-align: right;
        }

        .user-name {
            font-weight: 600;
            font-size: 0.9rem;
        }

        .user-role {
            font-size: 0.75rem;
            color: #94a3b8;
        }

        /* Main Content */
        .main-content {
            flex: 1;
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
            width: 100%;
        }

        /* Page Header */
        .page-header {
            margin-bottom: 2rem;
        }

        .page-title {
            font-size: 1.875rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.5rem;
        }

        .page-description {
            color: #64748b;
            font-size: 0.95rem;
        }

        /* Search Section */
        .search-section {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            margin-bottom: 2rem;
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
            color: #374151;
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
        }

        .form-input {
            width: 100%;
            padding: 0.75rem 1rem;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            font-size: 0.95rem;
            font-family: inherit;
            transition: all 0.2s ease;
            background: #f9fafb;
        }

        .form-input:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            background: white;
        }

        .form-input::placeholder {
            color: #9ca3af;
        }

        .btn {
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.95rem;
            font-family: inherit;
            cursor: pointer;
            transition: all 0.2s ease;
            border: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }

        .btn-primary {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
        }

        .btn-primary:hover {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }

        .btn svg {
            width: 18px;
            height: 18px;
        }

        /* Results Section */
        .results-section {
            background: white;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }

        .results-header {
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .results-title {
            font-weight: 600;
            color: #1e293b;
        }

        .results-count {
            color: #64748b;
            font-size: 0.875rem;
        }

        .results-table {
            width: 100%;
            border-collapse: collapse;
        }

        .results-table th {
            text-align: left;
            padding: 1rem 1.5rem;
            background: #f8fafc;
            font-weight: 600;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            border-bottom: 1px solid #e5e7eb;
        }

        .results-table td {
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #f1f5f9;
            font-size: 0.95rem;
        }

        .results-table tr:last-child td {
            border-bottom: none;
        }

        .results-table tr:hover {
            background: #f8fafc;
        }

        .employee-name {
            font-weight: 600;
            color: #1e293b;
        }

        .employee-id {
            color: #94a3b8;
            font-size: 0.8rem;
            font-weight: 400;
        }

        .department-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            background: #eff6ff;
            color: #1e40af;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }

        .email-link {
            color: #3b82f6;
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
            width: 80px;
            height: 80px;
            margin: 0 auto 1.5rem;
            background: #f1f5f9;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .empty-icon svg {
            width: 40px;
            height: 40px;
            fill: #94a3b8;
        }

        .empty-title {
            font-size: 1.125rem;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 0.5rem;
        }

        .empty-text {
            color: #64748b;
            font-size: 0.95rem;
        }

        /* Error State */
        .error-message {
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: #b91c1c;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            font-size: 0.95rem;
        }

        /* Footer */
        .footer {
            background: #1e293b;
            color: #94a3b8;
            padding: 1.5rem 2rem;
            margin-top: auto;
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
        }

        .footer-links {
            display: flex;
            gap: 1.5rem;
            list-style: none;
        }

        .footer-links a {
            color: #94a3b8;
            text-decoration: none;
            font-size: 0.875rem;
            transition: color 0.2s ease;
        }

        .footer-links a:hover {
            color: white;
        }

        .footer-tech {
            font-size: 0.75rem;
            color: #64748b;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .footer-tech-divider {
            color: #475569;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .nav-links {
                display: none;
            }

            .search-form {
                flex-direction: column;
            }

            .footer-container {
                flex-direction: column;
                text-align: center;
            }

            .footer-left {
                flex-direction: column;
                gap: 1rem;
            }
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar">
        <div class="nav-container">
            <a href="/" class="logo">
                <div class="logo-icon">
                    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                    </svg>
                </div>
                <span class="logo-text">Nexus<span>HR</span></span>
            </a>

            <ul class="nav-links">
                <li><a href="/" class="active">Employee Directory</a></li>
                <li><a href="#">Departments</a></li>
                <li><a href="#">Reports</a></li>
                <li><a href="#">Settings</a></li>
            </ul>

            <div class="nav-user">
                <div class="user-info">
                    <div class="user-name">HR Administrator</div>
                    <div class="user-role">Human Resources</div>
                </div>
                <div class="user-avatar">HA</div>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
        <div class="page-header">
            <h1 class="page-title">Employee Directory</h1>
            <p class="page-description">Search and manage employee records using our command-line database interface. Enter a name or department to find employees.</p>
        </div>

        <!-- Search Section -->
        <section class="search-section">
            <form method="GET" action="/" class="search-form">
                <div class="form-group">
                    <label for="search" class="form-label">Search Employees</label>
                    <input
                        type="text"
                        id="search"
                        name="q"
                        class="form-input"
                        placeholder="Enter employee name or department..."
                        value="{{ search_query }}"
                        autocomplete="off"
                    >
                </div>
                <button type="submit" class="btn btn-primary">
                    <svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                        <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                    </svg>
                    Search
                </button>
            </form>
        </section>

        {% if error %}
        <div class="error-message">
            {{ error }}
        </div>
        {% endif %}

        <!-- Results Section -->
        <section class="results-section">
            <div class="results-header">
                <span class="results-title">Search Results</span>
                <span class="results-count">{{ employees|length }} employee(s) found</span>
            </div>

            {% if employees %}
            <table class="results-table">
                <thead>
                    <tr>
                        <th>Employee</th>
                        <th>Department</th>
                        <th>Position</th>
                        <th>Email</th>
                    </tr>
                </thead>
                <tbody>
                    {% for emp in employees %}
                    <tr>
                        <td>
                            <div class="employee-name">{{ emp.name }}</div>
                            <div class="employee-id">ID: {{ emp.id }}</div>
                        </td>
                        <td><span class="department-badge">{{ emp.department }}</span></td>
                        <td>{{ emp.position }}</td>
                        <td><a href="mailto:{{ emp.email }}" class="email-link">{{ emp.email }}</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty-state">
                <div class="empty-icon">
                    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                    </svg>
                </div>
                <h3 class="empty-title">{% if search_query %}No employees found{% else %}Enter a search term{% endif %}</h3>
                <p class="empty-text">{% if search_query %}Try adjusting your search criteria or check the spelling.{% else %}Use the search box above to find employees by name or department.{% endif %}</p>
            </div>
            {% endif %}
        </section>
    </main>

    <!-- Footer -->
    <footer class="footer">
        <div class="footer-container">
            <div class="footer-left">
                <span class="footer-copyright">2024 NexusHR Enterprise. All rights reserved.</span>
                <ul class="footer-links">
                    <li><a href="#">Privacy Policy</a></li>
                    <li><a href="#">Terms of Service</a></li>
                    <li><a href="#">Support</a></li>
                </ul>
            </div>
            <div class="footer-tech">
                <span>PostgreSQL 16.6</span>
                <span class="footer-tech-divider">|</span>
                <span>psql CLI Backend</span>
            </div>
        </div>
    </footer>
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
        HTML_TEMPLATE,
        search_query=search_query,
        employees=employees,
        error=error
    )


@app.route('/health')
def health():
    """Health check endpoint."""
    return {'status': 'healthy', 'service': 'nexushr-web'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
