import cv2
import os
from svg.path import parse_path
from xml.dom import minidom



class DesmosArtist:
    img_path: str = None
    lower_threshold: int = None
    upper_threshold: int = None
    svg_paths = []
    latex_expressions = []

    def __init__(self, img_path: str):
        self.img_path = img_path
        self.lower_threshold = 50
        self.upper_threshold = 150

    def set_lower_threshold(self, lower_threshold: int):
        self.lower_threshold = lower_threshold

    def set_upper_threshold(self, upper_threshold: int):
        self.upper_threshold = upper_threshold

    ###########################################################################

    def __make_canny_img(self):
        img = cv2.imread(self.img_path)
        canny_img = cv2.Canny(img, self.lower_threshold, self.upper_threshold)
        filename = os.path.basename(self.img_path)
        cv2.imwrite(f'canny_{filename}', canny_img)
        return f'canny_{filename}'

    def __make_potrace_img(self, canny_img_path: str):
        os.system(f'potrace {canny_img_path} -b svg')
        return f'{canny_img_path.split(".")[0]}.svg'


    def __get_svg_paths(self, potrace_img_path: str):
        svg_paths = []
        with open(potrace_img_path) as f:
            content = '\n'.join([line.strip() for line in f.readlines()])
            svg_dom = minidom.parseString(content)

            path_strings = [path.getAttribute('d') for path in svg_dom.getElementsByTagName('path')]

            for path_string in path_strings:
                path_data = parse_path(path_string)
                svg_paths.append(path_data.d())
        return svg_paths

    def __process_svg_paths(self):
        operators = 'mlczMLCZ'
        sub_str_start = None
        for path in self.svg_paths:
            for i, char in enumerate(path):
                if char in operators:
                    if sub_str_start != None:
                        sub_str = path[sub_str_start:i - 1]
                        sub_str = sub_str.replace(',', ' ')
                        sub_str = sub_str.split(' ')
                        operator = sub_str.pop(0)
                        self.__process_svg_path(operator, sub_str)
                    sub_str_start = i
            sub_str_start = None

    def __process_svg_path(self, operator, path):
        p = [int(x) for x in path]
        if operator.lower() == 'c':
            a = p[0]
            b = p[1]
            c = p[2]
            d = p[3]
            f = p[4]
            g = p[5]

            latex = r'((%f-2%f+%f)t^{2}-2(%f-%f)t+%f,(%f-2%f+%f)t^{2}-2(%f-%f)t+%f)' % (a, c, f, a, c, a, b, d, g, b, d, b)

            # latex = r'\left(\left(%f-2%f+%f\right)t^{2}-2\left(%f-%f\right)t+%f,\left(%f-2%f+%f\right)t^{2}-2\left(%f-%f\right)t+%f\right)' % (a, c, f, a, c, a, b, d, g, b, d, b)

            # latex = f'(({p[0]}-2{p[2]}+{p[4]})t^2-2({p[0]}-{p[2]})t+{p[0]}, ({p[1]}-2{p[3]}+{p[5]})t^2-2({p[1]}-{p[3]})t+{p[1]})'
            print(latex)
            self.latex_expressions.append(latex)

    def edit_html(self):
        start_line = None
        with open('desmos_edit.html', 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if 'calculator.setExpression' in line:
                lines.pop(i)
        for i, line in enumerate(lines):
            if '// MARKER' in line:
                start_line = i + 1
        for j, expression in enumerate(self.latex_expressions):
            js_str = f"    calculator.setExpression({{id:'graph{j}', latex:'{expression}'}});\n"
            lines.insert(start_line, js_str)

        with open('desmos_edit.html', 'w') as f:
            f.writelines(lines)

    def draw(self):
        canny_img_path = self.__make_canny_img()
        potrace_img_path = self.__make_potrace_img(canny_img_path)
        self.svg_paths = self.__get_svg_paths(potrace_img_path)
        for path in self.svg_paths:
            print(path)
        print()
        self.__process_svg_paths()

        print('\n', '\n', '\n')
        print(self.latex_expressions)
        self.edit_html()
