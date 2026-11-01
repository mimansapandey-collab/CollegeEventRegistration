from flask import Flask, request, redirect, render_template_string
import sqlite3

app = Flask(__name__)

DATABASE = "college_events.db"


# Connect to the database
def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# Create tables and insert sample events
def setup_database():
    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT NOT NULL,
            event_date TEXT NOT NULL,
            venue TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            email TEXT NOT NULL,
            event_id INTEGER NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(event_id)
        )
    """)

    # Add sample events only if the events table is empty
    count = connection.execute(
        "SELECT COUNT(*) FROM events"
    ).fetchone()[0]

    if count == 0:
        connection.executemany("""
            INSERT INTO events (event_name, event_date, venue)
            VALUES (?, ?, ?)
        """, [
            ("Coding Competition", "2026-11-15", "Computer Lab"),
            ("Cultural Fest", "2026-11-20", "College Auditorium"),
            ("Sports Day", "2026-11-25", "College Ground")
        ])

    connection.commit()
    connection.close()


# Main website page
@app.route("/")
def home():
    connection = get_db()

    # SELECT query: display all events
    events = connection.execute("""
        SELECT * FROM events
    """).fetchall()

    # SELECT query: display all student registrations
    registrations = connection.execute("""
        SELECT
            registrations.registration_id,
            registrations.student_name,
            registrations.email,
            events.event_name
        FROM registrations
        JOIN events
        ON registrations.event_id = events.event_id
        ORDER BY registrations.registration_id DESC
    """).fetchall()

    connection.close()

    message = request.args.get("message", "")

    return render_template_string(PAGE,
                                  events=events,
                                  registrations=registrations,
                                  message=message)


# Register a student for an event
@app.route("/register", methods=["POST"])
def register():
    student_name = request.form.get("student_name", "").strip()
    email = request.form.get("email", "").strip()
    event_id = request.form.get("event_id", "")

    if not student_name or not email or not event_id:
        return redirect("/?message=Please+fill+all+fields")

    connection = get_db()

    # Check whether the selected event exists
    event = connection.execute(
        "SELECT event_id FROM events WHERE event_id = ?",
        (event_id,)
    ).fetchone()

    if event is None:
        connection.close()
        return redirect("/?message=Please+select+a+valid+event")

    # INSERT query: save the student registration
    connection.execute("""
        INSERT INTO registrations (student_name, email, event_id)
        VALUES (?, ?, ?)
    """, (student_name, email, event_id))

    connection.commit()
    connection.close()

    return redirect("/?message=Registration+successful")


# Delete a student registration
@app.route("/delete/<int:registration_id>", methods=["POST"])
def delete_registration(registration_id):
    connection = get_db()

    # DELETE query: remove the selected registration
    connection.execute("""
        DELETE FROM registrations
        WHERE registration_id = ?
    """, (registration_id,))

    connection.commit()
    connection.close()

    return redirect("/?message=Registration+deleted")


# Website design (HTML and CSS)
PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>College Event Registration System</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f2f5fa;
            margin: 0;
            padding: 0;
            color: #243047;
        }

        header {
            background: #253b80;
            color: white;
            text-align: center;
            padding: 25px 10px;
        }

        header h1 {
            margin: 0 0 10px;
        }

        .container {
            max-width: 1000px;
            margin: 25px auto;
            padding: 0 15px;
        }

        .card {
            background: white;
            padding: 22px;
            margin-bottom: 22px;
            border-radius: 10px;
            box-shadow: 0 3px 10px #00000012;
        }

        h2 {
            color: #253b80;
        }

        input, select {
            width: 100%;
            box-sizing: border-box;
            padding: 11px;
            margin: 8px 0 15px;
            border: 1px solid #ccd2df;
            border-radius: 5px;
        }

        button {
            background: #253b80;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 5px;
            cursor: pointer;
        }

        button:hover {
            background: #17295f;
        }

        .delete-button {
            background: #c0392b;
        }

        .message {
            background: #e0f5e7;
            color: #176533;
            padding: 12px;
            border-radius: 5px;
            margin-bottom: 18px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }

        th, td {
            padding: 11px;
            border: 1px solid #ddd;
            text-align: left;
        }

        th {
            background: #253b80;
            color: white;
        }

        tr:nth-child(even) {
            background: #f6f7fb;
        }

        .table-wrapper {
            overflow-x: auto;
        }

        footer {
            text-align: center;
            padding: 20px;
            color: #666;
        }
    </style>
</head>

<body>

<header>
    <h1>College Event Registration System</h1>
    <p>Register for college events easily!</p>
</header>

<div class="container">

    {% if message %}
        <div class="message">{{ message }}</div>
    {% endif %}

    <section class="card">
        <h2>Available College Events</h2>

        <div class="table-wrapper">
            <table>
                <tr>
                    <th>Event ID</th>
                    <th>Event Name</th>
                    <th>Date</th>
                    <th>Venue</th>
                </tr>

                {% for event in events %}
                <tr>
                    <td>{{ event['event_id'] }}</td>
                    <td>{{ event['event_name'] }}</td>
                    <td>{{ event['event_date'] }}</td>
                    <td>{{ event['venue'] }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </section>

    <section class="card">
        <h2>Student Registration Form</h2>

        <form action="/register" method="POST">

            <label>Student Name</label>
            <input
                type="text"
                name="student_name"
                placeholder="Enter your full name"
                maxlength="100"
                required
            >

            <label>Email Address</label>
            <input
                type="email"
                name="email"
                placeholder="Enter your email"
                maxlength="150"
                required
            >

            <label>Select Event</label>
            <select name="event_id" required>
                <option value="">Choose an event</option>

                {% for event in events %}
                <option value="{{ event['event_id'] }}">
                    {{ event['event_name'] }}
                </option>
                {% endfor %}

            </select>

            <button type="submit">Register Now</button>
        </form>
    </section>

    <section class="card">
        <h2>Student Registrations</h2>

        <div class="table-wrapper">
            <table>
                <tr>
                    <th>ID</th>
                    <th>Student Name</th>
                    <th>Email</th>
                    <th>Event</th>
                    <th>Action</th>
                </tr>

                {% for student in registrations %}
                <tr>
                    <td>{{ student['registration_id'] }}</td>
                    <td>{{ student['student_name'] }}</td>
                    <td>{{ student['email'] }}</td>
                    <td>{{ student['event_name'] }}</td>
                    <td>
                        <form
                            action="/delete/{{ student['registration_id'] }}"
                            method="POST"
                            onsubmit="return confirm('Delete this registration?');"
                        >
                            <button class="delete-button" type="submit">
                                Delete
                            </button>
                        </form>
                    </td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="5">No registrations yet.</td>
                </tr>
                {% endfor %}

            </table>
        </div>
    </section>

</div>

<footer>
    <p>DBMS PBL Project | College Event Registration System</p>
</footer>

</body>
</html>
"""


# Start the application
if __name__ == "__main__":
    setup_database()
    print("Database is ready!")
    print("Open http://127.0.0.1:5000 in your browser.")
    app.run(debug=True)