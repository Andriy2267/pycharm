import pyodbc
from flask import Flask, render_template, session, request, redirect, url_for

app = Flask(__name__)

app.secret_key = "My secret key"


@app.route('/')
def index():  # put application's code here
    if 'login' in session:
        session.pop('login', None)
        session.pop('password', None)
        session.pop('employee_id', None)
    return render_template('index.html')


@app.route('/actions', methods=['GET', 'POST'])
def actions():
    if  'login' in session:
        cnxn = pyodbc.connect('Driver={SQL Server};' +
                              'server=DESKTOP-K00LQHI\Andriy;' +
                              'DATABASE=Chopek;' +
                              'UID=' + request.form['log'] + ';PWD=' + request.form['pwd'])
        cursor = cnxn.cursor()
        cursor.execute("EXECUTE All_RoleByEmployeeId" + session["employee_id"])
        row = cursor.fetchone()
        if row[0] == 2:
            return render_template('ca_actions.html')
        else:
            return render_template('index.html')
    else:
        session["login"] = request.form['log']
        session["password"] = request.form['pwd']
        session["employee_id"] = request.form['id']
    return redirect(url_for('actions'))


if __name__ == '__main__':
    app.run()
