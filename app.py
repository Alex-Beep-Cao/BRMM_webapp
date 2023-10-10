from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
import re
from datetime import datetime
import mysql.connector
from mysql.connector import FieldType
import connect

app = Flask(__name__)

dbconn = None
connection = None


def getCursor():
    global dbconn
    global connection
    connection = mysql.connector.connect(user=connect.dbuser,
                                         password=connect.dbpass, host=connect.dbhost,
                                         database=connect.dbname, autocommit=True)
    dbconn = connection.cursor()
    return dbconn


@app.route("/")
def home():
    return render_template("base.html")


@app.route("/listdrivers")
def listdrivers():
    connection = getCursor()
    connection.execute(
        "SELECT * FROM driver d left join car c on d.car = c.car_num;")
    driverList = connection.fetchall()

    return render_template("driverlist.html", driver_list=driverList)


@app.route("/listcourses")
def listcourses():
    connection = getCursor()
    connection.execute("SELECT * FROM course;")
    courseList = connection.fetchall()
    return render_template("courselist.html", course_list=courseList)


@app.route("/listruns")
@app.route("/listruns/<driverid>")
def listruns(driverid=None):
    connection = getCursor()
    if (driverid):
        query = (
            "SELECT r.dr_id, CONCAT(first_name, ' ' ,surname), c.model, c.drive_class, r.crs_id, r.run_num, r.seconds, r.cones, r.wd, CAST(r.seconds AS DECIMAL(10, 2)) + COALESCE(CAST(r.cones AS SIGNED), 0) * 5 + CAST(r.wd AS SIGNED ) * 10 FROM run r inner join driver d on r.dr_id = d.driver_id left join car c on d.car = c.car_num left join course co on co.course_id = r.crs_id WHERE r.dr_id = %s;"
        )
        connection.execute(query, (driverid,))
        runList = connection.fetchall()
    else:
        query = (
            "SELECT r.dr_id, CONCAT(first_name, ' ' ,surname), c.model, c.drive_class, r.crs_id, r.run_num, r.seconds, r.cones, r.wd, CAST(r.seconds AS DECIMAL(10, 2)) + COALESCE(CAST(r.cones AS SIGNED), 0) * 5 + CAST(r.wd AS SIGNED ) * 10 FROM run r inner join driver d on r.dr_id = d.driver_id left join car c on d.car = c.car_num left join course co on co.course_id = r.crs_id;"
        )
        connection.execute(query,)
        runList = connection.fetchall()

    connection.execute(
        "SELECT driver_id, CONCAT(first_name, ' ' ,surname) FROM driver;")
    driverNameList = connection.fetchall()
    return render_template("runlist.html", run_list=runList, driver_name_list=driverNameList)


@app.route("/overallresult")
def overallresult():
    connection = getCursor()

    query = ("SELECT re.dr_id, re.crs_id, MIN(re.RunTotal), CASE WHEN CAST(d1.age AS SIGNED) >= 12 AND CAST(d1.age AS SIGNED) <= 25 THEN CONCAT(d1.first_name, ' ' ,d1.surname, ' (J)') ELSE CONCAT(d1.first_name, ' ' ,d1.surname) END As name, c1.model FROM "
             "(SELECT r.dr_id, r.crs_id, COALESCE(CAST(r.seconds AS DECIMAL(10, 2)) + "
             "COALESCE(CAST(r.cones AS SIGNED), 0) * 5 + CAST(r.wd AS SIGNED) * 10, 'dnf') AS RunTotal "
             "FROM run r "
             "INNER JOIN driver d ON r.dr_id = d.driver_id "
             "LEFT JOIN car c ON d.car = c.car_num LEFT JOIN course co ON co.course_id = r.crs_id) AS re "
             "LEFT JOIN driver d1 ON re.dr_id = d1.driver_id "
             "LEFT JOIN car c1 ON d1.car = c1.car_num "
             "GROUP BY re.dr_id, re.crs_id")

    connection.execute(query)
    courseTimeList = connection.fetchall()
    sortedList = getOverAllData(courseTimeList)

    return render_template("overallresult.html", course_time_list=courseTimeList, display_result=sortedList)


@app.route("/graph")
def showgraph():

    # Insert code to get top 5 drivers overall, ordered by their final results.
    # Use that to construct 2 lists: bestDriverList containing the names, resultsList containing the final result values
    # Names should include their ID and a trailing space, eg '133 Oliver Ngatai '
    connection = getCursor()

    query = ("SELECT re.dr_id, re.crs_id, MIN(re.RunTotal), CASE WHEN CAST(d1.age AS SIGNED) >= 12 AND CAST(d1.age AS SIGNED) <= 25 THEN CONCAT(d1.first_name, ' ' ,d1.surname, ' (J)') ELSE CONCAT(d1.first_name, ' ' ,d1.surname) END As name, c1.model FROM "
             "(SELECT r.dr_id, r.crs_id, COALESCE(CAST(r.seconds AS DECIMAL(10, 2)) + "
             "COALESCE(CAST(r.cones AS SIGNED), 0) * 5 + CAST(r.wd AS SIGNED) * 10, 'dnf') AS RunTotal "
             "FROM run r "
             "INNER JOIN driver d ON r.dr_id = d.driver_id "
             "LEFT JOIN car c ON d.car = c.car_num LEFT JOIN course co ON co.course_id = r.crs_id) AS re "
             "LEFT JOIN driver d1 ON re.dr_id = d1.driver_id "
             "LEFT JOIN car c1 ON d1.car = c1.car_num "
             "GROUP BY re.dr_id, re.crs_id")

    connection.execute(query)
    courseTimeList = connection.fetchall()
    sortedList = getOverAllData(courseTimeList)
    sortedList = sortedList[:5]
    resultsList = [item[1] for item in sortedList]
    bestDriverList = [item[2] for item in sortedList]

    return render_template("top5graph.html", name_list=bestDriverList, value_list=resultsList)


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/listjuniordrivers")
def listjuniordrivers():
    connection = getCursor()
    connection.execute("SELECT d.driver_id, d.age, CONCAT(d.first_name, ' ' ,d.surname) AS driver_name, CONCAT(d1.first_name, ' ' ,d1.surname) AS caregiver_name "
                       "FROM driver d LEFT JOIN driver d1 "
                       "ON d.caregiver = d1.driver_id "
                       "WHERE d.age >= 12 and d.age <= 25 "
                       "ORDER BY d.age desc, d.surname asc;")
    juniordriverList = connection.fetchall()

    return render_template("juniordriverlist.html", junior_driver_list=juniordriverList)


@app.route('/search', methods=['GET', 'POST'])
def search():
    result = []
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        connection = getCursor()
        # Example:
        connection.execute("SELECT *  FROM driver WHERE first_name LIKE %s or surname LIKE %s;",
                           ('%' + search_query + '%', '%' + search_query + '%',))
        result = connection.fetchall()

    return render_template('search.html', result_driver=result)


@app.route('/update', methods=['GET', 'POST'])
@app.route("/update/<searchelement>")
def update(searchelement=None):
    if request.method == 'GET':
        connection = getCursor()
        if (searchelement):
            query = (
                "SELECT r.dr_id, CONCAT(first_name, ' ' ,surname) AS fullname, r.crs_id, r.run_num, r.seconds, r.cones, r.wd FROM run r inner join driver d on r.dr_id = d.driver_id left join course co on co.course_id = r.crs_id WHERE r.dr_id = %s or r.crs_id =%s;"
            )
            connection.execute(query, (searchelement, searchelement))
            runList = connection.fetchall()
        else:
            query = (
                "SELECT r.dr_id, CONCAT(first_name, ' ' ,surname) AS fullname, r.crs_id, r.run_num, r.seconds, r.cones, r.wd FROM run r inner join driver d on r.dr_id = d.driver_id left join course co on co.course_id = r.crs_id;"
            )
            connection.execute(query,)
            runList = connection.fetchall()

        # Get driverNameList
        connection.execute(
            "SELECT driver_id, CONCAT(first_name, ' ' ,surname) FROM driver;")
        driverNameList = connection.fetchall()

        connection.execute(
            "SELECT course_id FROM course;")
        courseList = connection.fetchall()

        return render_template("update.html", run_list=runList, driver_name_list=driverNameList, course_list=courseList)
   
    elif  request.method == 'POST':
        result = []
        query = ""
        selected_driver = request.form.get('selected_driver')
        selected_course = request.form.get('selected_course')
        selected_run_num = request.form.get('selected_run_num')
        time = request.form.get('time')
        cone = request.form.get('cone')
        wd = request.form.get('wd')

        try:
            validateCheck(time, cone, wd)
        except ValueError:
            errorMessage = "Value Error."
            return render_template('error.html', error_message = errorMessage )

        # If time, cone, wd are all empty means no need to update
        if (time != ""):
            query = query + "seconds =" + time + ", "
        if (cone != ""):
            query = query + "cones =" + cone + ", "
        if (wd != ""):
            query = query + "wd = " + wd + ", "

        if query != "":
            query = query.strip()[:-1]
        else:
            errorMessage = "Please enter at least one value for Time, Cones and Wd."
            return render_template('error.html', error_message = errorMessage)

        connection = getCursor()
        try:
            updateQuery =(
                "UPDATE run SET " + query + " WHERE dr_id = %s and crs_id = %s and run_num = %s;"
            )
            connection.execute(updateQuery,(selected_driver, selected_course, selected_run_num))

            connection.execute("SELECT r.dr_id, CONCAT(first_name, ' ' ,surname) AS fullname, r.crs_id, r.run_num, r.seconds, r.cones, r.wd FROM run r INNER JOIN driver d ON r.dr_id = d.driver_id LEFT JOIN course co ON co.course_id = r.crs_id WHERE r.dr_id = %s AND r.crs_id = %s AND r.run_num = %s;", (selected_driver, selected_course, selected_run_num))
            updatedData = connection.fetchall()

            Message =" Update Successfully."
            return render_template('success.html', message = Message, update_data = updatedData)
        except:
            errorMessage ="Error during updating the table."
            return render_template('error.html', error_message = errorMessage)
    
    
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'GET':
        connection = getCursor()
        connection.execute(
            "SELECT driver_id, CONCAT(first_name, ' ' ,surname) FROM driver WHERE age > 25 or age is NUll;")
        caregiverList = connection.fetchall() 

        connection.execute(
            "SELECT car_num, model, drive_class FROM car;")
        carList = connection.fetchall()

        return render_template('addnewdriver.html',car_list = carList, caregiver_list= caregiverList)   

    elif request.method == 'POST':
        # Add in table driver
        # Validate AGE format INT, cannot be float or string
        # Normal Age 
        # Return TypeError - error page
        # Return DB Error - error page

        # Junior 12-25 
        # Validate AGE format INT, cannot be float or string
        # Return TypeError - error page 
        # Return AGE (12-25)but no DOB Error- error page
        # Return AGE Not Match with DOB Error - error page
        # Return No caregiver (<= 16) Error - error page
        # Return DB Error - error page

        # Driver id += 1

        # Add in table run
        # Check existing Driver using dr_id
        # Add run 2*7 = 14 with value NULL
        # DB Error
        
        
        Message =" Add Successfully."
        return render_template('success.html', message = Message, update_data = updatedData) 

def validateCheck(time, cone, wd):
    # Validate data type
    # Validate time
    if (validateEmpty(time)):
        if (validateFloatType(time)):
            time=round(float(time), 2)
            if (time >= 20 and time <= 200):
                return True
                
    # Validate Cone
    if (validateEmpty(cone)):
        if (validateIntType(cone)):
            cone=int(cone)
            if (cone >= 0 or cone <= 15):
                return True

     # Validate Wd
    if (validateEmpty(wd)):
        if (validateIntType(wd)):
            wd=int(wd)
            if (wd == 0 or wd == 1):
                return True

    return False

def validateEmpty(value):
    if value == "":
        return False
    return True


def validateFloatType(value):
    try:
        value=float(value)
        return True
    except ValueError:
        return False


def validateIntType(value):
    try:
        value=int(value)
        return True
    except ValueError:
        return False


def getOverAllData(courseTimeList):
    overall_result={}
    driver_details={}
    displayResult=[]
    for ele in courseTimeList:
        if ele[0] not in overall_result.keys():
            overall_result[ele[0]]=[]
            overall_result[ele[0]].append(ele[2])
            driver_details[ele[0]]=[]
            driver_details[ele[0]].append(ele[3])
            driver_details[ele[0]].append(ele[4])
        else:
            overall_result[ele[0]].append(ele[2])

    for key, value in overall_result.items():
        item=[]
        if 'dnf' in value:
            item.append(key)
            item.append('NQ')
            item=item + driver_details[key]
            displayResult.append(item)
        else:
            value_list=list(map(float, value))
            item.append(key)
            item.append(round(sum(value_list), 2))
            item=item + driver_details[key]
            displayResult.append(item)
    sortedList=sorted(displayResult, key=lambda x: (
        x[1], x[0]) if isinstance(x[1], float) else (float('inf'), x[0]))
    return sortedList

