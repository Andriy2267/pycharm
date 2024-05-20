import pyodbc
from flask import Flask, session, render_template, request, redirect, url_for

app = Flask(__name__)
app.secret_key = "My secret key"
global my_connection, my_cursor, my_cursor1


@app.route("/")
def index():
    session.clear()
    return render_template('index.html')


@app.route('/connection_to_db', methods=['GET', 'POST'])
def connection_to_db():
    global my_connection, my_cursor, my_cursor1
    try:
        my_connection = pyodbc.connect('Driver={SQL Server};'
                                        'Server=WIN-N0S9BV6L2D6\SQLEXPRESS;'
                                        'Database=Kryshtop;'
                                        'UID=' + request.form["log"] + ';'
                                        'PWD=' + request.form["pwd"])
    except Exception:
        return render_template("index.html",
                               message='Wrong login or password. If you have not account, refer to crew administrator')
    else:
        my_cursor = my_connection.cursor()
        my_cursor1 = my_connection.cursor()
        my_cursor.execute("EXECUTE All_RoleByEmployeeId " + request.form["id"])
        role_id = my_cursor.fetchall()[0][0]
        if role_id:
            session['employee_id'] = request.form['id']
            session['role_id'] = role_id
            return actions()
        else:
            my_connection.close()
            return render_template("index.html", message='You are not registered. Please refer to the crew administrator.')


@app.route('/actions', methods=['GET', 'POST'])
def actions():
    if session['role_id'] == 1:
        return cm_form('Choose options and press Submit')
    elif session['role_id'] == 2:
        return render_template('ca_list_request.html')
    elif session['role_id'] in (3, 4):
        return render_template('flights_request.html')
    else:
        return render_template("index.html", message='Your role not defined. Refer to crew administrator')


def if_empty_will_be_null(string_for_check):
    return 'null' if string_for_check == '' else "'" + string_for_check + "'"


@app.route('/ca_list_request')
def ca_list_request():
    if 'f_id' in session:
        f_id = if_empty_will_be_null(session['f_id'])
        f_phone = if_empty_will_be_null(session['f_phone'])
        sql = "EXECUTE CA_ListCrewRequest " + f_id + "," + f_phone + ",'" + session['f_description'] +  "','" + \
            session['f_address'] + "'"
        my_cursor.execute(sql)
        rows = my_cursor.fetchall()
        return render_template('ca_list_request.html', rows=rows, f_id=session['f_id'], f_phone=session['f_phone'],
                               f_description=session['f_description'], f_address=session['f_address'])
    else:
        return render_template('ca_list_request', rows=None) #rows


@app.route('/ca_list_processing', methods=['POST', 'GET'])
def ca_list_processing():
    if 'exit' in request.form:
        return index()
    elif 'add' in request.form:
        current_id = request.form['newid']
        sql = 'SET NOCOUNT ON; EXECUTE CA_insertCrew %s' % current_id
        my_cursor.execute(sql)
        message = my_cursor.fetchall()
        my_cursor.commit()
    elif 'submit' in request.form:
        if 'f_id' in session:
            session.pop('f_id', None)
            session.pop('f_phone', None)
            session.pop('f_description', None)
            session.pop('f_address', None)
    session['f_id'], session['f_phone'], session['f_description'], session['f_address'] = \
        request.form['employee_id'], request.form['phone'], request.form['description'], request.form['address']
    return ca_list_request()


@app.route('/ca_form', methods=['POST' , 'GET'])
def ca_form():
    if 'employee_id' in session:
        emp_id = request.args.get('id', '')
        my_cursor.execute("EXECUTE CA_FormCrewRequest " + str(emp_id))
        row = my_cursor.fetchall()[0]
        return render_template('ca_form.html', row=row)


@app.route('/ca_form_processing', methods=['POST','GET'])
def ca_form_processing():
    response = ''
    current_id = request.form['id']
    if 'dismiss' in request.form:
        sql = 'SET NOCOUNT ON; EXECUTE CA_DismissCrew ' + current_id
    elif 'submit' in request.form:
        sql = 'SET NOCOUNT ON; EXECUTE CA_EditCrew ' + current_id + ",'" + request.form['description'] + \
            "','" + request.form['address'] + "','" + request.form['email'] + "','" + request.form['phone'] + "'"
    if 'exit' not in request.form:
        my_cursor.execute(sql)
        response = my_cursor.fetchall()[0][0]
        my_cursor.commit()
    return render_template('ca_list_request.html', f_id=session['f_id'], f_phone=session['f_phone'],
                            f_description=session['f_description'], f_address=session['f_address'], message=response)


@app.route('/flights_request')
def flights_request():
    if 'f_description' in session:
        f_dep_from = if_empty_will_be_null(session['f_dep_from'])
        f_dep_to = if_empty_will_be_null(session['f_dep_to'])
        f_arr_from = if_empty_will_be_null(session['f_arr_from'])
        f_arr_to = if_empty_will_be_null(session['f_arr_to'])
        sql = "EXECUTE FA_ListFlightsRequest '" + session['f_description'] + "', " + f_dep_from + ',' + \
              f_dep_to + ',' + f_arr_from + ',' + f_arr_to
        my_cursor.execute(sql)
        rows = my_cursor.fetchall()
        return render_template('flights_request.html', rows=rows, f_description=session['f_description'],
                               f_dep_from=session['f_dep_from'], f_dep_to=session['f_dep_to'],
                               f_arr_from=session['f_arr_from'], f_arr_to=session['f_arr_to'])
    else:
        return render_template('flights_request.html')


@app.route('/flights_processing', methods=['POST', 'GET'])
def flights_processing():
    if 'exit' in request.form:
        return index()
    if 'f_description' in session:
        session.pop('f_description', None)
        session.pop('f_dep_from', None)
        session.pop('f_dep_to', None)
        session.pop('f_arr_from', None)
        session.pop('f_arr_to', None)
    session['f_description'] = request.form['description']
    session['f_dep_from'] = request.form['dep_from']
    session['f_dep_to'] = request.form['dep_to']
    session['f_arr_from'] = request.form['arr_from']
    session['f_arr_to'] = request.form['arr_to']
    return flights_request()


@app.route('/fa_form')
def fa_form():
    if 'employee_id' in session:
        flight_id = request.args.get('id', '')
        my_cursor.execute("SET NOCOUNT ON; EXECUTE FA_FormFlightRequest " + str(flight_id))
        row = my_cursor.fetchone()
        my_cursor.execute("SET NOCOUNT ON; EXECUTE FA_CrewListForAssignments")
        crewRows = my_cursor.fetchall()
        my_cursor.execute("SET NOCOUNT ON; EXECUTE FA_CrewAssignmentsForFlight " + str(flight_id))
        assignments = my_cursor.fetchall()
        return render_template('fa_form.html', row=row, crewRows=crewRows, assignments=assignments)


@app.route('/fa_form_processing', methods=['POST','GET'])
def fa_form_processing():
    current_id = request.form['id']
    if 'exit' in request.form:
        return flights_request()
    elif 'delete' in request.form:
        sql = 'SET NOCOUNT ON; EXECUTE FA_CancelFlight ' + current_id
    elif 'save' in request.form:
        sql = 'SET NOCOUNT ON; EXECUTE FA_EditFlight ' + current_id + ",'" + request.form['description'] + \
            "','" + request.form['departure_time'] + "','" + request.form['arrival_time'] + "'"
    elif 'assign' in request.form:
        sql = 'SET NOCOUNT ON; EXECUTE FA_AppointCrewForFlight ' + current_id + "," + \
            if_empty_will_be_null(request.form['crew_assign'])
    elif 'revoke' in request.form:
        sql = 'SET NOCOUNT ON; EXECUTE FA_CancelAppointCrewForFlight ' + current_id + "," + \
            if_empty_will_be_null(request.form['crew_revoke'])
    elif 'approve' in request.form:
        sql = 'SET NOCOUNT ON; EXECUTE FA_ApproveAssignmentsForFlight ' + current_id
    elif 'delivering' in request.form:
        sql = 'SET NOCOUNT ON; EXECUTE FA_CreateDeliveringForFlight ' + current_id
    else:
        sql = ''
    my_cursor.execute(sql)
    response = my_cursor.fetchone()
    my_cursor.commit()
    row = my_cursor.execute("SET NOCOUNT ON; EXECUTE FA_FormFlightRequest " + current_id).fetchone()
    my_cursor.execute("SET NOCOUNT ON; EXECUTE FA_CrewListForAssignments ")
    crewrows = my_cursor.fetchall()
    my_cursor.execute("SET NOCOUNT ON; EXECUTE FA_CrewAssignmentsForFlight " + str(current_id))
    assignments = my_cursor.fetchall()
    return render_template('fa_form.html', row=row, crewrows=crewrows,
                           response=response[0], assignments=assignments)


@app.route('/cm_form')
def cm_form(response):
    if 'employee_id' in session:
        my_cursor.execute("EXECUTE CM_DeliveringRequest " + str(session['employee_id']))
        rows = my_cursor.fetchall()
        return render_template('cm_form.html', rows=rows, message=rows[0][0])


@app.route('/cm_form_processing', methods=['POST','GET'])
def cm_form_processing():
    if 'exit' in request.form:
        return index()
    departure = '1' if 'departure' in request.form else '2'
    arrive = '1' if 'arrive' in request.form else '2'
    my_cursor.execute("SET NOCOUNT ON; EXECUTE CM_SendCheck " + str(session["employee_id"]) + ',' + departure + ',' + arrive)
    response = my_cursor.fetchone()[0]
    my_cursor.commit()
    return cm_form(response)


@app.route('/ta_form')
def ta_form():
    flight_id = request.args.get('id', '')
    if flight_id:
        my_cursor.execute("EXECUTE TA_CreateTripPoints ?", flight_id)
        my_cursor.execute("EXECUTE TA_TripPointsRequest ?", flight_id)
        rows = my_cursor.fetchall()
        if len(rows) > 1:
            return render_template('ta_form.html', flight=flight_id, rows=rows)
        else:
            return render_template('ta_form.html', flight=flight_id, rows=[], message=rows[0][0])
    return render_template('index.html')


@app.route('/ta_form_processing', methods=['POST'])
def ta_form_processing():
    message = 'No changes saved.'
    flight_id = request.form['id']
    if 'exit' in request.form:
        return flights_request()
    rows = my_cursor.execute("EXECUTE TA_TripPointsRequest ?", flight_id).fetchall()
    for row in rows:
        if 'time' + str(row[0]) in request.form:
            my_cursor.execute("EXECUTE TA_EditTripPoint ?, ?", row[0], request.form['time' + str(row[0])]).commit
            if my_cursor.rowcount != 0:
                message = 'Data saved.'
                rows = my_cursor.execute('EXECUTE TA_TripPointsRequest ?', flight_id).fetchall()
    return render_template('ta_form.html', flight=flight_id, rows=rows, message=message)


if __name__ == 'main':
    app.run()


