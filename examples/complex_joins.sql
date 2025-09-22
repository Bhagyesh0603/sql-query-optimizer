-- Complex JOIN Examples
-- These queries show optimization opportunities in multi-table scenarios

-- Example 1: Missing JOIN conditions (Cartesian Product)
-- Problem: Creates cartesian product between tables
SELECT e.first_name, d.dept_name, p.project_name
FROM employees e, departments d, projects p
WHERE e.salary > 50000;

-- Optimized version:
-- SELECT e.first_name, d.dept_name, p.project_name
-- FROM employees e
-- JOIN departments d ON e.dept_id = d.id
-- JOIN projects p ON e.emp_id = p.employee_id
-- WHERE e.salary > 50000;

-- Example 2: Subquery that could be JOIN
-- Problem: N+1 query pattern, inefficient execution
SELECT emp_id, first_name, last_name
FROM employees
WHERE dept_id IN (
    SELECT id 
    FROM departments 
    WHERE budget > 100000
);

-- Optimized version:
-- SELECT e.emp_id, e.first_name, e.last_name
-- FROM employees e
-- JOIN departments d ON e.dept_id = d.id
-- WHERE d.budget > 100000;

-- Example 3: Complex JOIN with aggregation
-- Shows opportunities for index recommendations
SELECT d.dept_name, 
       COUNT(*) as employee_count,
       AVG(e.salary) as avg_salary,
       MAX(e.hire_date) as latest_hire
FROM employees e
JOIN departments d ON e.dept_id = d.id
WHERE e.hire_date >= '2020-01-01'
GROUP BY d.dept_name
HAVING COUNT(*) > 5
ORDER BY avg_salary DESC;

-- Recommended indexes:
-- CREATE INDEX idx_employees_hire_date ON employees (hire_date);
-- CREATE INDEX idx_employees_dept_salary ON employees (dept_id, salary);
-- CREATE INDEX idx_departments_name ON departments (dept_name);

-- Example 4: Multiple subqueries that could be optimized
SELECT e.emp_id, e.first_name, e.last_name,
       (SELECT COUNT(*) FROM projects p WHERE p.employee_id = e.emp_id) as project_count,
       (SELECT d.dept_name FROM departments d WHERE d.id = e.dept_id) as dept_name
FROM employees e
WHERE e.salary > (
    SELECT AVG(salary) 
    FROM employees e2 
    WHERE e2.dept_id = e.dept_id
);

-- Optimized version:
-- WITH dept_avg_salaries AS (
--     SELECT dept_id, AVG(salary) as avg_salary
--     FROM employees
--     GROUP BY dept_id
-- )
-- SELECT e.emp_id, e.first_name, e.last_name,
--        COUNT(p.project_id) as project_count,
--        d.dept_name
-- FROM employees e
-- JOIN departments d ON e.dept_id = d.id
-- JOIN dept_avg_salaries das ON e.dept_id = das.dept_id
-- LEFT JOIN projects p ON e.emp_id = p.employee_id
-- WHERE e.salary > das.avg_salary
-- GROUP BY e.emp_id, e.first_name, e.last_name, d.dept_name;