-- Basic SELECT Examples
-- These queries demonstrate common optimization opportunities

-- Example 1: SELECT * issue
-- Problem: Retrieves all columns, inefficient I/O
SELECT * FROM employees WHERE salary > 50000;

-- Optimized version:
-- SELECT emp_id, first_name, last_name, salary FROM employees WHERE salary > 50000;

-- Example 2: Missing LIMIT with ORDER BY
-- Problem: Sorts entire result set without limit
SELECT first_name, last_name, salary 
FROM employees 
WHERE dept_id = 1 
ORDER BY salary DESC;

-- Optimized version:
-- SELECT first_name, last_name, salary 
-- FROM employees 
-- WHERE dept_id = 1 
-- ORDER BY salary DESC 
-- LIMIT 10;

-- Example 3: Function in WHERE clause
-- Problem: Prevents index usage
SELECT emp_id, first_name, last_name 
FROM employees 
WHERE UPPER(first_name) = 'JOHN';

-- Optimized version:
-- SELECT emp_id, first_name, last_name 
-- FROM employees 
-- WHERE first_name ILIKE 'john';
-- -- Or create functional index: CREATE INDEX idx_employees_upper_name ON employees (UPPER(first_name));

-- Example 4: LIKE with leading wildcard
-- Problem: Cannot use indexes effectively
SELECT emp_id, first_name, last_name 
FROM employees 
WHERE first_name LIKE '%john%';

-- Better approach (if possible):
-- SELECT emp_id, first_name, last_name 
-- FROM employees 
-- WHERE first_name LIKE 'john%';
-- -- Or use full-text search for complex pattern matching