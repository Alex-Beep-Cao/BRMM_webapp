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
    print(driverList)
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
            "SELECT r.dr_id, CONCAT(first_name, ' ' ,surname), c.model, c.drive_class, r.crs_id, r.run_num, r.seconds, r.cones, r.wd, CAST(r.seconds AS SIGNED) + COALESCE(CAST(r.cones AS SIGNED), 0) * 5 + CAST(r.wd AS SIGNED ) * 10 FROM run r inner join driver d on r.dr_id = d.driver_id left join car c on d.car = c.car_num left join course co on co.course_id = r.crs_id WHERE r.dr_id = %s;"
        )
        connection.execute(query, (driverid,))
        runList = connection.fetchall()
    else:
        runList = []
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
    overall_result = {}
    driver_details = {}
    displayResult = []
    for ele in courseTimeList:
        if ele[0] not in overall_result.keys():
            overall_result[ele[0]] = []
            driver_details[ele[0]] = []
            driver_details[ele[0]].append(ele[3])
            driver_details[ele[0]].append(ele[4])
        else:
            overall_result[ele[0]].append(ele[2])

    for key, value in overall_result.items():
        item = []
        if 'dnf' in value:
            item.append(key)
            item.append('NQ')
            item = item + driver_details[key]
            displayResult.append(item)
        else:
            value_list = list(map(float, value))
            item.append(key)
            item.append(round(sum(value_list), 2))
            item = item + driver_details[key]
            displayResult.append(item)
    sortedList = sorted(displayResult, key=lambda x: (
        x[1], x[0]) if isinstance(x[1], float) else (float('inf'), x[0]))

    return render_template("overallresult.html", course_time_list=courseTimeList, display_result=sortedList)


@app.route("/graph")
def showgraph():
    connection = getCursor()
    # Insert code to get top 5 drivers overall, ordered by their final results.
    # Use that to construct 2 lists: bestDriverList containing the names, resultsList containing the final result values
    # Names should include their ID and a trailing space, eg '133 Oliver Ngatai '

    return render_template("top5graph.html", name_list=bestDriverList, value_list=resultsList)
