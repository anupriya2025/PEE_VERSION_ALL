import threading

from .Recognistion_process.ConfigLoader import ConfigLoader
from .audio import AudioThreadManager
from .authentication import Authentication
from .camera import Camera
# from .vehicle import Vehicle
from .event import Event
import pyodbc
# from config.configloader import ConfigLoader


class Core:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Core, cls).__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self):
        if self.__initialized:
            return  # Prevent re-initialization

        self.config=ConfigLoader()

        self.dict_user_data = {
            "i_user_id": "",
            "str_user_name": "",
            "str_email_id": "",
            "str_phone_number": "",
            "str_password": ""
        }
        abcd=self.config.get('database','N/A')
        self.dict_db_details = {
            "str_server": abcd.get('server','N/A'),
            "str_username": abcd.get('user','N/A'),
            "str_password": abcd.get('password','N/A'),
            "str_db_name": abcd.get('db_name','N/A'),
            "str_user_table": "user_details",
            "str_vehicle_table": "vehicle_details",
            "str_vehicle_tracking_table": "vehicle_tracking_details",
            "str_event_details_table": "event_details",
            "str_camera_details": "Camera_Details",
            # "str_missed_event_details_table": "missed_event_details"
        }

        self.obj_Authentication = Authentication(self.dict_db_details, self.dict_user_data)
        # self.obj_Vehicle = Vehicle(self.dict_db_details, self.dict_user_data)
        self.obj_event = Event(self.dict_db_details, self.dict_user_data)
        self.obj_Camera = Camera(self.dict_db_details, self.dict_user_data)

        if self.check_PPE_database(self.dict_db_details):
            print(f"\nDatabase '{self.dict_db_details["str_db_name"]}' created successfully.")
            if self.check_userdetails_table(self.dict_db_details):
                print(f"\nTable '{self.dict_db_details["str_user_table"]}' created successfully.")
            else:
                print(f"\nTable '{self.dict_db_details["str_user_table"]}' creation failed!")

            # if self.check_vehicles_table(self.dict_db_details):
            #     print(f"\nTable '{self.dict_db_details["str_vehicle_table"]}' created successfully.")
            # else:
            #     print(f"\nTable '{self.dict_db_details["str_vehicle_table"]}' creation failed!")

            if self.check_camera_table(self.dict_db_details):
                print(f"\nTable '{self.dict_db_details["str_camera_details"]}' created successfully.")
            else:
                print(f"\nTable '{self.dict_db_details["str_camera_details"]}' creation failed!")

            # if self.check_missed_vehicle_event_table(self.dict_db_details):
            #     print(f"\nTable '{self.dict_db_details["str_missed_event_details_table"]}' created successfully.")
            # else:
            #     print(f"\nTable '{self.dict_db_details["str_missed_event_details_table"]}' creation failed!")


        #     if self.check_vehicle_event_table(self.dict_db_details):
        #         print(f"\nTable '{self.dict_db_details["str_event_details_table"]}' created successfully.")
        #     else:
        #         print(f"\nTable '{self.dict_db_details["str_event_details_table"]}' creation failed!")
        # else:
        #     print(f"\nDatabase '{self.dict_db_details["str_db_name"]}' creation failed!")

        self.__initialized = True

    def check_PPE_database(self, dict_db_details: dict) -> bool:
        try:
            connection = pyodbc.connect(
                f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={dict_db_details["str_server"]};UID={dict_db_details["str_username"]};PWD={dict_db_details["str_password"]}",
                autocommit=True)
            cursor = connection.cursor()
            cursor.execute(f"SELECT name FROM sys.databases WHERE name = ?", (dict_db_details["str_db_name"]))
            bool_db_exists = cursor.fetchone() is not None

            if not bool_db_exists:
                cursor.execute(f"CREATE DATABASE {dict_db_details["str_db_name"]}")

            cursor.close()
            connection.close()
            return True

        except:
            return False

    def check_userdetails_table(self, dict_db_details: dict) -> bool:
        try:
            connection = pyodbc.connect(
                f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={dict_db_details["str_server"]};UID={dict_db_details["str_username"]};PWD={dict_db_details["str_password"]}",
                autocommit=True)
            cursor = connection.cursor()

            select_db_query = f"USE {dict_db_details['str_db_name']};"
            cursor.execute(select_db_query)

            cursor.execute("""SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?""",
                           (dict_db_details["str_user_table"],))
            bool_table_exists = cursor.fetchone() is not None

            if not bool_table_exists:
                create_query = f"""CREATE TABLE {self.dict_db_details["str_user_table"]} (
                                  User_ID INT PRIMARY KEY IDENTITY(1,1),
                                  User_Name VARCHAR(50) NOT NULL,
                                  Email_ID VARCHAR(50) UNIQUE NOT NULL,
                                  Phone_Number VARCHAR(15) UNIQUE NOT NULL,
                                  Password VARCHAR(255) NOT NULL)
                                """
                cursor.execute(create_query)

                insert_query=   f"""
                                INSERT INTO [dbo].{self.dict_db_details["str_user_table"]}
                                ( [User_Name], [Email_ID], [Phone_Number], [Password]) 
                                VALUES 
                                ( 'admin', 'admin@example.com', '1234567890', 'admin');
                                """
                cursor.execute(insert_query)

            cursor.close()
            connection.close()
            return True

        except:
            return False



   
  
    def check_camera_table(self, dict_db_details: dict) -> bool:
        print("**************************************************************camera tabel")
        try:
            connection = pyodbc.connect(
                f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={dict_db_details["str_server"]};UID={dict_db_details["str_username"]};PWD={dict_db_details["str_password"]}",
                autocommit=True)
            cursor = connection.cursor()

            select_db_query = f"USE {dict_db_details['str_db_name']};"
            cursor.execute(select_db_query)

            cursor.execute("""SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?""",
                           (dict_db_details["str_camera_details"],))
            bool_table_exists = cursor.fetchone() is not None

            if not bool_table_exists:
                create_query = f"""CREATE TABLE {self.dict_db_details["str_camera_details"]} (
                                       Camera_Name varchar(255) PRIMARY KEY,
                                       Camera_direction varchar(7) ,
                                       URL VARCHAR(255) NOT NULL
     								  )"""
                cursor.execute(create_query)

            cursor.close()
            connection.close()
            return True

        except:
            return False