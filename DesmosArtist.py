import cv2
import os
from svg.path import parse_path
from xml.dom import minidom
import potrace
import numpy as np
from PIL import Image


class DesmosArtist:
    img_path: str = None
    lower_threshold: int = None
    upper_threshold: int = None

    latex_expressions = []

    def __init__(self, img_path: str):
        self.img_path = img_path
        self.lower_threshold = 50
        self.upper_threshold = 150

    def __get_contours(self) -> np.ndarray:
        img = cv2.imread(self.img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        contours = cv2.Canny(gray, self.lower_threshold, self.upper_threshold)
        return contours

    def __get_vectorized_img(self, data: np.ndarray) -> potrace.Path:
        # limit values in data to max of 1
        for i in range(len(data)):
            data[i][data[i] > 1] = 1
            # ValueError: The truth value of an array with more than one element is ambiguous.
            # Use a.any() or a.all()
        bmp = potrace.Bitmap(data)
        path = bmp.trace()
        return path

    def __get_latex_equations(self, vector_img: potrace.Path) -> list[str]:
        latex_equations = []
        # curve contains different segments starting at the same point
        for curve in vector_img.curves:
            start = curve.start_point
            segments = curve.segments
            for segment in segments:
                #potrace.CornerSegment
                # 2 linear segments, 2 linear bezier curves
                if segment.is_corner:
                    x0, y0 = start
                    x1, y1 = segment.c
                    x2, y2 = segment.end_point

                    line1x = f'(1-t){x0}+t{x1}'
                    line1y = f'(1-t){y0}+t{y1}'
                    line2x = f'(1-t){x1}+t{x2}'
                    line2y = f'(1-t){y1}+t{y2}'

                    latex_equations.extend((line1x, line1y, line2x, line2y))

                #potrace.BezierSegment
                # 4 points total, one cubic bezier curve
                else:
                    x0, y0 = start
                    x1, y1 = segment.c1
                    x2, y2 = segment.c2
                    x3, y3 = segment.end_point

                    line1x = f'((1-t)^3){x0}+3((1-t)^2)t{x1}+3(1-t)(t^2){x2}+(t^3){x3}'
                    line1y = f'((1-t)^3){y0}+3((1-t)^2)t{y1}+3(1-t)(t^2){y2}+(t^3){y3}'

                    latex_equations.extend((line1x, line1y))

                start = segment.end_point
        return latex_equations


    def draw(self):
        # convert image first with canny edge detection
        contours: np.ndarray = self.__get_contours()
        # use potrace to convert image from raster to vector
        vector_img: potrace.Path = self.__get_vectorized_img(contours)
        # use vectorized data to get bezier curves for graphing
        latex_equations = self.__get_latex_equations(vector_img)
        for e in latex_equations:
            print(e)





