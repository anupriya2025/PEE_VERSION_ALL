import re
import pyodbc
from base64 import b64decode
from numpy import frombuffer, uint8
from customtkinter import CTkImage
from cv2 import imdecode, IMREAD_COLOR
from PIL import Image
import datetime


class Event:
    def __init__(self, dict_db_details: dict, dict_user_data: dict):
        self.dict_db_details = dict_db_details
        self.dict_user_data = dict_user_data

    def fetch_events(self, i_start_index: int, dict_filter_criteria: dict):
        list_event = []
        start_date = ""

        try:
            connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.dict_db_details['str_server']};UID={self.dict_db_details['str_username']};PWD={self.dict_db_details['str_password']}"
            connection = pyodbc.connect(connection_string, autocommit=True)
            cursor = connection.cursor()

            select_db_query = f"USE {self.dict_db_details['str_db_name']};"
            cursor.execute(select_db_query)

            # Assume Time is datetime; adjust if string (e.g., DD-MM-YYYY HH:MM:SS)
            if dict_filter_criteria["str_start_Timeperiod"] == "" and dict_filter_criteria["str_end_Timeperiod"] == "":
                query = f"""SELECT Object_Img, Track_Id, Country, Time, Status, Alarm, Acknowledgment_Message, Acknowledgment_Time, Event_Id, Camera_Name, Object_Type
                            FROM [{self.dict_db_details['str_db_name']}].[dbo].[{self.dict_db_details['str_event_details_table']}]
                            ORDER BY Time DESC OFFSET ? ROWS FETCH NEXT 10 ROWS ONLY 
                         """
                print(f"Executing query without filter: {query} with offset {i_start_index}")
                cursor.execute(query, i_start_index)
            else:
                query = f"""SELECT Object_Img, Track_Id, Country, Time, Status, Alarm, Acknowledgment_Message, Acknowledgment_Time, Event_Id, Camera_Name, Object_Type
                            FROM [{self.dict_db_details['str_db_name']}].[dbo].[{self.dict_db_details['str_event_details_table']}]
                            WHERE CAST(Time AS datetime) BETWEEN ? AND ?
                            ORDER BY Time DESC OFFSET ? ROWS FETCH NEXT 10 ROWS ONLY 
                         """
                print(
                    f"Executing query with filter: {query} with params {dict_filter_criteria['str_start_Timeperiod']}, {dict_filter_criteria['str_end_Timeperiod']}, {i_start_index}")
                cursor.execute(query, dict_filter_criteria["str_start_Timeperiod"],
                               dict_filter_criteria["str_end_Timeperiod"],
                               i_start_index)

            response = cursor.fetchall()
            print(f"Fetched {len(response)} records")

            if response:
                columns = [column[0] for column in cursor.description]
                for data in response:
                    record_dict = {columns[i]: data[i] for i in range(len(columns))}
                    record_dict['Time'] = record_dict['Time'].replace(microsecond=0) if isinstance(record_dict['Time'],
                                                                                                   datetime.datetime) else \
                    record_dict['Time']
                    list_event.append(record_dict)

                for data in list_event:
                    if data["Object_Img"] != "N/A":
                        data["Object_Img"] = self.base64_to_cv2mat_or_pillow_image_converter(data["Object_Img"], 200,
                                                                                             135)
                    else:
                        data["Object_Img"] = None

                query = f"""
                            SELECT TOP 1 FORMAT(Time, 'dd-MM-yyyy')
                            FROM [{self.dict_db_details['str_db_name']}].[dbo].[{self.dict_db_details['str_event_details_table']}]
                            ORDER BY Time ASC
                        """
                cursor.execute(query)
                result = cursor.fetchall()
                start_date = result[0][0] if result else ""

        except Exception as e:
            print(f"Error in fetch_events: {e}")
            import traceback
            print(traceback.format_exc())

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()

        print(f"Returning {len(list_event)} events")
        return list_event, start_date

    def get_data_count(self, dict_filter_criteria: dict):
        i_data_count = 0
        try:
            connection = pyodbc.connect(
                f"""DRIVER={{ODBC Driver 17 for SQL Server}};
                    SERVER={self.dict_db_details["str_server"]};
                    UID={self.dict_db_details["str_username"]};
                    PWD={self.dict_db_details["str_password"]}""",
                autocommit=True
            )
            cursor = connection.cursor()
            select_db_query = f"USE {self.dict_db_details['str_db_name']};"
            cursor.execute(select_db_query)

            if dict_filter_criteria["str_start_Timeperiod"] == "" and dict_filter_criteria["str_end_Timeperiod"] == "":
                query = f"""SELECT COUNT(*)
                            FROM [{self.dict_db_details['str_db_name']}].[dbo].[{self.dict_db_details['str_event_details_table']}]
                         """
                print(f"Executing count query without filter: {query}")
                cursor.execute(query)
            else:
                query = f"""SELECT COUNT(*)
                            FROM [{self.dict_db_details['str_db_name']}].[dbo].[{self.dict_db_details['str_event_details_table']}]
                            WHERE CAST(Time AS datetime) BETWEEN ? AND ?
                         """
                print(
                    f"Executing count query with filter: {query} with params {dict_filter_criteria['str_start_Timeperiod']}, {dict_filter_criteria['str_end_Timeperiod']}")
                cursor.execute(query, dict_filter_criteria["str_start_Timeperiod"],
                               dict_filter_criteria["str_end_Timeperiod"])

            result = cursor.fetchone()
            i_data_count = int(result[0]) if result else 0
            print(f"get_data_count returned: {i_data_count}")

        except Exception as e:
            print(f"Error in get_data_count: {e}")
            import traceback
            print(traceback.format_exc())

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()

        return i_data_count

    def validate_filter_criteria(self, str_start_date: str, str_end_date: str,
                                 str_start_hour: str, str_end_hour: str,
                                 str_start_minute: str, str_end_minute: str,
                                 str_vehicle_number: str):
        dict_response = {
            "str_error_msg_heading": "",
            "str_error_msg": "",
            "dict_filter_criteria": {
                "str_start_Timeperiod": "",
                "str_end_Timeperiod": "",
                "str_vehicle_number": "%"  # Default to wildcard since vehicle_number is not in schema
            }
        }

        try:
            start_date = datetime.datetime.strptime(str_start_date, "%d-%m-%Y")
            end_date = datetime.datetime.strptime(str_end_date, "%d-%m-%Y")

            if start_date > end_date:
                dict_response["str_error_msg_heading"] = "Invalid Date Range!"
                dict_response["str_error_msg"] = "'Starting Date' must be less than 'Ending Date'"
                return dict_response
            elif start_date == end_date:
                if int(str_start_hour) > int(str_end_hour):
                    dict_response["str_error_msg_heading"] = "Invalid Time Range!"
                    dict_response["str_error_msg"] = "'Starting Time' must be less than 'Ending Time'"
                    return dict_response
                elif int(str_start_hour) == int(str_end_hour):
                    if int(str_start_minute) > int(str_end_minute):
                        dict_response["str_error_msg_heading"] = "Invalid Time Range!"
                        dict_response["str_error_msg"] = "'Starting Time' must be less than 'Ending Time'"
                        return dict_response

            dict_response["dict_filter_criteria"]["str_start_Timeperiod"] = (
                f"{start_date.year}-{start_date.month:02d}-{start_date.day:02d} {str_start_hour}:{str_start_minute}:00"
            )
            dict_response["dict_filter_criteria"]["str_end_Timeperiod"] = (
                f"{end_date.year}-{end_date.month:02d}-{end_date.day:02d} {str_end_hour}:{str_end_minute}:59"
            )

        except ValueError as e:
            print(f"Date parsing error: {e}")
            dict_response["str_error_msg_heading"] = "Invalid Date Format!"
            dict_response["str_error_msg"] = "Please enter dates in DD-MM-YYYY format."

        return dict_response

    def fetch_vehicle_data_and_count(self, dict_filter_criteria: dict):
        entry_count = exit_count = 0
        try:
            connection = pyodbc.connect(
                f"""DRIVER={{ODBC Driver 17 for SQL Server}};
                    SERVER={self.dict_db_details['str_server']};
                    UID={self.dict_db_details['str_username']};
                    PWD={self.dict_db_details['str_password']}""",
                autocommit=True
            )
            cursor = connection.cursor()
            select_db_query = f"USE {self.dict_db_details['str_db_name']};"
            cursor.execute(select_db_query)

            entry_count_query = f"""
                SELECT COUNT(*) 
                FROM [{self.dict_db_details['str_db_name']}].[dbo].[{self.dict_db_details['str_event_details_table']}]
                WHERE CAST(Time AS datetime) BETWEEN ? AND ? 
                AND Status = 'Entry'
            """
            cursor.execute(entry_count_query, dict_filter_criteria["str_start_Timeperiod"],
                           dict_filter_criteria["str_end_Timeperiod"])
            entry_count = cursor.fetchone()[0]

            exit_count_query = f"""
                SELECT COUNT(*) 
                FROM [{self.dict_db_details['str_db_name']}].[dbo].[{self.dict_db_details['str_event_details_table']}]
                WHERE CAST(Time AS datetime) BETWEEN ? AND ? 
                AND Status = 'Exit'
            """
            cursor.execute(exit_count_query, dict_filter_criteria["str_start_Timeperiod"],
                           dict_filter_criteria["str_end_Timeperiod"])
            exit_count = cursor.fetchone()[0]

            print(f"Entry: {entry_count}, Exit: {exit_count}, Balance: {entry_count - exit_count}")
            return entry_count, exit_count, entry_count - exit_count

        except Exception as e:
            print(f"Error in fetch_vehicle_data_and_count: {e}")
            import traceback
            print(traceback.format_exc())
            return entry_count, exit_count, entry_count - exit_count

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()

    def insert_acknowledgment(self, event_id: str, acknowledgment_note: str):
        try:
            connection = pyodbc.connect(
                f"""DRIVER={{ODBC Driver 17 for SQL Server}};
                    SERVER={self.dict_db_details['str_server']};
                    UID={self.dict_db_details['str_username']};
                    PWD={self.dict_db_details['str_password']}""",
                autocommit=True
            )
            cursor = connection.cursor()
            select_db_query = f"USE {self.dict_db_details['str_db_name']};"
            cursor.execute(select_db_query)

            verify_query = f"""
                SELECT COUNT(*) 
                FROM [{self.dict_db_details['str_db_name']}].[dbo].[{self.dict_db_details['str_event_details_table']}]
                WHERE Event_Id = ?
            """
            cursor.execute(verify_query, (event_id,))
            count = cursor.fetchone()[0]
            print(f"Found {count} matching records for Event_Id: {event_id}")

            if count == 0:
                print("No matching record found")
                return False

            update_query = f"""
                UPDATE [{self.dict_db_details['str_db_name']}].[dbo].[{self.dict_db_details['str_event_details_table']}]
                SET Acknowledgment_Message = ?,
                    Acknowledgment_Time = GETDATE()
                WHERE Event_Id = ?
            """
            print(f"Executing update query: {update_query} with params {acknowledgment_note}, {event_id}")
            cursor.execute(update_query, (acknowledgment_note, event_id))
            connection.commit()
            print("Update successful")
            return True

        except Exception as e:
            print(f"Error inserting acknowledgment: {e}")
            import traceback
            print(traceback.format_exc())
            return False

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()

    def fetch_unrecognized_vehicles(self):
        list_unrecognized_event = []
        try:
            connection = pyodbc.connect(
                f"""DRIVER={{ODBC Driver 17 for SQL Server}};
                    SERVER={self.dict_db_details['str_server']};
                    UID={self.dict_db_details['str_username']};
                    PWD={self.dict_db_details['str_password']}""",
                autocommit=True
            )
            cursor = connection.cursor()
            select_db_query = f"USE {self.dict_db_details['str_db_name']};"
            cursor.execute(select_db_query)

            query = f"""
                SELECT TOP 10 * 
                FROM [{self.dict_db_details['str_db_name']}].[dbo].[{self.dict_db_details['str_event_details_table']}]
                WHERE Alarm = 2 
                AND Acknowledgment_Time IS NULL
                ORDER BY Event_Id DESC
            """
            cursor.execute(query)
            response = cursor.fetchall()
            columns = [column[0] for column in cursor.description]

            for data in response:
                record_dict = {columns[i]: data[i] for i in range(len(columns))}

            for data in list_unrecognized_event:
                if data["Object_Img"] != "N/A":
                    data["Object_Img"] = self.base64_to_cv2mat_or_pillow_image_converter(data["Object_Img"], 200, 130)
                else:
                    data["Object_Img"] = None

        except Exception as e:
            print(f"Error in fetch_unrecognized_vehicles: {e}")
            import traceback
            print(traceback.format_exc())

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()

        return list_unrecognized_event

    def fetch_missed_vehicles(self):
        list_unrecognized_event = []
        try:
            connection = pyodbc.connect(
                f"""DRIVER={{ODBC Driver 17 for SQL Server}};
                    SERVER={self.dict_db_details['str_server']};
                    UID={self.dict_db_details['str_username']};
                    PWD={self.dict_db_details['str_password']}""",
                autocommit=True
            )
            cursor = connection.cursor()
            select_db_query = f"USE {self.dict_db_details['str_db_name']};"
            cursor.execute(select_db_query)

            query = f"""
                SELECT TOP (100) * 
                FROM [{self.dict_db_details['str_db_name']}].[dbo].[{self.dict_db_details['str_missed_event_details_table']}]
                ORDER BY Event_Id DESC
            """
            cursor.execute(query)
            response = cursor.fetchall()
            columns = [column[0] for column in cursor.description]

            for data in response:
                record_dict = {columns[i]: data[i] for i in range(len(columns))}
                list_unrecognized_event.append(record_dict)

            for data in list_unrecognized_event:
                if data["Object_Img"] != "N/A":
                    data["Object_Img"] = self.base64_to_cv2mat_or_pillow_image_converter(data["Object_Img"], 200, 130)
                else:
                    data["Object_Img"] = None

        except Exception as e:
            print(f"Error in fetch_missed_vehicles: {e}")
            import traceback
            print(traceback.format_exc())

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()

        return list_unrecognized_event

    def get_distinct_vehicles(self, search_text=None):
        pass
        # list_vehicles = []
        # try:
        #     connection = pyodbc.connect(
        #         f"""DRIVER={{ODBC Driver 17 for SQL Server}};
        #             SERVER={self.dict_db_details["str_server"]};
        #             UID={self.dict_db_details["str_username"]};
        #             PWD={self.dict_db_details["str_password"]}""",
        #         autocommit=True
        #     )
        #     cursor = connection.cursor()
        #     select_db_query = f"USE {self.dict_db_details['str_db_name']};"
        #     cursor.execute(select_db_query)

        #     # Since vehicle_number doesn't exist, return empty list or modify to use another column (e.g., Track_Id)
        #     print("Warning: get_distinct_vehicles not implemented as vehicle_number column does not exist")
        #     return list_vehicles

        # except Exception as e:
        #     print(f"Error in get_distinct_vehicles: {e}")
        #     import traceback
        #     print(traceback.format_exc())

        # finally:
        #     if 'cursor' in locals():
        #         cursor.close()
        #     if 'connection' in locals():
        #         connection.close()

        # return list_vehicles

    def base64_to_cv2mat_or_pillow_image_converter(self, base64_image, requiredWidth, requiredHeight):
        try:
            image_data = b64decode(base64_image)
            image_array = frombuffer(image_data, dtype=uint8)
            image_mat = imdecode(image_array, IMREAD_COLOR)
            thumbnail_plate = Image.fromarray(image_mat).resize((requiredWidth, requiredHeight),
                                                                Image.Resampling.LANCZOS)
            photo = CTkImage(light_image=thumbnail_plate, size=(requiredWidth, requiredHeight))
            return photo
        except Exception as e:
            print(f"Error converting base64 image: {e}")
            return None

    def today_entry_exit_count(self):
        pass
        # entry_count = exit_count = 0
        # try:
        #     today_date = datetime.datetime.now().strftime('%Y-%m-%d')
        #     start_time = f"{today_date} 00:00:00"
        #     end_time = f"{today_date} 23:59:59"

        #     connection = pyodbc.connect(
        #         f"""DRIVER={{ODBC Driver 17 for SQL Server}};
        #             SERVER={self.dict_db_details['str_server']};
        #             UID={self.dict_db_details['str_username']};
        #             PWD={self.dict_db_details['str_password']}""",
        #         autocommit=True
        #     )
        #     cursor = connection.cursor()
        #     select_db_query = f"USE {self.dict_db_details['str_db_name']};"
        #     cursor.execute(select_db_query)

        #     entry_count_query = f"""
        #         SELECT COUNT(*) 
        #         FROM [{self.dict_db_details['str_db_name']}].[dbo].[{self.dict_db_details['str_event_details_table']}]
        #         WHERE CAST(Time AS datetime) BETWEEN ? AND ? 
        #         AND Status = 'Entry'
        #     """
        #     cursor.execute(entry_count_query, start_time, end_time)
        #     entry_count = cursor.fetchone()[0]

        #     exit_count_query = f"""
        #         SELECT COUNT(*) 
        #         FROM [{self.dict_db_details['str_db_name']}].[dbo].[{self.dict_db_details['str_event_details_table']}]
        #         WHERE CAST(Time AS datetime) BETWEEN ? AND ? 
        #         AND Status = 'Exit'
        #     """
        #     cursor.execute(exit_count_query, start_time, end_time)
        #     exit_count = cursor.fetchone()[0]

        #     print(f"Today's Entry: {entry_count}, Exit: {exit_count}")
        #     return entry_count, exit_count

        # except Exception as e:
        #     print(f"Error in today_entry_exit_count: {e}")
        #     import traceback
        #     print(traceback.format_exc())
        #     return entry_count, exit_count