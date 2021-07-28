from flask_login import UserMixin


class User(UserMixin):
    # flask_login_user = User(user["ID"], user["email"], user["fName"], user["lName"], user["hourlyPay"], user["isManager"], user["orgKey"]) # creating flask-login user instance

    def __init__(self, id, email, first_name, last_name, hourly_pay, is_manager, org_key):
        self.id = str(id)
        self.email = str(email)
        self.first_name = str(first_name)
        self.last_name = str(last_name)
        self.hourly_pay = str(hourly_pay)
        self.is_manager = is_manager
        self.org_key = str(org_key)

    def is_admin(self):
        if self.is_manager:
            return True
        return False