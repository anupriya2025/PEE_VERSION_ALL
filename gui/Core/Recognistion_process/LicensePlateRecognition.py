import gc
import re

import cv2
from ultralytics import YOLO

import base64

from gui.Core.Recognistion_process.LicensePlateColorDetector import LicensePlateColorDetector
from gui.Core.Recognistion_process.ConfigLoader import ConfigLoader
import logging


class LicensePlateRecognition:
    def __init__(self):
        logging.info("Initializing LicensePlateRecognition class")
        self.configloader=ConfigLoader("Config/config.json")
        self.license_plate_model = YOLO(self.configloader.get("model_details.license_plate_detection_model_path"))



    def check_plate_format(self, input_string):
        """
        Check the Country name and valid number
        :param input_string string give by ocr
        :return string  Country name and Unknown in failure case

        """
        Country_patterns = {
            'India': [
                r'[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}',
                r'[A-Z]{2}[0-9]{1}[A-Z]{3}[0-9]{3}[A-Z]{1}',
                r'[A-Z]{2}[0-9]{1}[A-Z]{3}[0-9]{4}',
                r'[A-Z]{2}[0-9]{2}[A-Z]{1}[0-9]{4}',
                r'[A-Z]{2}[0-9]{6}',
                r'[A-Z]{2}[0-9]{1}[A-Z]{2}[0-9]{4}',
                r'[0-9]{2}[A-Z]{2}[0-9]{4}[A-Z]{2}',
                r'[0-9]{2}[A-Z]{2}[0-9]{4}[A-Z]{1}',
                r'[0-9]{2}[A-Z]{1}[0-9]{6}[A-Z]{1}'
            ],
            'China': [
                r'[A-Z]{1}[0-9]{4}[A-Z]{1}',
                r'[A-Z]{2}[0-9]{3}[A-Z]{1}',
                r'[A-Z]{4}[0-9]{2}',
                r'[A-Z]{3}[0-9]{3}',
                r'[A-Z]{1}[0-9]{1}[A-Z]{1}[0-9]{3}',
                r'[A-Z]{1}[0-9]{3}[A-Z]{1}[0-9]{1}',
            ]
        }

        # Match the input_string with regex patterns for each Country
        for Country, patterns in Country_patterns.items():
            for pattern in patterns:
                if re.fullmatch(pattern, input_string):
                    return Country

        # Return Unknown if no pattern matches
        gc.collect()
        return "Unknown"


    def pre_process_ocr_result(self,text):
        text = re.sub(r'[^A-Z0-9]', '', text)
        if  7 < len(text) < 11 :
            text = re.sub(r'[^A-Z0-9]', '', text)

        corrected_text = list(text)

        if len(corrected_text)==10 and (corrected_text[0].isalpha() or corrected_text[1].isalpha()):
            for i, char in enumerate(corrected_text):
                if char == 'O' and i in [2, 3, 6, 7, 8, 9]:
                    corrected_text[i] = '0'

                if char in ['I', 'L'] and i in [2, 3, 6, 7, 8, 9]:
                    corrected_text[i] = '1'

                if char in ['B', 'b'] and i in [2, 3, 6, 7, 8, 9]:
                    corrected_text[i] = '8'

                if char in ['A', 'K'] and i in [2, 3, 6, 7, 8, 9]:
                    corrected_text[i] = '4'

                if char == '0' and i in [0, 4, 5,]:
                    corrected_text[i] = 'O'

                if char == '0' and i in [1]:
                    corrected_text[i] = 'D'

                if char == '1' and i in [0, 1, 4, 5,]:
                    corrected_text[i] = 'I'

                if char == '8' and i in [0, 1, 4, 5,]:
                    corrected_text[i] = 'B'

                if char == '4' and i in [0, 1, 4, 5,]:
                    corrected_text[i] = 'A'

        if len(corrected_text)==9 and (corrected_text[0].isalpha() or corrected_text[1].isalpha()):
            for i, char in enumerate(corrected_text):
                if char == 'O' and i in [2, 3, 5,6, 7, 8]:
                    corrected_text[i] = '0'

                if char in ['I', 'L'] and i in [2, 3, 5,6, 7, 8]:
                    corrected_text[i] = '1'

                if char in ['B', 'b'] and i in [2, 3, 5,6, 7, 8]:
                    corrected_text[i] = '8'

                if char in ['A', 'K'] and i in [2, 3, 5,6, 7, 8]:
                    corrected_text[i] = '4'

                if char == '0' and i in [0, 4]:
                    corrected_text[i] = 'O'

                if char == '0' and i in [1]:
                    corrected_text[i] = 'D'

                if char == '1' and i in [0, 1, 4]:
                    corrected_text[i] = 'I'

                if char == '8' and i in [0, 1, 4]:
                    corrected_text[i] = 'B'

                if char == '4' and i in [0, 1, 4]:
                    corrected_text[i] = 'A'

        text = ''.join(corrected_text)
        return  text


    def detect_plate(self, image):
        """
        Detect the license plate, perform OCR at multiple scales, determine plate color and Country.

        :param image: Vehicle image
        :return: detected_text, plate_base64, vehicle_base64, color, Country
        """
        try:
            detection_results = self.license_plate_model(image)
            plate_base64, vehicle_base64, color, detected_text, Country = 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'

            # Encode vehicle image to base64
            _, encoded_vehicle = cv2.imencode('.jpg', image)
            vehicle_base64 = base64.b64encode(encoded_vehicle.tobytes()).decode('utf-8')

            if detection_results[0].boxes:
                for box in detection_results[0].boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    if box.conf[0] > 0.5:
                        plate_image = image[y1:y2, x1:x2]
                        _, encoded_plate = cv2.imencode('.jpg', plate_image)
                        plate_base64 = base64.b64encode(encoded_plate.tobytes()).decode('utf-8')
                        color = LicensePlateColorDetector.guess_plate_color(plate_image)

                        scales = [0.5, 0.8, 1.0, 1.4, 1.8]
                        for scale in scales:
                            resized_plate = cv2.resize(plate_image, None, fx=scale, fy=scale,
                                                       interpolation=cv2.INTER_LINEAR)
                            try:
                                ocr_results = self.ocr.ocr(resized_plate, cls=True)
                            except Exception:
                                continue

                            if ocr_results and isinstance(ocr_results[0], list):
                                text1 = ' '.join([line[1][0] for line in ocr_results[0] if len(line) > 1])
                                text = self.pre_process_ocr_result(text1)
                                logging.info(f"Detected text is -> {text1} and corrected to {text} ")
                                if text:
                                    detected_text = text
                                    Country = self.check_plate_format(detected_text)
                                    if Country != 'Unknown':
                                        logging.info(f"plate number recognised for Country : {detected_text} for Country : {Country} with color : {color}")
                                        return detected_text, plate_base64, vehicle_base64, color, Country,detected_text

            return 'N/A', plate_base64, vehicle_base64, color, 'N/A',detected_text

        except Exception as e:
            print(f"Error in plate detection: {e}")
            return 'N/A', 'N/A', 'N/A', 'N/A', 'N/A','N/A'

