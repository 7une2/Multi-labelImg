import codecs
import os

from libs.constants import DEFAULT_ENCODING

TXT_EXT = '.txt'
ENCODE_METHOD = DEFAULT_ENCODING

class YOLOWriter:

    def __init__(self, folder_name, filename, img_size, database_src='Unknown', local_img_path=None):
        self.folder_name = folder_name
        self.filename = filename
        self.database_src = database_src
        self.img_size = img_size
        self.box_list = []
        self.local_img_path = local_img_path
        self.verified = False

    def add_bnd_box(self, x_min, y_min, x_max, y_max, names, difficult):
        bnd_box = {'xmin': x_min, 'ymin': y_min, 'xmax': x_max, 'ymax': y_max}
        bnd_box['names'] = names  # 여러 라벨을 리스트로 저장
        bnd_box['difficult'] = difficult
        self.box_list.append(bnd_box)

    def bnd_box_to_yolo_line(self, box, class_list=[]):
        x_min = box['xmin']
        x_max = box['xmax']
        y_min = box['ymin']
        y_max = box['ymax']

        x_center = float((x_min + x_max)) / 2 / self.img_size[1]
        y_center = float((y_min + y_max)) / 2 / self.img_size[0]

        w = float((x_max - x_min)) / self.img_size[1]
        h = float((y_max - y_min)) / self.img_size[0]

        box_names = box['names']
        class_indices = []
        for box_name in box_names:
            if box_name not in class_list:
                class_list.append(box_name)
            class_index = class_list.index(box_name)
            class_indices.append(class_index)

        return class_indices, x_center, y_center, w, h

    def save(self, class_list=[], target_file=None):

        out_file = None  # Update yolo .txt
        out_class_file = None   # Update class list .txt

        if target_file is None:
            out_file = open(self.filename + TXT_EXT, 'w', encoding=ENCODE_METHOD)
            classes_file = os.path.join(os.path.dirname(os.path.abspath(self.filename)), "classes.txt")
            out_class_file = open(classes_file, 'w')
        else:
            out_file = codecs.open(target_file, 'w', encoding=ENCODE_METHOD)
            classes_file = os.path.join(os.path.dirname(os.path.abspath(target_file)), "classes.txt")
            out_class_file = open(classes_file, 'w')

        for box in self.box_list:
            class_indices, x_center, y_center, w, h = self.bnd_box_to_yolo_line(box, class_list)
            class_indices_str = ",".join(map(str, class_indices))  # 여러 라벨을 쉼표로 구분하여 저장
            out_file.write("%s %.6f %.6f %.6f %.6f\n" % (class_indices_str, x_center, y_center, w, h))

        for c in class_list:
            out_class_file.write(c + '\n')

        out_class_file.close()
        out_file.close()

class YoloReader:

    def __init__(self, file_path, image, class_list_path=None):
        self.shapes = []
        self.file_path = file_path

        if class_list_path is None:
            dir_path = os.path.dirname(os.path.realpath(self.file_path))
            self.class_list_path = os.path.join(dir_path, "classes.txt")
        else:
            self.class_list_path = class_list_path

        classes_file = open(self.class_list_path, 'r')
        self.classes = classes_file.read().strip('\n').split('\n')

        img_size = [image.height(), image.width(), 1 if image.isGrayscale() else 3]
        self.img_size = img_size

        self.verified = False
        self.parse_yolo_format()

    def get_shapes(self):
        return self.shapes

    def add_shape(self, labels, x_min, y_min, x_max, y_max, difficult):
        points = [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)]
        self.shapes.append((labels, points, None, None, difficult))

    def yolo_line_to_shape(self, class_indices_str, x_center, y_center, w, h):
        class_indices = map(int, class_indices_str.split(","))
        labels = [self.classes[i] for i in class_indices]

        x_min = max(float(x_center) - float(w) / 2, 0)
        x_max = min(float(x_center) + float(w) / 2, 1)
        y_min = max(float(y_center) - float(h) / 2, 0)
        y_max = min(float(y_center) + float(h) / 2, 1)

        x_min = round(self.img_size[1] * x_min)
        x_max = round(self.img_size[1] * x_max)
        y_min = round(self.img_size[0] * y_min)
        y_max = round(self.img_size[0] * y_max)

        return labels, x_min, y_min, x_max, y_max

    def parse_yolo_format(self):
        bnd_box_file = open(self.file_path, 'r')
        for bndBox in bnd_box_file:
            class_indices_str, x_center, y_center, w, h = bndBox.strip().split(' ')
            labels, x_min, y_min, x_max, y_max = self.yolo_line_to_shape(class_indices_str, x_center, y_center, w, h)
            self.add_shape(labels, x_min, y_min, x_max, y_max, False)