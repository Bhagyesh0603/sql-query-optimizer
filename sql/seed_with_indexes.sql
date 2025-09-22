-- Drop old tables if exist
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS departments CASCADE;
DROP TABLE IF EXISTS salaries CASCADE;
DROP TABLE IF EXISTS projects CASCADE;

-- Departments
CREATE TABLE departments (
    dept_id SERIAL PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL
);

-- Employees
CREATE TABLE employees (
    emp_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    dept_id INT REFERENCES departments(dept_id),
    hire_date DATE NOT NULL,
    salary NUMERIC(10,2)
);

-- Salaries history
CREATE TABLE salaries (
    emp_id INT REFERENCES employees(emp_id),
    amount NUMERIC(10,2),
    from_date DATE,
    to_date DATE,
    PRIMARY KEY(emp_id, from_date)
);

-- Projects
CREATE TABLE projects (
    proj_id SERIAL PRIMARY KEY,
    proj_name VARCHAR(100),
    dept_id INT REFERENCES departments(dept_id),
    budget NUMERIC(12,2)
);

-- Indexes to improve join performance
CREATE INDEX idx_emp_dept ON employees(dept_id);
CREATE INDEX idx_sal_emp ON salaries(emp_id);
CREATE INDEX idx_proj_dept ON projects(dept_id);

-- Sample data
INSERT INTO departments (dept_name) VALUES
('HR'), ('Engineering'), ('Sales'), ('Finance');

INSERT INTO employees (first_name, last_name, dept_id, hire_date, salary) VALUES
('Amit', 'Sharma', 1, '2015-06-01', 50000),
('Priya', 'Mehta', 2, '2018-09-15', 75000),
('Rahul', 'Verma', 2, '2017-02-20', 68000),
('Sneha', 'Patil', 3, '2020-01-10', 45000),
('Karan', 'Gupta', 4, '2016-11-23', 90000);

INSERT INTO salaries (emp_id, amount, from_date, to_date) VALUES
(1, 48000, '2015-06-01', '2016-05-31'),
(1, 50000, '2016-06-01', '9999-01-01'),
(2, 70000, '2018-09-15', '2020-12-31'),
(2, 75000, '2021-01-01', '9999-01-01'),
(3, 65000, '2017-02-20', '2019-12-31'),
(3, 68000, '2020-01-01', '9999-01-01');

INSERT INTO projects (proj_name, dept_id, budget) VALUES
('Recruitment System', 1, 200000),
('AI Platform', 2, 500000),
('CRM Tool', 3, 300000),
('Audit Tracker', 4, 150000);
