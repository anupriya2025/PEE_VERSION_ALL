import pyodbc

from gui.Core.Recognistion_process.ConfigLoader import ConfigLoader


# from config.configloader import ConfigLoader


class Camera_db():
    def __init__(self):
        self.config = ConfigLoader()
        self.dict_user_data = {
            "i_user_id": "",
            "str_user_name": "",
            "str_email_id": "",
            "str_phone_number": "",
            "str_password": ""
        }
        abcd = self.config.get('database', 'N/A')
        self.dict_db_details = {
            "str_server": abcd.get('server', 'N/A'),
            "str_username": abcd.get('user', 'N/A'),
            "str_password": abcd.get('assword', 'N/A'),
            "str_db_name": abcd.get('db_name', 'N/A'),
            "str_user_table": "user_details",
            "str_vehicle_table": "vehicle_details",
            "str_vehicle_tracking_table": "vehicle_tracking_details",
            "str_event_details_table": "event_details",
            "str_camera_details": "Camera_Details",
            "str_missed_event_details_table": "missed_event_details"
        }
    def fetch_all_Camera_data(self):
        cursor = None
        try:
            connection = pyodbc.connect(f"""DRIVER={{ODBC Driver 17 for SQL Server}};
                                        SERVER={self.dict_db_details["str_server"]};
                                        UID={self.dict_db_details["str_username"]};
                                        PWD={self.dict_db_details["str_password"]}""",
                                        autocommit=True)
            cursor = connection.cursor()
            select_all_query = f"""SELECT * FROM [{self.dict_db_details["str_db_name"]}].[dbo].[{self.dict_db_details["str_camera_details"]}]"""
            cursor.execute(select_all_query)
            rows = cursor.fetchall()

            # Create list of dictionaries properly
            columns = [column[0] for column in cursor.description]
            camera_list = [
                {columns[i]: row[i] for i in range(len(columns))}
                for row in rows
            ]
            return camera_list
        except Exception as e:
            print(f"Error fetching camera data: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
                connection.close()

