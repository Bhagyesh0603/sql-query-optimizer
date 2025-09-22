import psycopg2
from faker import Faker
import random
from datetime import timedelta

fake = Faker()

# --------------------------------
# DB connection
# --------------------------------
conn = psycopg2.connect(
    host="localhost",
    database="sql_optimizer",
    user="postgres",
    password="JOSHIbjj@0603005"
)
cur = conn.cursor()

# --------------------------------
# Drop + recreate schema
# --------------------------------
cur.execute("""
DROP TABLE IF EXISTS appointments, visits, patients, doctors, salaries, projects, employees, departments CASCADE;

CREATE TABLE departments (
    dept_id SERIAL PRIMARY KEY,
    dept_name VARCHAR(50)
);
CREATE TABLE employees (
    emp_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    dept_id INT REFERENCES departments(dept_id),
    hire_date DATE,
    salary NUMERIC
);
CREATE TABLE projects (
    proj_id SERIAL PRIMARY KEY,
    proj_name VARCHAR(50),
    dept_id INT REFERENCES departments(dept_id),
    budget NUMERIC
);
CREATE TABLE salaries (
    emp_id INT REFERENCES employees(emp_id),
    amount NUMERIC,
    from_date DATE,
    to_date DATE
);
CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    dob DATE
);
CREATE TABLE doctors (
    doctor_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    specialty VARCHAR(50)
);
CREATE TABLE visits (
    visit_id SERIAL PRIMARY KEY,
    emp_id INT REFERENCES employees(emp_id),
    patient_id INT REFERENCES patients(patient_id)
);
CREATE TABLE appointments (
    appointment_id SERIAL PRIMARY KEY,
    visit_id INT REFERENCES visits(visit_id),
    doctor_id INT REFERENCES doctors(doctor_id),
    appointment_date DATE
);
""")
conn.commit()

# --------------------------------
# Configurable dataset sizes
# --------------------------------
N_DEPTS = 10
N_EMPLOYEES = 500
N_PROJECTS = 50
N_PATIENTS = 200
N_DOCTORS = 50
N_VISITS = 1000
N_APPOINTMENTS = 1000

# --------------------------------
# Seed data
# --------------------------------

# Departments
cur.executemany("INSERT INTO departments (dept_name) VALUES (%s);",
                [(fake.company(),) for _ in range(N_DEPTS)])

# Employees
cur.executemany(
    "INSERT INTO employees (first_name, last_name, dept_id, hire_date, salary) VALUES (%s, %s, %s, %s, %s);",
    [(fake.first_name(), fake.last_name(),
      random.randint(1, N_DEPTS),
      fake.date_between(start_date='-10y', end_date='today'),
      random.randint(30000, 150000))
     for _ in range(N_EMPLOYEES)]
)

# Projects
cur.executemany(
    "INSERT INTO projects (proj_name, dept_id, budget) VALUES (%s, %s, %s);",
    [(fake.bs(), random.randint(1, N_DEPTS), random.randint(5000, 200000))
     for _ in range(N_PROJECTS)]
)

# Salaries
salary_rows = []
for emp_id in range(1, N_EMPLOYEES + 1):
    for _ in range(2):
        from_date = fake.date_between(start_date='-5y', end_date='-1y')
        to_date = from_date + timedelta(days=random.randint(180, 730))
        salary_rows.append((emp_id, random.randint(30000, 150000), from_date, to_date))
cur.executemany(
    "INSERT INTO salaries (emp_id, amount, from_date, to_date) VALUES (%s, %s, %s, %s);",
    salary_rows
)

# Patients
cur.executemany(
    "INSERT INTO patients (name, dob) VALUES (%s, %s);",
    [(fake.name(), fake.date_of_birth(minimum_age=0, maximum_age=90))
     for _ in range(N_PATIENTS)]
)

# Doctors
cur.executemany(
    "INSERT INTO doctors (name, specialty) VALUES (%s, %s);",
    [(fake.name(), fake.job()) for _ in range(N_DOCTORS)]
)

# Visits
cur.executemany(
    "INSERT INTO visits (emp_id, patient_id) VALUES (%s, %s);",
    [(random.randint(1, N_EMPLOYEES), random.randint(1, N_PATIENTS))
     for _ in range(N_VISITS)]
)

# Appointments
cur.executemany(
    "INSERT INTO appointments (visit_id, doctor_id, appointment_date) VALUES (%s, %s, %s);",
    [(random.randint(1, N_VISITS), random.randint(1, N_DOCTORS),
      fake.date_between(start_date='-3y', end_date='today'))
     for _ in range(N_APPOINTMENTS)]
)

conn.commit()
cur.close()
conn.close()

print("✅ Dummy data populated successfully with optimized seeding!")
