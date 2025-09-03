import cv2
import json
import time
import base64
import random
import pyodbc
import threading
import numpy as np
from PIL import Image
from io import BytesIO
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import logging
from src.utility.shared_queue import vehicle_tracking_details_queue
from gui.Core.Recognistion_process.ConfigLoader import  ConfigLoader
from gui.Core.Recognistion_process.DatabaseHandler import DatabaseHandler
from gui.Core.Recognistion_process.ImageProcessing import ImageProcessing
from gui.Core.Recognistion_process.LicensePlateRecognition import LicensePlateRecognition

class LicensePlateRecognizer:
    def __init__(self):

        logging.info("Initializing LicensePlateRecognizer class")
        self.unique_license_plates = set()
        self.configloader=ConfigLoader("Config/config.json")
        self.license_plate_recognition = LicensePlateRecognition()
        self.image_processing = ImageProcessing()
        self.db_handler = DatabaseHandler()
        self.stop_event = threading.Event()  # Event to signal stopping the thread



    def process_image_for_plate(self, img_base64):
        """
        Recognise the image and return all data about that license plate.
        :param img_base64 : Input image as a encrypted format as base64 string.
        :return: The Recognised data abut the license plate in dictionary.

        """
        try:
            full_image_data = base64.b64decode(img_base64)
            full_image = Image.open(BytesIO(full_image_data))
            full_image = self.image_processing.resize_image(full_image)
            full_image_np = np.array(full_image)
            full_image_cv2 = cv2.cvtColor(full_image_np, cv2.COLOR_RGB2BGR)

            detection_result, plate_base64, vehicle_base64 ,color ,Country, Assume_number = self.license_plate_recognition.detect_plate(full_image_cv2)
            now = datetime.now()
            if detection_result != 'N/A':
                logging.info(f"Data returned successfully : plate_number: {detection_result} , system_Time : {now.year}-{now.month}-{now.day:02d} {now.hour:02d}:{now.minute:02d}:{now.second:02d} ")
                return {
                    'plate_number': detection_result,
                    'plate_img': plate_base64,
                    'Object_Img': vehicle_base64,
                    'color':color,
                    'Country':Country,
                    'system_Time':f"{now.year}-{now.month}-{now.day:02d} {now.hour:02d}:{now.minute:02d}:{now.second:02d}.{now.microsecond // 1000:03d}",
                    'assume_number':Assume_number
                }
            else:
                return {
                    'plate_number': detection_result,
                    'plate_img': plate_base64,
                    'Object_Img': vehicle_base64,
                    'color': color,
                    'Country': Country,
                    'system_Time': f"{now.year}-{now.month}-{now.day:02d} {now.hour:02d}:{now.minute:02d}:{now.second:02d}.{now.microsecond // 1000:03d}",
                    'assume_number': Assume_number
                }

        except Exception as e:
            logging.info(f"Error in  processing image for plate fun : {e}")
            return None

    import logging

    def process_vehicle_data(self, vehicle_data, connection):
        """
        Inserts the vehicle data into the database.

        :param vehicle_data: Dictionary containing vehicle details.
        :param connection: Database connection to handle DB operations.
        """
        try:
            detection_result = None
            for i in range(1, 6):
                img_base64 = vehicle_data.get(f'Object_Img{i}', '').strip()
                if not img_base64:
                    continue

                detection_result = self.process_image_for_plate(img_base64)

                # Ensure detection_result is valid and has plate_number
                if detection_result and detection_result.get('plate_number') and detection_result[
                    'plate_number'] != 'N/A':
                    Status = 'Entry' if vehicle_data.get('Status', 0) == 0 else 'Exit'
                    Alarm_code = self.db_handler.check_vehicle_availability(detection_result['plate_number'])
                    Is_Recognized = 1 if detection_result['plate_number'] != 'N/A' else 0

                    insert_data = {
                        "Track_Id": vehicle_data.get('Track_Id'),
                        "vehicle_number": detection_result.get('plate_number', ""),
                        "Country": detection_result.get('Country', ""),
                        "Object_Img": detection_result.get('Object_Img', ""),
                        "number_plate_img": detection_result.get('plate_img', ""),
                        "Is_Recognized": Is_Recognized,
                        "Time": detection_result.get('system_Time', ""),
                        "Status": Status,
                        "Alarm": Alarm_code
                    }

                    # Insert vehicle data into the database
                    self.db_handler.insert_data(
                        connection,
                        self.db_handler.event_details_table_name,
                        self.db_handler.event_details_table_columns,
                        list(insert_data.values())
                    )
                    logging.info(f"Data inserted into DB: {insert_data}")

                    connection.commit()  # Ensure data is saved
                    return  # Exit loop after first valid detection

            # If no valid detection result, insert default "N/A" data
            if not detection_result or detection_result.get('plate_number') == 'N/A':
                Status = 'Entry' if vehicle_data.get('Status', 0) == 0 else 'Exit'
                Alarm_code = self.db_handler.check_vehicle_availability("N/A")

                insert_data = {
                    "Track_Id": vehicle_data.get('Track_Id'),
                    "vehicle_number": detection_result.get('assume_number',"N/A"),
                    "Country": "N/A",
                    "Object_Img": detection_result.get('Object_Img', ""),
                    "number_plate_img": detection_result.get('plate_img', ""),
                    "Is_Recognized": 0,
                    "Time": detection_result.get('system_Time', ""),
                    "Status": Status,
                    "Alarm": Alarm_code
                }
                # if insert_data.get('number_plate_img') != 'N/A':
                self.db_handler.insert_data(
                    connection,
                    self.db_handler.missed_event_details_table_name,
                    self.db_handler.event_details_table_columns,
                    list(insert_data.values())
                )
                logging.info(f"Default 'N/A' data inserted for vehicle {vehicle_data.get('Track_Id', 'N/A')}")

                connection.commit()

        except Exception as e:
            logging.error(f"Error processing vehicle {vehicle_data.get('Track_Id', 'N/A')}: {str(e)}", exc_info=True)

    def main(self, connecting_string=''):
        """
        main fun that will get the data from src.utility.shared queue for further process and this will handle all worker threads
        """
        logging.info(f"LicensePlateRecognizer main function called !")
        try:
            connecting_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.configloader.get('database.server','N/A')};UID={self.configloader.get('database.user','N/A')};PWD={self.configloader.get('database.password','N/A')}"
            connection = pyodbc.connect(connecting_string, autocommit=True)
            cursor = connection.cursor()
            cursor.execute(DatabaseHandler.fun_USE_DB(self.configloader.get("database.db_name","Error_Database")))
            logging.info(f"Worker thread start working !")
            # Use ThreadPoolExecutor for concurrent processing
            with ThreadPoolExecutor(max_workers=5) as executor:
                while not self.stop_event.is_set():
                    if not vehicle_tracking_details_queue.empty():
                        vehicle_data = vehicle_tracking_details_queue.get()
                        executor.submit(self.process_vehicle_data, vehicle_data, connection)

                    time.sleep(0.1)

        except Exception as e:
            logging.info(f"Database connection error: {e}")

