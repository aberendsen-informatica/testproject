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
        c.execute(
            "CREATE TABLE IF NOT EXISTS modules (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)"
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS student_modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                module_id INTEGER,
                status TEXT DEFAULT 'open',
                completion_date TEXT,
                FOREIGN KEY(student_id) REFERENCES students(id),
                FOREIGN KEY(module_id) REFERENCES modules(id)
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

def add_module_to_db(name):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO modules(name) VALUES (?)", (name,))
        conn.commit()

def get_module_names():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM modules")
        return [row[0] for row in c.fetchall()]

def assign_module_to_student(student, module):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM students WHERE name=?", (student,))
        sid = c.fetchone()
        c.execute("SELECT id FROM modules WHERE name=?", (module,))
        mid = c.fetchone()
        if sid and mid:
            c.execute(
                "INSERT INTO student_modules(student_id, module_id, status) VALUES (?, ?, 'open')",
                (sid[0], mid[0]),
            )
            conn.commit()

def complete_module(student, module):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM students WHERE name=?", (student,))
        sid = c.fetchone()
        c.execute("SELECT id FROM modules WHERE name=?", (module,))
        mid = c.fetchone()
        if sid and mid:
            c.execute(
                "UPDATE student_modules SET status='done', completion_date=DATE('now') WHERE student_id=? AND module_id=?",
                (sid[0], mid[0]),
            )
            conn.commit()

def get_student_modules():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT id, name FROM students")
        result = {}
        for sid, sname in c.fetchall():
            c.execute(
                """
                SELECT modules.name, student_modules.status, IFNULL(student_modules.completion_date, '')
                FROM student_modules
                JOIN modules ON modules.id = student_modules.module_id
                WHERE student_modules.student_id = ?
                """,
                (sid,),
            )
            result[sname] = [
                {"module": row[0], "status": row[1], "date": row[2]} for row in c.fetchall()
            ]
        return result

@app.route('/')
def index():
    students = get_all_data()
    modules = get_student_modules()
    return render_template('index.html', students=students, modules=modules)

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

@app.route('/module/add', methods=['GET', 'POST'])
def add_module():
    if request.method == 'POST':
        name = request.form['name']
        add_module_to_db(name)
        return redirect(url_for('index'))
    return render_template('add_module.html')

@app.route('/module/assign', methods=['GET', 'POST'])
def assign_module_route():
    students = get_student_names()
    modules = get_module_names()
    if request.method == 'POST':
        student = request.form['student']
        module = request.form['module']
        assign_module_to_student(student, module)
        return redirect(url_for('index'))
    return render_template('assign_module.html', students=students, modules=modules)

@app.route('/module/complete', methods=['GET', 'POST'])
def complete_module_route():
    students = get_student_names()
    modules = get_module_names()
    if request.method == 'POST':
        student = request.form['student']
        module = request.form['module']
        complete_module(student, module)
        return redirect(url_for('index'))
    return render_template('complete_module.html', students=students, modules=modules)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
