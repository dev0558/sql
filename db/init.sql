-- NexusHR Database Initialization
-- Enterprise Human Resources Management System

-- Create employees table
CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    position VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    salary DECIMAL(10, 2) NOT NULL,
    hire_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create hr_secrets table (confidential HR data)
CREATE TABLE IF NOT EXISTS hr_secrets (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    classification VARCHAR(20) DEFAULT 'CONFIDENTIAL',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample employees
INSERT INTO employees (name, department, position, email, salary, hire_date) VALUES
    ('Sarah Mitchell', 'Engineering', 'Senior Software Engineer', 's.mitchell@nexushr.local', 145000.00, '2019-03-15'),
    ('James Chen', 'Engineering', 'DevOps Lead', 'j.chen@nexushr.local', 135000.00, '2020-06-01'),
    ('Emily Rodriguez', 'Marketing', 'Marketing Director', 'e.rodriguez@nexushr.local', 125000.00, '2018-09-20'),
    ('Michael Thompson', 'Finance', 'Financial Analyst', 'm.thompson@nexushr.local', 95000.00, '2021-01-10'),
    ('Jessica Park', 'Human Resources', 'HR Manager', 'j.park@nexushr.local', 105000.00, '2017-11-05'),
    ('David Wilson', 'Engineering', 'Frontend Developer', 'd.wilson@nexushr.local', 110000.00, '2022-02-28'),
    ('Amanda Foster', 'Sales', 'Sales Executive', 'a.foster@nexushr.local', 85000.00, '2021-08-15'),
    ('Robert Kim', 'Engineering', 'Backend Developer', 'r.kim@nexushr.local', 115000.00, '2020-11-30'),
    ('Lisa Nguyen', 'Legal', 'Corporate Counsel', 'l.nguyen@nexushr.local', 155000.00, '2019-07-22'),
    ('Christopher Brown', 'Operations', 'Operations Manager', 'c.brown@nexushr.local', 98000.00, '2018-04-18');

-- Insert confidential HR secrets
INSERT INTO hr_secrets (key, value, classification) VALUES
    ('admin_flag', 'Exploit3rs{th3_gr34t_3sc4p3_cve2025}', 'TOP SECRET'),
    ('executive_bonus_pool', '2500000', 'CONFIDENTIAL'),
    ('layoff_list_q4', 'PENDING REVIEW - 15 positions', 'CONFIDENTIAL'),
    ('merger_codename', 'Project Phoenix', 'TOP SECRET'),
    ('salary_adjustment_budget', '850000', 'CONFIDENTIAL'),
    ('ceo_compensation_2024', '4750000', 'TOP SECRET');

-- Create index for faster searches
CREATE INDEX idx_employees_name ON employees(name);
CREATE INDEX idx_employees_department ON employees(department);

-- Grant permissions
GRANT SELECT ON employees TO PUBLIC;
-- hr_secrets should only be accessible via direct query (no application access)
