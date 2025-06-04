from flask import Flask, render_template, request, redirect, url_for
import sqlite3


app = Flask(__name__)

DB_FILE = 'students.db'

# Initialize database and tables
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(
            "CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)"
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                entry TEXT,
                FOREIGN KEY(student_id) REFERENCES students(id)
            )
            """
        )
        conn.commit()


def get_all_data():
    """Return a dictionary of students with their progress entries."""
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT id, name FROM students")
        students = {}
        for sid, name in c.fetchall():
            c.execute(
                "SELECT entry FROM progress WHERE student_id=?",
                (sid,),
            )
            students[name] = [row[0] for row in c.fetchall()]
        return students


def get_student_names():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM students")
        return [row[0] for row in c.fetchall()]


def add_student_to_db(name):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO students(name) VALUES (?)", (name,))
        conn.commit()


def add_progress_to_db(name, entry):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM students WHERE name=?", (name,))
        row = c.fetchone()
        if row:
            c.execute(
                "INSERT INTO progress(student_id, entry) VALUES (?, ?)",
                (row[0], entry),
            )
            conn.commit()

@app.route('/')
def index():
    students = get_all_data()
    return render_template('index.html', students=students)

@app.route('/student/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        add_student_to_db(name)
        return redirect(url_for('index'))
    return render_template('add_student.html')

@app.route('/progress/add', methods=['GET', 'POST'])
def add_progress():
    students = get_student_names()
    if request.method == 'POST':
        name = request.form['name']
        progress = request.form['progress']
        add_progress_to_db(name, progress)
        return redirect(url_for('index'))
    return render_template('add_progress.html', students=students)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
