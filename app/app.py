from flask import Flask, render_template, request, redirect, url_for, flash
from database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = "devops-project-secret"

init_db()


@app.route("/")
def index():
    connection = get_db_connection()

    employees = connection.execute(
        "SELECT * FROM employees ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return render_template("index.html", employees=employees)


@app.route("/add", methods=["POST"])
def add_employee():
    name = request.form["name"].strip()
    email = request.form["email"].strip()
    department = request.form["department"].strip()

    try:
        salary = float(request.form["salary"])

        if not name or not email or not department or salary < 0:
            raise ValueError

        connection = get_db_connection()

        connection.execute(
            """INSERT INTO employees
            (name, email, department, salary)
            VALUES (?, ?, ?, ?)""",
            (name, email, department, salary)
        )

        connection.commit()
        connection.close()

        flash("Employee added successfully!", "success")

    except ValueError:
        flash("Please enter valid employee details.", "danger")

    except Exception:
        flash("Email already exists or an error occurred.", "danger")

    return redirect(url_for("index"))


@app.route("/delete/<int:employee_id>")
def delete_employee(employee_id):
    connection = get_db_connection()

    connection.execute(
        "DELETE FROM employees WHERE id = ?",
        (employee_id,)
    )

    connection.commit()
    connection.close()

    flash("Employee deleted successfully!", "success")

    return redirect(url_for("index"))


@app.route("/health")
def health():
    return {"status": "healthy"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)