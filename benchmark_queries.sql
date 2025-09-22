-- Query 1: Full scan (baseline)
SELECT * FROM employees;

-- Query 2: Indexed filter
SELECT * FROM employees WHERE salary BETWEEN 80000 AND 100000;

-- Query 3: Join with filter (dept + budget)
SELECT e.emp_id, e.first_name, d.dept_name, p.proj_name
FROM employees e
JOIN departments d ON e.dept_id = d.dept_id
JOIN projects p ON d.dept_id = p.dept_id
WHERE p.budget > 1000000;

-- Query 4: Aggregation with GROUP BY
SELECT dept_id, AVG(salary), COUNT(*) AS emp_count
FROM employees
GROUP BY dept_id;

-- Query 5: Correlated subquery
SELECT emp_id, first_name
FROM employees e
WHERE salary > (SELECT AVG(salary) FROM employees s WHERE s.dept_id = e.dept_id);

-- Query 6: Heavy join with ORDER + LIMIT
SELECT e.emp_id, e.first_name, p.proj_name, p.budget
FROM employees e
JOIN projects p ON e.dept_id = p.dept_id
ORDER BY p.budget DESC
LIMIT 100;

-- Query 7: Nested join + filter
SELECT e.emp_id, e.first_name, d.dept_name, p.proj_name
FROM employees e
JOIN departments d ON e.dept_id = d.dept_id
JOIN projects p ON d.dept_id = p.dept_id
WHERE e.salary > 120000 AND p.budget < 200000;

-- Query 8: Aggregation with HAVING
SELECT dept_id, COUNT(*) AS emp_count
FROM employees
GROUP BY dept_id
HAVING COUNT(*) > 5000;

-- Query 9: Subquery in WHERE (budget threshold)
SELECT emp_id, first_name
FROM employees
WHERE dept_id IN (
    SELECT dept_id
    FROM projects
    WHERE budget > 1800000
);

-- Query 10: Complex join + aggregation
SELECT d.dept_name, COUNT(e.emp_id) AS emp_count, SUM(p.budget) AS total_budget
FROM employees e
JOIN departments d ON e.dept_id = d.dept_id
JOIN projects p ON d.dept_id = p.dept_id
GROUP BY d.dept_name
ORDER BY total_budget DESC;
