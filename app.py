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
        "SELECT * FROM driver d left join car c on d.car = c.car_num order by d.surname, d.first_name;")
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
    runList = []
    connection = getCursor()
    # get run by driver_id
    if (driverid):
        query = (
            "SELECT r.dr_id, CONCAT(first_name, ' ' ,surname), c.model, c.drive_class, co.name, r.run_num, r.seconds, r.cones, r.wd, CAST(r.seconds AS DECIMAL(10, 2)) + COALESCE(CAST(r.cones AS SIGNED), 0) * 5 + CAST(r.wd AS SIGNED ) * 10 FROM run r inner join driver d on r.dr_id = d.driver_id left join car c on d.car = c.car_num left join course co on co.course_id = r.crs_id WHERE r.dr_id = %s;"
        )
        connection.execute(query, (driverid,))
        runList = connection.fetchall()

    # get driver list and dirver id
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
    # pass data into getOverAllData function return sorted list 
    courseTimeList = connection.fetchall()
    sortedList = getOverAllData(courseTimeList)

    return render_template("overallresult.html", course_time_list=courseTimeList, display_result=sortedList)

@app.route("/graph")
def showgraph():

    # Insert code to get top 5 drivers overall, ordered by their final results.
    # Use that to construct 2 lists: bestDriverList containing the names, resultsList containing the final result values
    # Names should include their ID and a trailing space, eg '133 Oliver Ngatai '
    connection = getCursor()
    # get data same as overall result
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
    # only get first 5 element
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
    # get age >=12 and <=25 order by age then surname
    connection.execute("SELECT d.driver_id, CONCAT(d.first_name, ' ' ,d.surname) AS driver_name, d.age, CONCAT(d1.first_name, ' ' ,d1.surname) AS caregiver_name "
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
        # search in first or surname using match
        connection.execute("SELECT driver_id, CONCAT(first_name, ' ' ,surname), date_of_birth, age, caregiver, car FROM driver WHERE first_name LIKE %s or surname LIKE %s;",
                           ('%' + search_query + '%', '%' + search_query + '%',))
        result = connection.fetchall()

    return render_template('search.html', result_driver=result)

@app.route('/update', methods=['GET', 'POST'])
@app.route("/update/<searchelement>")
def update(searchelement=None):
    # able to filter by driver or course
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
        # init
        result = []
        query = ""
        # get data from form
        selected_driver = request.form.get('selected_driver')
        selected_course = request.form.get('selected_course')
        selected_run_num = request.form.get('selected_run_num')
        time = request.form.get('time')
        cone = request.form.get('cone')
        wd = request.form.get('wd')

        try:
            # validate all input
            result = validateCheck(time, cone, wd)
            if (result == False):
                errorMessage = "Value Error."
                return render_template('error.html', error_message = errorMessage )

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
            # update 
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

        connection.execute(
            "SELECT MAX(driver_id) FROM driver;")
        max_driverId = connection.fetchall()

        return render_template('addnewdriver.html',car_list = carList, caregiver_list= caregiverList)   

    elif request.method == 'POST':
        # Add in table driver
        # Gather information
        firstname_entered = request.form.get('firstname')
        surname_entered = request.form.get('surname')
        # age_entered = request.form.get('age')
        birthday_entered = request.form.get('birthday')
        selected_caregiver = request.form.get('selected_caregiver')
        selected_car = request.form.get('selected_car')
        
        courses= ["A","B","C","D","E","F"]
        runs = [1, 2]
        connection = getCursor()
        connection.execute("SELECT MAX(dr_id) FROM run;")
        max_run_driverId = connection.fetchall()[0]
        exist_check_Id = int(max_run_driverId[0])

        #Normal Age older than 25
        if birthday_entered == '' :
            query = "INSERT INTO driver VALUES(NULL, %s, %s, NULL, NULL, NULL, %s);"
            try:
                #Add into driver table
                connection.execute(query,(firstname_entered, surname_entered, selected_car))
                try:
                    connection = getCursor()
                    connection.execute(
                        "SELECT MAX(driver_id) FROM driver;")
                    max_driverId = connection.fetchall()[0]
                    driverId = int(max_driverId[0])
                    # Add in table run
                    if (exist_check_Id < driverId):
                        for course in courses:
                            for run in runs:
                                query = "INSERT INTO run VALUES(%s, %s, %s, NULL, NULL, 0);"
                                values =(driverId, course, run)
                                connection.execute(query, values)
                    # return newly added data
                    addData = createList(driverId, firstname_entered + " " + surname_entered, courses, runs)
                    Message =" Add driver and runs Successfully."
                    return render_template('success.html', message = Message, update_data = addData)
                except:
                    errorMessage ="Error during adding driver's runs into the run table."
                    return render_template('error.html', error_message = errorMessage)
                
            except:
                errorMessage ="Error during adding driver into the driver table."
                return render_template('error.html', error_message = errorMessage) 
        
        else: # Junior 12-25
            dob = datetime.strptime(birthday_entered, "%Y-%m-%d")
            # base is 2023-01-01
            current_date = datetime.strptime('2023-01-01', "%Y-%m-%d")
            age = current_date.year - dob.year - ((current_date.month, current_date.day) < (dob.month, dob.day))

            if validateAge(age) :
                if(age <= 16):
                    # add driver with caregiver
                    if(selected_caregiver != ''):
                        query = "INSERT INTO driver VALUES(NULL, %s, %s, %s, %s, %s, %s);"
                        try:
                            connection.execute(query,(firstname_entered, surname_entered, birthday_entered, age, selected_caregiver,selected_car))
                            # add run for this new driver
                            try:
                                driverId = maxDriverId()
                                addRuns(exist_check_Id, driverId, courses, runs)
                                # return newly added data
                                addData = createList(driverId, firstname_entered + " " + surname_entered, courses, runs)
                                Message =" Add driver and runs Successfully."
                                return render_template('success.html', message = Message, update_data = addData)
                            except:
                                errorMessage ="Error during adding driver's runs into the run table."
                                return render_template('error.html', error_message = errorMessage)
                        except:
                            errorMessage ="Error during adding driver into the driver table."
                            return render_template('error.html', error_message = errorMessage) 
                    else:
                        errorMessage ="You age is under 16, please enter a caregiver."
                        return render_template('error.html', error_message = errorMessage)
                # age > 16
                else:
                    query = "INSERT INTO driver VALUES(NULL, %s, %s, %s, %s, NULL, %s);"
                    try:
                        connection.execute(query,(firstname_entered, surname_entered, birthday_entered, age, selected_car))
                        try:
                            driverId = maxDriverId()
                            addRuns(exist_check_Id, driverId, courses, runs)
                            addData = createList(driverId, firstname_entered + " " + surname_entered, courses, runs)
                            Message =" Add driver and runs Successfully."
                            return render_template('success.html', message = Message, update_data = addData)
                        except:
                            errorMessage ="Error during adding driver's runs into the run table."
                            return render_template('error.html', error_message = errorMessage)
                    except:
                        errorMessage ="Error during adding driver into the driver table."
                        return render_template('error.html', error_message = errorMessage) 
            else:
                errorMessage ="Sorry, you are not able to join the competition."
                return render_template('error.html', error_message = errorMessage) 
        

def validateCheck(time, cone, wd):
    result = []
    # Validate data type
    # Validate time
    if (validateEmpty(time)):
        if (validateFloatType(time)):
            time=round(float(time), 2)
            if (time < 20 and time > 200):
                return False
        else:
            return False
                
    # Validate Cone
    if (validateEmpty(cone)):
        if (validateIntType(cone)):
            cone=int(cone)
            if (cone < 0 or cone > 25):
                return False
        else:
            return False

     # Validate Wd
    if (validateEmpty(wd)):
        if (validateIntType(wd)):
            wd=int(wd)
            if (wd != 0 and wd != 1):
                return False
        else:
            return False
    return True

# check empty
def validateEmpty(value):
    if value == "":
        return False
    return True

# check float tyoe
def validateFloatType(value):
    try:
        value=float(value)
        return True
    except ValueError:
        return False

# check int tyoe
def validateIntType(value):
    try:
        value=int(value)
        return True
    except ValueError:
        return False

# valudate age
def validateAge(value):
    if(int(value) > 100 or int(value) < 12 ):
        return False
    else:
        return True

def getOverAllData(courseTimeList):
    overall_result={}
    driver_details={}
    displayResult=[]
    # loop all course time and pass into a dic, key is driver id
    for ele in courseTimeList:
        if ele[0] not in overall_result.keys():
            overall_result[ele[0]]=[]
            overall_result[ele[0]].append(ele[2])
            # pass dirver details to dirver dict
            driver_details[ele[0]]=[]
            driver_details[ele[0]].append(ele[3])
            driver_details[ele[0]].append(ele[4])
        else:
            overall_result[ele[0]].append(ele[2])

    # loop dict caculate the run time 
    for key, value in overall_result.items():
        item=[]
        # has dnf in the value -> reutrn NQ
        if 'dnf' in value:
            value_list=list(value)
            item.append(key)
            item.append('NQ')
            item=item + driver_details[key] + value_list
            
            displayResult.append(item)
        # caculate sum of the run times
        else:
            # convert string to float
            value_list=list(map(float, value))
            item.append(key)
            item.append(round(sum(value_list), 2))
            item=item + driver_details[key] + value_list
            
            displayResult.append(item)
    # sort list by total seconds and put the NQ at the end     
    sortedList=sorted(displayResult, key=lambda x: (
        x[1], x[0]) if isinstance(x[1], float) else (float('inf'), x[0]))
    return sortedList

# add run into run table
def addRuns (exist_check_Id, driverId, courses, runs):
    connection = getCursor()
    if (exist_check_Id < driverId):
        for course in courses:
            for run in runs:
                query = "INSERT INTO run VALUES(%s, %s, %s, NULL, NULL, 0);"
                values =(driverId, course, run)
                connection.execute(query, values)
    
# create a list for returning newly added data
def createList(id, name, courses, runs):
    result = []
    for course in courses:
        for run in runs:
            item = [id, name, course, run, 'NULL', 'NULL', 0]
            result.append(item)
    return result

# get max driver id
def maxDriverId():
    connection = getCursor()
    connection.execute(
        "SELECT MAX(driver_id) FROM driver;")
    max_driverId = connection.fetchall()[0]
    driverId = int(max_driverId[0])
    return driverId
