from flask import Flask, request, jsonify, make_response, send_from_directory, redirect, render_template
from flask_login import LoginManager, login_required, login_user, logout_user
import flask_login
from flask_user import User
import flask_excel as excel
import socket
import os
import json
import pyrebase
import requests

SERVER_HOSTNAME = socket.gethostname()
SERVER_IP = socket.gethostbyname(SERVER_HOSTNAME)
PID = str(os.getpid())


print("HTTP Server started on: " + SERVER_HOSTNAME + " with IP: " + SERVER_IP + "\nPID: " + PID)
app = Flask(__name__, static_folder="www/build", template_folder="www/build")
app.secret_key = salt = "jmcaasd3fjajnewj23sfdj"
login_manager = LoginManager()
login_manager.init_app(app)


config = {
  "apiKey": "AIzaSyDzzHN0J3BXGE7GQZwFeIF818iWnwZ5l-4",
  "authDomain": "projectId.firebaseapp.com",
  "databaseURL": "https://easy-attendance-38c39.firebaseio.com",
  "storageBucket": "easy-attendance-38c39.appspot.com",
  "serviceAccount": "easy-attendance.json"
}

email = "fbproject91@gmail.com"
password = "A@jk30821"

firebase = pyrebase.initialize_app(config)
db = firebase.database()



############################################################################


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path.startswith("static") or path.startswith("images") or path.startswith("favicon") or path.startswith("manifest") or path.startswith("robots"):
        if os.path.exists("www/build/" + path):
            return send_from_directory_response('www/build/', path)
    else:
        if check_if_logged_in():
            return redirect("/main", code=302)
        else:
            return send_from_directory_response('www/build', "login.html")


def check_if_logged_in():
    if flask_login.current_user.is_authenticated:
        if flask_login.current_user.is_user():
            return True
    return False


@app.route('/main', methods=['GET'])
@login_required
def main():
    current_user = get_user()
    if current_user.is_admin():
        employees = {}
        users = db.child("Users").get().val()
        for key, user in users.items():
            if current_user.org_key == str(user.get("orgKey", "")):  #check that user is from the same org as the admin
                employees[user.get("ID", "")] = user.get("fName", "") + " " + user.get("lName", "")
        return render_template("main_admin.html", first_name=current_user.first_name.capitalize(), employees=employees)

    return render_template("main.html", first_name=current_user.first_name.capitalize())


@app.route('/generate_report', methods=['POST'])
@login_required
def generate_report():
    user = get_user()
    if user.is_admin():
        try:
            selected_year = request.values["selected_year"]
            selected_month = request.values["selected_month"]
            selected_employee = request.values["selected_employee"]
        except:
            return send_http_response("0", "missing parameters")
        try:
            attendance = db.child("Attendance").order_by_key().equal_to(selected_employee).order_by_key().get().val()[selected_employee]
            month_selected = attendance[selected_year][selected_month]
        except Exception as e: # if month and year weren't found, return
            return send_http_response("0", "Selected year and month wasn't found")

        data_to_send = {"year": selected_year, "month": selected_month, "data": month_selected}
        return send_http_response("1", data_to_send)

    try:
        selected_year = request.values["selected_year"]
        selected_month = request.values["selected_month"]
    except:
        return send_http_response("0", "missing parameters")

    try:
        attendance = db.child("Attendance").order_by_key().equal_to(user.id).order_by_key().get().val()[user.id]
        month_selected = attendance[selected_year][selected_month]
    except Exception as e: # if month and year weren't found, return
        return send_http_response("0", "Selected year and month wasn't found")

    data_to_send = {"year": selected_year, "month": selected_month, "data": month_selected}
    return send_http_response("1", data_to_send)


def export_to_excel(selected_year, selected_month, month_selected):
    data_to_export = {"Year": [], "Month": [], "Day": [], "Entry": [], "Exit": [], "Total": []}
    for day, value in month_selected.items():
        data_to_export["Year"].append(selected_year)
        data_to_export["Month"].append(selected_month)
        data_to_export["Day"].append(day)
        data_to_export["Entry"].append(value.get("entry", ""))
        data_to_export["Exit"].append(value.get("exit", ""))
        data_to_export["Total"].append(value.get("total", ""))

    return data_to_export


@app.route('/download_report', methods=['POST', 'GET'])
@login_required
def download_report():
    if flask_login.current_user.is_admin():
        try:
            selected_year = request.values["selected_year"]
            selected_month = request.values["selected_month"]
            selected_employee = request.values["selected_employee"]
        except:
            return send_http_response("0", "missing parameters")
        try:
            attendance = db.child("Attendance").order_by_key().equal_to(selected_employee).order_by_key().get().val()[selected_employee]
            month_selected = attendance[selected_year][selected_month]
        except Exception as e: # if month and year weren't found, return
            return send_http_response("0", "Selected year and month wasn't found")

        data_to_export = export_to_excel(selected_year, selected_month, month_selected)
        excel.init_excel(app)
        extension_type = "csv"
        filename = selected_employee + "." + extension_type
        return excel.make_response_from_dict(data_to_export, file_type=extension_type, file_name=filename)


    try:
        selected_year = request.values["selected_year"]
        selected_month = request.values["selected_month"]
    except:
        return send_http_response("0", "missing parameters")

    try:
        user = get_user()
        attendance = db.child("Attendance").order_by_key().equal_to(user.id).order_by_key().get().val()[user.id]
        month_selected = attendance[selected_year][selected_month]
    except Exception as e: # if month and year weren't found, return
        return send_http_response("0", "Selected year and month wasn't found")


    data_to_export = export_to_excel(selected_year, selected_month, month_selected)
    excel.init_excel(app)
    extension_type = "csv"
    filename = user.id + "." + extension_type
    return excel.make_response_from_dict(data_to_export, file_type=extension_type, file_name=filename)



#####################################################
# USER MANAGEMENT
#####################################################

@login_manager.user_loader
def user_loader(email):
    user = db.child("Users").order_by_child("email").equal_to(email).get().val()
    if not user:
        return None
    user = user[next(iter(user))] # extracting the first value from the ordered dict
    return User(user["ID"], user["email"], user["fName"], user["lName"], user["hourlyPay"], user["isManager"], user["orgKey"])


@app.route('/login', methods=["POST"])
def login():
    content = request.get_json(silent=True, force=True)
    if content is None:
        return send_http_response("0", "request not json")
    user_name = content["user_name"]
    user_password = content["user_password"]

    ret_code, msg, user = login_from_db(user_name, user_password)
    if ret_code == 2:
        return send_http_response("0", msg)

    flask_login_user = User(user["ID"], user["email"], user["fName"], user["lName"], user["hourlyPay"], user["isManager"], user["orgKey"]) # creating flask-login user instance
    flask_login_user.id = user["email"]
    if login_user(flask_login_user):
        return send_http_response("1", "")
    else:
        return send_http_response("0", "Couldn't login")


@app.route('/logout', methods=['GET'])
@login_required
def log_out_user():
    logout_user()
    return redirect("/", code=302)


def get_user():
    return flask_login.current_user


def login_from_db(email, password):
    auth = firebase.auth()
    user = None
    try:
        user = auth.sign_in_with_email_and_password(email, password)
    except requests.HTTPError as e:
        error = json.loads(e.args[1])
        if error["error"]["message"] == "EMAIL_NOT_FOUND":
            return 2, "Email not found", user
        elif error["error"]["message"] == "INVALID_PASSWORD":
            return 2, "Wrong password entered", user

    user = db.child("Users").order_by_child("email").equal_to(email).get().val()
    if not user:
        return 2, "Email not found", None
    user = user[next(iter(user))] # extracting the first value from the ordered dict
    return 1, "Login successfully", user


def send_http_response(status, extra_data=None):
    #1 == ok,  0 == error
    if extra_data is None:
        extra_data = ""
    response = make_response(jsonify(status=status, extra_data=extra_data))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


def send_from_directory_response(dir_path, file_path):
    response = make_response(send_from_directory(dir_path, file_path))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
