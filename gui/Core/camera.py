import json

import pyodbc
import datetime


class Camera():

    def __init__(self, dict_db_details, dict_user_data):

        self.dict_db_details = dict_db_details
        self.dict_user_data = dict_user_data

        super().__init__()

    def add_camera(self, camera_data):
        pass
        # """
        # Adds a new camera's data to the database.
        # :param camera_data: A dictionary containing the camera's details.
        # """
        # cursor = None

        # try:
        #     # Connect to the database
        #     connection = pyodbc.connect(f"""DRIVER={{ODBC Driver 17 for SQL Server}};
        #                                     SERVER={self.dict_db_details["str_server"]};
        #                                     UID={self.dict_db_details["str_username"]};
        #                                     PWD={self.dict_db_details["str_password"]}""",
        #                                 autocommit=True)
        #     cursor = connection.cursor()

        #     # Prepare the query to insert camera data
        #     insert_query = f"""
        #     INSERT INTO [{self.dict_db_details["str_db_name"]}].[dbo].[{self.dict_db_details["str_camera_details"]}]
        #     (Camera_Name, URL, Camera_direction)
        #     VALUES (?, ?, ?, ?, ?,?,?)
        #     """

        #     # Execute the insert query
        #     cursor.execute(insert_query, (
        #         camera_data["Camera_Name"],
        #         camera_data["URL"],
        #         camera_data["Camera_direction"],
        #         15,
        #         90,
        #         15,90
        #     ))

        #     print(f"Camera {camera_data['Camera_Name']} added successfully.")
        #     return True
        # except pyodbc.InterfaceError as e:
        #     # Handle database interface errors (e.g., issues with the connection)
        #     print(f"Database interface error: {e}")
        #     return False
        # except pyodbc.DatabaseError as e:
        #     # Handle database-related errors (e.g., issues with executing the query)
        #     print(f"Database error: {e}")
        #     return False
        # except pyodbc.OperationalError as e:
        #     # Handle operational errors (e.g., issues with connecting to the server)
        #     print(f"Operational error: {e}")
        #     return False
        # except pyodbc.Error as e:
        #     # General pyodbc errors
        #     print(f"SQL execution error: {e}")
        #     return False
        # except KeyError as e:
        #     # Handle missing keys in the camera_data dictionary
        #     print(f"Missing expected field in camera data: {e}")
        #     return False
        # except Exception as e:
        #     # Catch all other exceptions
        #     print(f"An unexpected error occurred: {e}")
        #     return False
        # finally:
        #     # Clean up and close the connection
        #     if cursor:
        #         cursor.close()
        #     if connection:
        #         connection.close()

    def fetch_all_Camera_data(self):
        pass
        # cursor = None
        # try:
        #     connection = pyodbc.connect(f"""DRIVER={{ODBC Driver 17 for SQL Server}};
        #                                 SERVER={self.dict_db_details["str_server"]};
        #                                 UID={self.dict_db_details["str_username"]};
        #                                 PWD={self.dict_db_details["str_password"]}""",
        #                                 autocommit=True)
        #     cursor = connection.cursor()
        #     select_all_query = f"""SELECT * FROM [{self.dict_db_details["str_db_name"]}].[dbo].[{self.dict_db_details["str_camera_details"]}]"""
        #     cursor.execute(select_all_query)
        #     rows = cursor.fetchall()

        #     # Create list of dictionaries properly
        #     columns = [column[0] for column in cursor.description]
        #     camera_list = [
        #         {columns[i]: row[i] for i in range(len(columns))}
        #         for row in rows
        #     ]
        #     return camera_list
        # except Exception as e:
        #     print(f"Error fetching camera data: {e}")
        #     return []
        # finally:
        #     if cursor:
        #         cursor.close()
        #         connection.close()

    def get_camera_count(self):
      
    
        i_data_count = 0

        try:
            connection = pyodbc.connect(f"""DRIVER={{ODBC Driver 17 for SQL Server}};
                                        SERVER={self.dict_db_details["str_server"]};
                                        UID={self.dict_db_details["str_username"]};
                                        PWD={self.dict_db_details["str_password"]}""",
                                        autocommit=True)
            cursor = connection.cursor()
            select_db_query = f"USE {self.dict_db_details['str_db_name']};"
            cursor.execute(select_db_query)

            data_count_query = f"""SELECT COUNT(*) FROM [{self.dict_db_details["str_db_name"]}].[dbo].[{self.dict_db_details["str_camera_details"]}] """
            cursor.execute(data_count_query)
            result = cursor.fetchone()
            i_data_count = int(result[0])

        except Exception as e:
            pass

        finally:
            cursor.close()
            connection.close()

        return i_data_count


    def rtsp_of_camera(self, cameraname):
        pass
       
        # print("camera name = ", cameraname)
        # camera_data = ''
        # cursor = None

        # try:
        #     connection = pyodbc.connect(f"""DRIVER={{ODBC Driver 17 for SQL Server}};
        #                                 SERVER={self.dict_db_details["str_server"]};
        #                                 UID={self.dict_db_details["str_username"]};
        #                                 PWD={self.dict_db_details["str_password"]}""",
        #                                 autocommit=True)
        #     cursor = connection.cursor()
        #     # select_db_query = f"USE {self.dict_db_details['str_db_name']};"
        #     # cursor.execute(select_db_query)
        #     select_all_query = f"""SELECT * FROM [{self.dict_db_details["str_db_name"]}].[dbo].[{self.dict_db_details["str_camera_details"]}] WHERE Camera_Name ='{cameraname}' """
        #     cursor.execute(select_all_query)
        #     camera_data = cursor.fetchone()
        #     if camera_data:
        #         camera_rtsp = f'rtsp://{camera_data[3]}:{camera_data[4]}@{camera_data[1]}/{camera_data[2]}'
        #         print("fetch data = ", camera_rtsp)
        #         return camera_rtsp

        # except Exception as e:
        #     pass

        # finally:
        #     cursor.close()
        #     connection.close()

        # return camera_data

    def update_camera(self, camera_data):
        pass
        # """
        # Updates an existing camera's data in the database.
        # :param camera_data: A dictionary containing the camera's updated details.
        #                     The dictionary must include a unique identifier for the camera (e.g., Camera ID).
        # """
        # cursor = None

        # try:
        #     # Connect to the database
        #     connection = pyodbc.connect(f"""DRIVER={{ODBC Driver 17 for SQL Server}};
        #                                     SERVER={self.dict_db_details["str_server"]};
        #                                     UID={self.dict_db_details["str_username"]};
        #                                     PWD={self.dict_db_details["str_password"]}""",
        #                                 autocommit=True)
        #     cursor = connection.cursor()

        #     # Ensure the camera_data dictionary includes the unique identifier for the camera
        #     if "Camera_Name" not in camera_data:
        #         return False

        #     # Prepare the query to update camera data
        #     update_query = f"""
        #     UPDATE [{self.dict_db_details["str_db_name"]}].[dbo].[{self.dict_db_details["str_camera_details"]}]
        #     SET URL = ?, Camera_direction = ?
        #     WHERE Camera_Name = ?
        #     """

        #     # Execute the update query
        #     cursor.execute(update_query, (
        #         camera_data["URL"],
        #         camera_data["Camera_direction"],
        #         camera_data["Camera_Name"]
        #     ))

        #     return True
        # except pyodbc.InterfaceError as e:
        #     # Handle database interface errors (e.g., issues with the connection)
        #     print(f"Database interface error: {e}")
        #     return False
        # except pyodbc.DatabaseError as e:
        #     # Handle database-related errors (e.g., issues with executing the query)
        #     print(f"Database error: {e}")
        #     return False
        # except pyodbc.OperationalError as e:
        #     # Handle operational errors (e.g., issues with connecting to the server)
        #     print(f"Operational error: {e}")
        #     return False
        # except pyodbc.Error as e:
        #     # General pyodbc errors
        #     print(f"SQL execution error: {e}")
        #     return False
        # except KeyError as e:
        #     # Handle missing keys in the camera_data dictionary
        #     print(f"Missing expected field in camera data: {e}")
        #     return False
        # except Exception as e:
        #     # Catch all other exceptions
        #     print(f"An unexpected error occurred: {e}")
        #     return False
        # finally:
        #     # Clean up and close the connection
        #     if cursor:
        #         cursor.close()
        #     if connection:
        #         connection.close()



    def delete_cameras(self, Camera_Names):
        pass
        # """
        # Deletes multiple cameras from the database.
        # :param Camera_Names: A list of camera names to be deleted.
        # """
        # cursor = None

        # if not Camera_Names:
        #     print("No camera names provided for deletion.")
        #     return False

        # try:
        #     # Connect to the database
        #     connection = pyodbc.connect(f"""DRIVER={{ODBC Driver 17 for SQL Server}};
        #                                     SERVER={self.dict_db_details["str_server"]};
        #                                     UID={self.dict_db_details["str_username"]};
        #                                     PWD={self.dict_db_details["str_password"]}""",
        #                                 autocommit=True)
        #     cursor = connection.cursor()

        #     # Prepare the query to delete camera data
        #     placeholders = ', '.join(['?'] * len(Camera_Names))
        #     delete_query = f"""
        #     DELETE FROM [{self.dict_db_details["str_db_name"]}].[dbo].[{self.dict_db_details["str_camera_details"]}]
        #     WHERE Camera_Name IN ({placeholders})
        #     """

        #     # Execute the delete query
        #     cursor.execute(delete_query, Camera_Names)
        #     deleted_rows = cursor.rowcount  # Check how many rows were deleted

        #     if deleted_rows > 0:
        #         print(f"Deleted {deleted_rows} cameras: {', '.join(Camera_Names)} successfully.")
        #         return True
        #     else:
        #         print("No matching cameras found for deletion.")
        #         return False

        # except pyodbc.InterfaceError as e:
        #     print(f"Database interface error: {e}")
        #     return False
        # except pyodbc.DatabaseError as e:
        #     print(f"Database error: {e}")
        #     return False
        # except pyodbc.OperationalError as e:
        #     print(f"Operational error: {e}")
        #     return False
        # except pyodbc.Error as e:
        #     print(f"SQL execution error: {e}")
        #     return False
        # except Exception as e:
        #     print(f"An unexpected error occurred: {e}")
        #     return False
        # finally:
        #     if cursor:
        #         cursor.close()
        #     if connection:
        #         connection.close()


