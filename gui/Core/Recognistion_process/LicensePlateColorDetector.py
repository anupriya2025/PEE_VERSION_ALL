import cv2
import numpy as np
from sklearn.cluster import KMeans
import gc

import logging


class LicensePlateColorDetector:

    logging.info("Initializing LicensePlateColorDetector class")

    @staticmethod
    def get_top_two_dominant_colors(image):
        """
        Guesses the license plate dominant color.
        :param image: Input image as a NumPy array (BGR format).
        :return: The guessed plate color as a tuple in HSV format.
        """
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        pixels = hsv_image.reshape(-1, 3)
        kmeans = KMeans(n_clusters=2, random_state=0)
        kmeans.fit(pixels)
        cluster_centers = kmeans.cluster_centers_
        labels = kmeans.labels_
        label_counts = np.bincount(labels)
        sorted_indices = np.argsort(-label_counts)  # Sorting in descending order of frequency
        dominant_color_1 = cluster_centers[sorted_indices[0]]
        dominant_color_2 = cluster_centers[sorted_indices[1]]
        return tuple(map(int, dominant_color_1)), tuple(map(int, dominant_color_2))

    @staticmethod
    def classify_color(hsv):
        """
        Classifies a color into a predefined category based on HSV values.
        :param hsv: A tuple representing the color in (H, S, V) format.
        :return: A string representing the classified color.
        """
        h, s, v = hsv
        if 100 < h < 140 and s > 100 and v > 50:
            return "blue"

        elif 20 < h < 40 and s > 150 and v > 100:
            return "yellow"

        elif 60 < h < 100 and s > 150 and v > 50:
            return "green"

        elif s < 50 and v > 200:
            return "white"

        elif v < 50:
            return "black"

        elif (0 < h < 10 or 170 < h < 180) and s > 150 and v > 100:
            return "red"

        elif s < 50 and v > 100 and v < 200:
            return "grey"

        else:
            return "unknown"

    @staticmethod
    def guess_plate_color(image):
        """
        Guesses the license plate color based on the top two dominant colors using HSV.
        :param image: Input image as a NumPy array (BGR format).
        :return: The guessed plate color as a string.
        """
        dominant_color_1, dominant_color_2 = LicensePlateColorDetector.get_top_two_dominant_colors(image)
        color1 = LicensePlateColorDetector.classify_color(dominant_color_1)
        color2 = LicensePlateColorDetector.classify_color(dominant_color_2)


        if color1 == "blue" or color2 == "blue":
            return "blue"
        elif color1 == "yellow" or color2 == "yellow":
            return "yellow"
        elif color1 == "green" or color2 == "green":
            return "green"
        elif color1 == "white" or color2 == "white":
            return "white"
        elif color1 == "black" or color2 == "black":
            return "black"
        elif color1 == "red" or color2 == "red":
            return "red"
        elif color1 != "grey" and color2 == "grey":
            return "blue"
        else:
            return "blue"

