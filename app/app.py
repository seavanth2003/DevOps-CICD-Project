import os
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from database import get_db_connection, init_db
from auth import auth


# ==========================================
# APPLICATION CONFIGURATION
# ==========================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "local-development-secret-change-before-deployment"
)

# Register authentication routes
app.register_blueprint(auth)

# Initialize database
init_db()


# ==========================================
# LOGIN REQUIRED DECORATOR
# ==========================================

def login_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            flash(
                "Please log in to access the dashboard.",
                "warning"
            )

            return redirect(url_for("auth.login"))

        return function(*args, **kwargs)

    return decorated_function


# ==========================================
# EMPLOYEE DASHBOARD
# ==========================================

@app.route("/")
@login_required
def index():

    search = request.args.get("search", "").strip()

    connection = get_db_connection()

    try:

        # Employee search
        if search:

            employees = connection.execute(
                """
                SELECT *
                FROM employees
                WHERE name LIKE ?
                   OR email LIKE ?
                   OR department LIKE ?
                ORDER BY id DESC
                """,
                (
                    f"%{search}%",
                    f"%{search}%",
                    f"%{search}%"
                )
            ).fetchall()

        else:

            employees = connection.execute(
                """
                SELECT *
                FROM employees
                ORDER BY id DESC
                """
            ).fetchall()

        # Total employees
        total_employees = connection.execute(
            "SELECT COUNT(*) FROM employees"
        ).fetchone()[0]

        # Total departments
        total_departments = connection.execute(
            """
            SELECT COUNT(DISTINCT department)
            FROM employees
            """
        ).fetchone()[0]

        # Average salary
        average_salary = connection.execute(
            """
            SELECT COALESCE(AVG(salary), 0)
            FROM employees
            """
        ).fetchone()[0]

        # Total monthly payroll
        total_payroll = connection.execute(
            """
            SELECT COALESCE(SUM(salary), 0)
            FROM employees
            """
        ).fetchone()[0]

        # Department-wise employee statistics
        department_stats = connection.execute(
            """
            SELECT
                department,
                COUNT(*) AS employee_count
            FROM employees
            GROUP BY department
            ORDER BY employee_count DESC
            """
        ).fetchall()

        # Convert SQLite Row objects into dictionaries for JSON
        department_stats = [
            dict(row) for row in department_stats
        ]

        # Recent employees
        recent_employees = connection.execute(
            """
            SELECT *
            FROM employees
            ORDER BY id DESC
            LIMIT 5
            """
        ).fetchall()

    finally:

        connection.close()

    return render_template(
        "index.html",

        employees=employees,

        total_employees=total_employees,

        total_departments=total_departments,

        average_salary=average_salary,

        total_payroll=total_payroll,

        department_stats=department_stats,

        recent_employees=recent_employees,

        search=search
    )


# ==========================================
# ADD EMPLOYEE
# ==========================================

@app.route("/add", methods=["POST"])
@login_required
def add_employee():

    name = request.form.get(
        "name", ""
    ).strip()

    email = request.form.get(
        "email", ""
    ).strip().lower()

    department = request.form.get(
        "department", ""
    ).strip()

    try:

        salary = float(
            request.form.get("salary", "")
        )

        if (
            not name
            or not email
            or not department
            or salary < 0
        ):

            raise ValueError

        connection = get_db_connection()

        try:

            connection.execute(
                """
                INSERT INTO employees
                (name, email, department, salary)
                VALUES (?, ?, ?, ?)
                """,
                (
                    name,
                    email,
                    department,
                    salary
                )
            )

            connection.commit()

        finally:

            connection.close()

        flash(
            "Employee added successfully!",
            "success"
        )

    except ValueError:

        flash(
            "Please enter valid employee details.",
            "danger"
        )

    except Exception:

        flash(
            "Email already exists or an error occurred.",
            "danger"
        )

    return redirect(url_for("index"))


# ==========================================
# EDIT EMPLOYEE
# ==========================================

@app.route(
    "/edit/<int:employee_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_employee(employee_id):

    connection = get_db_connection()

    try:

        employee = connection.execute(
            """
            SELECT *
            FROM employees
            WHERE id = ?
            """,
            (employee_id,)
        ).fetchone()

        if employee is None:

            flash(
                "Employee not found.",
                "danger"
            )

            return redirect(url_for("index"))

        if request.method == "POST":

            name = request.form.get(
                "name", ""
            ).strip()

            email = request.form.get(
                "email", ""
            ).strip().lower()

            department = request.form.get(
                "department", ""
            ).strip()

            try:

                salary = float(
                    request.form.get("salary", "")
                )

                if (
                    not name
                    or not email
                    or not department
                    or salary < 0
                ):

                    raise ValueError

                connection.execute(
                    """
                    UPDATE employees

                    SET
                        name = ?,
                        email = ?,
                        department = ?,
                        salary = ?

                    WHERE id = ?
                    """,
                    (
                        name,
                        email,
                        department,
                        salary,
                        employee_id
                    )
                )

                connection.commit()

                flash(
                    "Employee updated successfully!",
                    "success"
                )

                return redirect(url_for("index"))

            except ValueError:

                flash(
                    "Please enter valid employee details.",
                    "danger"
                )

            except Exception:

                flash(
                    "Email already exists or an error occurred.",
                    "danger"
                )

    finally:

        connection.close()

    return render_template(
        "edit_employee.html",
        employee=employee
    )


# ==========================================
# DELETE EMPLOYEE
# ==========================================

@app.route(
    "/delete/<int:employee_id>",
    methods=["POST"]
)
@login_required
def delete_employee(employee_id):

    connection = get_db_connection()

    try:

        connection.execute(
            """
            DELETE FROM employees
            WHERE id = ?
            """,
            (employee_id,)
        )

        connection.commit()

    finally:

        connection.close()

    flash(
        "Employee deleted successfully!",
        "success"
    )

    return redirect(url_for("index"))


# ==========================================
# HEALTH CHECK
# ==========================================

@app.route("/health")
def health():

    return {
        "status": "healthy",
        "application": "HR Portal",
        "message": "Application is running successfully"
    }, 200


# ==========================================
# APPLICATION START
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
