import re
import pyodbc


class Authentication():

    def __init__(self, dict_db_details: dict, dict_user_data: dict):

        super().__init__()

        self.dict_db_details = dict_db_details
        self.dict_user_data = dict_user_data

    # ~~~~~~~~~~~~~~~~~~~~ CHECKING USER ID & PASSWORD ~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def check_signin_credential(self, str_emailid: str, str_password: str) -> dict:
        print(str_emailid,str_password,"******************************************")
        dict_Status = {
            "str_error_msg_heading": "",
            "str_error_msg": ""
        }

        try:
            connection = pyodbc.connect(
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.dict_db_details['str_server']};"
                f"UID={self.dict_db_details['str_username']};"
                f"PWD={self.dict_db_details['str_password']}",
                autocommit=True
            )
            cursor = connection.cursor()

            # Select the correct database
            select_db_query = f"USE {self.dict_db_details['str_db_name']};"
            cursor.execute(select_db_query)

            # Prepare parameterized query
            select_query = (
                f"SELECT * FROM [{self.dict_db_details['str_db_name']}].[dbo].[{self.dict_db_details['str_user_table']}] "
                "WHERE user_name = ?"
            )
            cursor.execute(select_query, str_emailid)

            user_data = cursor.fetchone()

            if user_data:
                if user_data.password != str_password:
                    dict_Status["str_error_msg_heading"] = "Error! Incorrect Password"
                    dict_Status["str_error_msg"] = (
                        "The password that you've entered is incorrect. Please try again."
                    )
                else:
                    self.dict_user_data["i_user_id"] = int(user_data.user_id)
                    self.dict_user_data["str_user_name"] = user_data.user_name
                    self.dict_user_data["str_email_id"] = user_data.email_id
                    self.dict_user_data["str_phone_number"] = user_data.phone_number
                    self.dict_user_data["str_password"] = user_data.password
            else:
                dict_Status["str_error_msg_heading"] = "Error! Account not found"
                dict_Status["str_error_msg"] = (
                    "There is no user registered with the given credentials."
                )

        except Exception as e:
            dict_Status["str_error_msg_heading"] = "Error! Something went wrong"
            dict_Status["str_error_msg"] = (
                "Something went wrong. Please contact the support team."
            )
        finally:
            try:
                cursor.close()
                connection.close()
            except:
                pass

        return dict_Status

    #

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~ ACCOUNT CREATION ~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # def create_account(self, str_username: str, str_email_id: str, str_phone_number: str, str_password: str) -> bool:

    #     dict_constraints = {}
    #     dict_Status = {
    #         "str_error_msg_heading": "",
    #         "str_error_msg": ""
    #     }

    #     try:
    #         connection = pyodbc.connect(
    #             f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.dict_db_details["str_server"]};UID={self.dict_db_details["str_username"]};PWD={self.dict_db_details["str_password"]}",
    #             autocommit=True)
    #         cursor = connection.cursor()

    #         select_db_query = f"USE {self.dict_db_details['str_db_name']};"
    #         cursor.execute(select_db_query)

    #         constraint_query = f"""SELECT tc.CONSTRAINT_NAME, ccu.COLUMN_NAME 
    #                                 FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS tc
    #                                 JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE AS ccu
    #                                 ON tc.CONSTRAINT_NAME = ccu.CONSTRAINT_NAME
    #                                 WHERE tc.TABLE_NAME = '{self.dict_db_details["str_user_table"]}';
    #                             """
    #         cursor.execute(constraint_query)
    #         data = cursor.fetchall()
    #         if data:
    #             for rows in data:
    #                 dict_constraints[f"{rows.COLUMN_NAME}"] = f"{rows.CONSTRAINT_NAME}"

    #         insert_query = f"INSERT INTO [{self.dict_db_details["str_db_name"]}].[dbo].[{self.dict_db_details["str_user_table"]}] (User_Name, Email_ID, Phone_Number, Password) VALUES (?, ?, ?, ?)"
    #         cursor.execute(insert_query, str_username, str_email_id, str_phone_number, str_password)


    #     except pyodbc.Error as e:
    #         if (e.args[0] == '23000' and "duplicate" in e.args[1]):
    #             dict_Status["str_error_msg_heading"] = "Error! Duplicate Entries"
    #             if dict_constraints["email_id"] in e.args[1]:
    #                 dict_Status["str_error_msg"] = "Email ID is already registered. Please enter a different one."
    #             elif dict_constraints["phone_number"] in e.args[1]:
    #                 dict_Status["str_error_msg"] = "Phone number is already registered. Please enter a different one."
    #         else:
    #             dict_Status["str_error_msg_heading"] = "Error! Something went wrong"
    #             dict_Status["str_error_msg"] = "Something went wrong. Please verify the inputs and try again."

    #     except Exception as e:
    #         dict_Status["str_error_msg_heading"] = "Error! Something went wrong"
    #         dict_Status["str_error_msg"] = "Something went wrong. Please contact with support team."

    #     finally:
    #         cursor.close()
    #         connection.close()

    #     return dict_Status

    # def update_details(self, str_username: str, str_pasword: str):
    #     dict_constraints = {}
    #     dict_Status = {
    #         "str_error_msg_heading": "",
    #         "str_error_msg": ""
    #     }

    #     try:
    #         connection = pyodbc.connect(
    #             f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.dict_db_details["str_server"]};UID={self.dict_db_details["str_username"]};PWD={self.dict_db_details["str_password"]}",
    #             autocommit=True)
    #         cursor = connection.cursor()

    #         select_db_query = f"USE {self.dict_db_details['str_db_name']};"
    #         cursor.execute(select_db_query)

    #         constraint_query = f"""SELECT tc.CONSTRAINT_NAME, ccu.COLUMN_NAME 
    #                                 FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS tc
    #                                 JOIN INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE AS ccu
    #                                 ON tc.CONSTRAINT_NAME = ccu.CONSTRAINT_NAME
    #                                 WHERE tc.TABLE_NAME = '{self.dict_db_details["str_user_table"]}';
    #                             """
    #         cursor.execute(constraint_query)
    #         data = cursor.fetchall()
    #         if data:
    #             for rows in data:
    #                 dict_constraints[f"{rows.COLUMN_NAME}"] = f"{rows.CONSTRAINT_NAME}"

    #         query = f"""UPDATE [{self.dict_db_details["str_db_name"]}].[dbo].[{self.dict_db_details["str_user_table"]}] 
    #                     SET User_Name = ?,Password = ? WHERE User_ID = ?"""
    #         cursor.execute(query, str_username, str_pasword, int(self.dict_user_data["i_user_id"]))

    #         self.dict_user_data["str_user_name"] = str_username
    #         # self.dict_user_data["str_phone_number"] = str_pasword
    #         self.dict_user_data["str_password"] = str_pasword

    #     except pyodbc.Error as e:
    #         if (e.args[0] == '23000' and "duplicate" in e.args[1]):
    #             dict_Status["str_error_msg_heading"] = "Error! Duplicate Entries"
    #             if dict_constraints["phone_number"] in e.args[1]:
    #                 dict_Status["str_error_msg"] = "Password is already registered. Please enter a different one."
    #         else:
    #             dict_Status["str_error_msg_heading"] = "Error! Something went wrong"
    #             dict_Status["str_error_msg"] = "Something went wrong. Please verify the inputs and try again."

    #     except Exception as e:
    #         dict_Status["str_error_msg_heading"] = "Error! Something went wrong"
    #         dict_Status["str_error_msg"] = "Something went wrong. Please contact with support team."

    #     finally:
    #         cursor.close()
    #         connection.close()

    #     return dict_Status

    # ~~~~~~~~~~~~~~~~~~~~~~ VALIDATE USER NAME FORMAT~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def validate_user_name(self, str_user_name: str) -> str:

        if len(str_user_name) == 0:
            return "ⓘ Username can't be empty"

        if len(str_user_name) < 3:
            return "ⓘ Must be at least 3 characters long."

        if str_user_name[0].isdigit():
            return "ⓘ Must not start with a number."

        if not re.match(r"^[a-zA-Z ]+$", str_user_name):
            return "ⓘ only [ a-z ], [ A-Z ] are allowed."

        return ""

    # ~~~~~~~~~~~~~~~~~~~~~~ VALIDATE EMAIL ID FORMAT ~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def validate_email(self, str_email: str) -> str:

        regex_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if len(str_email) == 0:
            return "ⓘ Email address can't be empty"

        if (not re.match(regex_pattern, str_email)):
            return "ⓘ Invalid email address"

        return ""

    # ~~~~~~~~~~~~~~~~~~~ VALIDATE MOBILE NUMBER FORMAT ~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def validate_phone_number(self, str_phone_number: str) -> str:

        regex_pattern = r"^(?:\+91\s?)?[6-9]\d{9}$"

        if len(str_phone_number) == 0:
            return "ⓘ Phone number can't be empty"

        if (not re.match(regex_pattern, str_phone_number)):
            return "ⓘ Invalid phone number"

        return ""

    # ~~~~~~~~~~~~~~~~~~~~~~~ VALIDATE PASSWORD FORMAT ~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def validate_password(self, str_password: str) -> str:

        if len(str_password) == 0:
            return "ⓘ Password can't be empty"

        if len(str_password) < 6:
            return "ⓘ Must be at least 6 characters long."

        if not re.search(r"\d", str_password):
            return "ⓘ Must contain a digit (0-9)"

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", str_password):
            return "ⓘ Must contain at least one special symbol (!@#$%^&*)."

        return ""