#!/usr/bin/env python

# + make dialog resizable to any size
# + init dialog size to correct value
# + sorter:
#   + create config syntax
#   + implement outer sorting nlog(n) sorting algo
#   + add 'corrupt' property to algo
#
# + make Model functions for correct 'files' array (array of dicts: 'name', 'spoilt', 'created')
# + make ViewController
# - make result writer to file - filename 'ps-result-USER.json'
# {"user":"STR","groups":[]}
# }
# - make main logic of application
# + make result writer function (out.json)

import sys
import random
import json
import os
import datetime
import time
from PIL import Image
import PIL.ExifTags
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
import sets

# "prefix": "d:\photo"
# "dirs": ["", "", ""]
# path = dir + filename

#   {
#       "user": "USER",
#       "groups": [{
#           "name": "GROUP1",
#           "files": [{"path": "dir+filename", "created": 12345, "spoilt": true},{...}]
#       }, {
#           "name": GROUP2",
#           "files": [{}, {}]
#       }]

def write_result(filename, user, groups):
    with open(filename, 'w') as f:
        json.dump({'user': user, 'groups': groups}, f)

class MergeSorter:
    def __init__(self, array):
        self.array = array

    def start(self):
        if len(self.array) < 2:
            return None, None
        self.pos = [0, 1]
        self.i = [0, 0]
        self.n = [1, 1]
        self.result = []
        return self.array[0], self.array[1]

    def next(self, _0_is_greater):
        g = 1
        if _0_is_greater:
            g = 0
        l = 1 - g
        self.result.append(self.array[self.pos[l] + self.i[l]])
        self.i[l] = self.i[l] + 1
        if self.i[l] == self.n[l]:
            self.result = self.result + self.array[self.pos[g] + self.i[g]:self.pos[g] + self.n[g]]
            self.array = self.array[:self.pos[0]] + self.result + self.array[self.pos[1] + self.n[1]:]
            self.result = []
            if self.move_to_next_subarray():
                return None, None
        return self.array[self.pos[0] + self.i[0]], self.array[self.pos[1] + self.i[1]]

    def move_to_next_subarray(self):
        self.pos[0] = self.pos[1] + self.n[1]
        if self.pos[0] + self.n[0] >= len(self.array):
            self.pos[0] = 0
            self.n[0] = self.n[0] * 2
            if self.n[0] >= len(self.array):
                return True
        self.pos[1] = self.pos[0] + self.n[0]
        self.n[1] = min(self.n[0], len(self.array) - self.pos[1])
        self.i[0] = 0
        self.i[1] = 0
        return False

# - 2 pictures - pixmaps[0,1]
# - mark_spoilt
# - mark_better
# - signal - images_changed()
# - group() - get group of photos - name, start, end

class MergeSorter:

    def set_params(self, array):
        self.array = array

    def start(self):

        if len(self.array) < 2:
            self.items = (None, None)
            return self.items
        self.pos = [0, 1]
        self.i = [0, 0]
        self.n = [1, 1]
        self.result = []
        self.items = (self.array[0], self.array[1])
        return self.items

    def next(self, _0_is_greater):

        g = 1
        if _0_is_greater:
            g = 0
        l = 1 - g
        self.result.append(self.array[self.pos[l] + self.i[l]])
        self.i[l] = self.i[l] + 1
        if self.i[l] == self.n[l]:
            self.result = self.result + self.array[self.pos[g] + self.i[g]:self.pos[g] + self.n[g]]
            self.array[:] = self.array[:self.pos[0]] + self.result + self.array[self.pos[1] + self.n[1]:]
            self.result = []
            if self.move_to_next_subarray():
                self.items = (None, None)
                return self.items
        self.items = (self.array[self.pos[0] + self.i[0]], self.array[self.pos[1] + self.i[1]])
        return self.items

    def move_to_next_subarray(self):

        self.pos[0] = self.pos[1] + self.n[1]
        if self.pos[0] + self.n[0] >= len(self.array):
            self.pos[0] = 0
            self.n[0] = self.n[0] * 2
            if self.n[0] >= len(self.array):
                return True
        self.pos[1] = self.pos[0] + self.n[0]
        self.n[1] = min(self.n[0], len(self.array) - self.pos[1])
        self.i[0] = 0
        self.i[1] = 0
        return False

    def restore_state(self, array, state):

        self.array = array
        self.pos = state['pos']
        self.i = state['i']
        self.n = state['n']
        self.result = state['result']
        self.items = state['items']

    def store_state(self):

        return {'pos': self.pos, 'i': self.i, 'n': self.n,
                'result': self.result, 'items': self.items}

# GROUPS ::= [GROUP*]
# GROUP = {"name":"STR","files":[FILE*]}
# FILE = {"name":"STR","created":NUM,"spoilt":bool}
class ImagesSorterModel(QtCore.QObject):

    files_changed = QtCore.pyqtSignal()
    group_changed = QtCore.pyqtSignal()
    spoilt_changed = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()

    def set_params(self, groups, sorter, obj):

        self.groups = groups
        self.sorter = sorter
        self.obj = obj

    def start(self):

        self.i = 0
        self.sorter.set_params(self.groups[self.i]['files'])
        self.sorter.start()
        self.group_changed.emit()
        self.files_changed.emit()

    def change_group(self):

        self.i = self.i + 1
        if self.i == len(self.groups):
            self.done.emit()
            self.obj.callback()
            return
        self.sorter.set_params(self.groups[self.i]['files'])
        self.sorter.start()
        self.group_changed.emit()
        self.files_changed.emit()

    def mark_better(self, _0_is_better):

        print "0 is better: %d" % int(_0_is_better)
        files = self.sorter.items
        if files[0].get('spoilt', False) or files[0].get('spoilt', False):
            _0_is_better = files[1].get('spoilt', False)
        while True:
            files = self.sorter.next(_0_is_better)
            if files[0] is None:
                self.change_group()
                return
            if not files[0].get('spoilt', False) and not files[0].get('spoilt', False):
                break
            _0_is_better = not files[0].get('spoilt', False)
            print "another turn"
        self.files_changed.emit()

    def files(self):
        return self.sorter.items

    def mark_spoilt(self, n):

        print "%d marked spoilt" % n
        file_ = self.sorter.items[n]
        if file_.get('spoilt', False):
            return
        file_['spoilt'] = True
        self.spoilt_changed.emit()
        if self.sorter.items[1 - n].get('spoilt', False):
            self.mark_better(0)

    def store_state(self):
        pass

    def restore_state(self, groups, sorter, obj, state):
        pass

class ImagesSorterViewController(QtGui.QWidget):

    def __init__(self):

        super(ImagesSorterViewController, self).__init__()
        self.create_child_widgets()

    def create_child_widgets(self):
        help_text = QtGui.QLabel("""Loooooooooooong help""")
        policy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        help_text.setSizePolicy(policy)
        self.left_image = ImageLabel(True)
        self.right_image = ImageLabel(False)
        self.left_spoilt = QtGui.QPushButton("Is Spoilt")
        self.right_spoilt = QtGui.QPushButton("Is Spoilt")
        layout = QtGui.QGridLayout()
        layout.addWidget(help_text, 0, 0, 1, 0)
        layout.addWidget(self.left_image, 1, 0)
        layout.addWidget(self.right_image, 1, 1)
        layout.addWidget(self.left_spoilt, 2, 0)
        layout.addWidget(self.right_spoilt, 2, 1)
        self.setLayout(layout)
        self.left_image.clicked.connect(self.mark_better)
        self.right_image.clicked.connect(self.mark_better)
        self.left_spoilt.clicked.connect(self.mark_left_spoilt)
        self.right_spoilt.clicked.connect(self.mark_right_spoilt)

        # set initial size
        rect = QtGui.QDesktopWidget().availableGeometry()
        self.resize(rect.size() / 4)

    def set_params(self, model):

        self.model = model
        files = self.model.files()
        self.left_image.load(files[0]['name'])
        self.right_image.load(files[1]['name'])
        self.model.files_changed.connect(self.update_images)
        self.model.spoilt_changed.connect(self.update_spoilt)

    @QtCore.pyqtSlot(int, QtGui.QWidget)
    def mark_left_spoilt(self):
        self.model.mark_spoilt(0)

    @QtCore.pyqtSlot(int, QtGui.QWidget)
    def mark_right_spoilt(self):
        self.model.mark_spoilt(1)

    @QtCore.pyqtSlot(int, QtGui.QWidget)
    def mark_better(self, left):
        self.model.mark_better(left)

    @QtCore.pyqtSlot(int, QtGui.QWidget)
    def update_images(self):
        files = self.model.files()
        self.left_image.load(files[0]['name'])
        self.right_image.load(files[1]['name'])
        self.left_spoilt.setEnabled(True)
        self.right_spoilt.setEnabled(True)

    @QtCore.pyqtSlot(int, QtGui.QWidget)
    def update_spoilt(self):
        files = self.model.files()
        self.left_spoilt.setEnabled(not files[0].get('spoilt', False))
        self.right_spoilt.setEnabled(not files[1].get('spoilt', False))

    @QtCore.pyqtSlot(int, QtGui.QWidget)
    def finish(self):
        pass 


class FilesSorter:

    def __init__(self, sorter, array):
        self.sorter = sorter(array)

    def start(self):
        self.curr = self.sorter.start()
        return self.curr[0]['name'], self.curr[1]['name']

    def next(self, _0_is_better):

        for i in self.curr:
            i['shown'] = True

        sp = ('spoilt' in self.curr[0], 'spoilt' in self.curr[1])
        if sp[0] != sp[1]:
            _0_is_better = sp[1]

        while True:
            self.curr = self.sorter.next(_0_is_better)
            if self.curr[0] is None:
                return self.curr
            sp = ('spoilt' in self.curr[0], 'spoilt' in self.curr[1])
            if sp[0] or sp[1]:
                _0_is_better = sp[1]
                continue
            return self.curr[0]['name'], self.curr[1]['name']
            """
        while True:
            self.curr = self.sorter.next(_0_is_better)
            if self.curr[0] is None:
                return self.curr
            sp = ('spoilt' in self.curr[0], 'spoilt' in self.curr[1])
            sh = ('shown' in self.curr[0], 'shown' in self.curr[1])

            if sh[0] and not sp[0] and sp[1]:
                _0_is_better = True
                continue
            if sh[1] and not sp[1] and sp[0]:
                _0_is_better = False
                continue
            """

    def mark_as_spoilt(self, _0_is_spoilt):
        i = 0 if _0_is_spoilt else 1
        self.curr[i]['spoilt'] = True

    def get_array(self):
        return self.sorter.array

class ImageLabel(QtGui.QLabel):

    clicked = QtCore.pyqtSignal(bool)

    def __init__(self, is_left):
        super(ImageLabel, self).__init__()
        self.is_left = is_left
        self.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        policy = QtGui.QSizePolicy()
        policy.setVerticalPolicy(QtGui.QSizePolicy.Ignored)
        policy.setHorizontalPolicy(QtGui.QSizePolicy.Ignored)
        self.setSizePolicy(policy)
        self.setText('None')
        self.pixmap = None
        self.filename = None

    def mousePressEvent(self, event):
        self.clicked.emit(self.is_left)

    def resizeEvent(self, event):
        if self.pixmap is not None:
            self.adjust_pixmap()

    def adjust_pixmap(self):
        self.setPixmap(self.pixmap.scaled(self.size(), Qt.KeepAspectRatio,
                       Qt.SmoothTransformation))

    def load(self, filename):
        self.pixmap = QtGui.QPixmap()
        if not self.pixmap.load(filename):
            self.pixmap = None
        self.adjust_pixmap()
        self.filename = filename

    def unload(self):
        self.setText('None')
        self.pixmap = None
        self.filename = None

class ImagesComparator(QtGui.QWidget):

    def __init__(self, sorter):
        super(ImagesComparator, self).__init__()
        self.sorter = sorter
        self.init_widgets()
        left, right = sorter.start()
        self.left_label.load(left)
        self.right_label.load(right)

    def init_widgets(self):
        top_label = QtGui.QLabel("""Loooooooooooong help""")
        policy = QtGui.QSizePolicy()
        policy.setVerticalPolicy(QtGui.QSizePolicy.Maximum)
        policy.setHorizontalPolicy(QtGui.QSizePolicy.Expanding)
        top_label.setSizePolicy(policy)
        self.left_label = ImageLabel(True)
        self.right_label = ImageLabel(False)
        self.left_spoilt = QtGui.QPushButton("Is Spoilt")
        self.right_spoilt = QtGui.QPushButton("Is Spoilt")
        layout = QtGui.QGridLayout()
        layout.addWidget(top_label, 0, 0, 1, 0)
        layout.addWidget(self.left_label, 1, 0)
        layout.addWidget(self.right_label, 1, 1)
        layout.addWidget(self.left_spoilt, 2, 0)
        layout.addWidget(self.right_spoilt, 2, 1)
        self.setLayout(layout)
        self.left_label.clicked.connect(self.load_next)
        self.right_label.clicked.connect(self.load_next)
        self.left_spoilt.clicked.connect(self.mark_left_spoilt)
        self.right_spoilt.clicked.connect(self.mark_right_spoilt)

        desktop = QtGui.QDesktopWidget()
        rect = desktop.availableGeometry()
        self.resize(rect.size() / 4)

    @QtCore.pyqtSlot(int, QtGui.QWidget)
    def load_next(self, is_left):
        left, right = self.sorter.next(is_left)
        if left is None:
            print sorter.get_array()
            make_html('index.html', sorter.get_array())
            sys.exit(0)
        self.left_label.load(left)
        self.right_label.load(right)
        self.left_spoilt.setEnabled(True)
        self.right_spoilt.setEnabled(True)

    @QtCore.pyqtSlot(int, QtGui.QWidget)
    def mark_left_spoilt(self):
        self.left_spoilt.setEnabled(False)
        self.sorter.mark_as_spoilt(True)

    @QtCore.pyqtSlot(int, QtGui.QWidget)
    def mark_right_spoilt(self):
        self.right_spoilt.setEnabled(False)
        self.sorter.mark_as_spoilt(False)

def create_random_array():
    array = []
    size = random.randrange(2, 20)
    for i in range(size):
        array.append(random.randrange(10))
    return array

def sort_by_sorter(klass, array):
    sorter = klass(array)
    a, b = sorter.start()
    while True:
        a, b = sorter.next(a > b)
        if a is None:
            return sorter.array

def test_sorter(klass):
    for i in range(100):
        array = create_random_array()
        array_a = sort_by_sorter(klass, array)
        assert sorted(array) == sort_by_sorter(klass, array)

def load_config():
    try:
        fp = open('test.json', 'r')
        config = json.load(fp)
        fp.close()
    except IOError:
        print "error: 'prank.conf' open failed"
        return
    except ValueError as err:
        print "error: invalid syntax in 'prank.conf': {0}".format(err)
        return
    return config

config = load_config()

def construct_files_array():

    if not 'dirs' in config:
        print "error: 'dir' not specified in configuration file"
        sys.exit(1)

    files = []
    for dir_ in config['dirs']:
        path = os.path.abspath(dir_)
        names = os.listdir(path)
        for name in names:
            name = os.path.join(path, name)
            desc = {'name': name}
            desc['created'] = get_exif_creation_time(name)
            files.append(desc)
    return files

def get_exif_creation_time(name):
    image = Image.open(name)
    string = image._getexif()[36867]
    return time.mktime(datetime.datetime.strptime(string, '%Y:%m:%d %H:%M:%S').utctimetuple())

def parse_time(string):
    return time.mktime(datetime.datetime.strptime(string, '%Y-%m-%d %H:%M:%S').utctimetuple())

def group_files_array(all_files):
    
    groups = []
    for g in config['groups']:
        group = {'name': g['name']}
        group['start'] = parse_time(g['start'])
        group['end'] = parse_time(g['end'])
        files = []
        for f in all_files:
            if f['created'] >= group['start'] and f['created'] <= group['end']:
                files.append(f)
        group['files'] = files
        groups.append(group)
    return groups

def make_html(name, files):
    with open(name, 'w') as html:
        html.write("<html><head></head><body>")
        for f in files:
            html.write('<img width="200" src="{0}" /><br>'.format(f['name']))
        html.write("</body></html>")

array = construct_files_array()
groups = group_files_array(array)

app = QtGui.QApplication(sys.argv)
sorter = MergeSorter()
model = ImagesSorterModel()
model.set_params(groups, sorter, None)
model.start()
view = ImagesSorterViewController()
view.set_params(model)
view.show()
#app.exec_()


#test_sorter(MergeSorter)

#sorter = FilesSorter(MergeSorter, groups[0]['files'])
#app = QtGui.QApplication(sys.argv)

#cd = ImagesComparator(sorter)
#cd.show()
#app.exec_()

