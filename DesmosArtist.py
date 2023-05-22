import cv2
import os
from xml.dom import minidom
import potrace
import numpy as np
from PIL import Image


class DesmosArtist:
    img_path: str = None
    lower_threshold: int = None
    upper_threshold: int = None

    def __init__(self, img_path: str):
        self.img_path = img_path
        self.lower_threshold = 50
        self.upper_threshold = 150

    def __get_contours(self) -> np.ndarray:
        img = cv2.imread(self.img_path)
        img_flipped = cv2.rotate(img, cv2.ROTATE_180)
        gray = cv2.cvtColor(img_flipped, cv2.COLOR_BGR2GRAY)
        contours = cv2.Canny(gray, self.lower_threshold, self.upper_threshold)
        # cv2.imshow('c1', contours)
        # cv2.waitKey(0)

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
                # potrace.CornerSegment
                # 2 linear segments, 2 linear bezier curves
                if segment.is_corner:
                    x0, y0 = start
                    x1, y1 = segment.c
                    x2, y2 = segment.end_point

                    line1 = f'((1-t){x0}+t{x1}, (1-t){y0}+t{y1})'
                    line2 = f'((1-t){x1}+t{x2}, (1-t){y1}+t{y2})'

                    latex_equations.extend((line1, line2))

                # potrace.BezierSegment
                # 4 points total, one cubic bezier curve
                else:
                    x0, y0 = start
                    x1, y1 = segment.c1
                    x2, y2 = segment.c2
                    x3, y3 = segment.end_point

                    line1 = f'((1-t)^3{x0}+3(1-t)^2t{x1}+3(1-t)t^2{x2}+t^3{x3}, ' \
                            f'(1-t)^3{y0}+3(1-t)^2t{y1}+3(1-t)t^2{y2}+t^3{y3})'

                    latex_equations.append(line1)

                start = segment.end_point
        return latex_equations

    def edit_html(self, latex_equations: list[str]):
        with open('desmos_edit.html', 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if 'calculator.setExpression' in line:
                lines.pop(i)

        for i, line in enumerate(lines):
            if '// MARKER' in line:
                start_line = i + 1
                break
        for i, equation in enumerate(latex_equations):
            lines.insert(start_line, f"     calculator.setExpression({{id:'graph{i}', latex:'{equation}'}})\n")

        with open('desmos_edit.html', 'w') as f:
            f.writelines(lines)


    def draw(self):
        # convert image first with canny edge detection
        contours: np.ndarray = self.__get_contours()
        # use potrace to convert image from raster to vector
        vector_img: potrace.Path = self.__get_vectorized_img(contours)
        # use vectorized data to get bezier curves for graphing
        latex_equations = self.__get_latex_equations(vector_img)
        # self.edit_html(latex_equations)

        latex_equations_lines = []
        for equation in latex_equations:
            equation += '\n'
            latex_equations_lines.append(equation)
        with open('latex.txt', 'w') as f:
            f.writelines(latex_equations_lines)

