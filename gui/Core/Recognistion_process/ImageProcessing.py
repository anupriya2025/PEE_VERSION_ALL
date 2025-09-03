import cv2
import numpy as np
from PIL import Image

import logging


class ImageProcessing:

    logging.info("Initializing ImageProcessing class")

    @staticmethod
    def increase_saturation(image, saturation_factor=1.5):
        """
        Increase the saturation of an image for better color recognition
        :param image nparray
        :param saturation_factor scale to set required saturation level
        :return nparray  saturated image
        """
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hsv_image[..., 1] = hsv_image[..., 1] * saturation_factor
        hsv_image[..., 1] = np.clip(hsv_image[..., 1], 0, 255)
        saturated_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR)
        return saturated_image


    @staticmethod
    def resize_image(image, size=(400, 400)):
        """
        Resize the image to required size
        :param image nparray  input image
        :param size to set the required size for image resizing
        :return nparray  resized image
        """

        if isinstance(image, np.ndarray):

            return cv2.resize(image, size)

        return np.array(image.resize(size, Image.Resampling.LANCZOS))
