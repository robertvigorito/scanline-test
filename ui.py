"""
1. Create a UI using QT that can be run in nuke:
-This UI should gather all node classes that exist in a nukescript at launch time, and list them in a dropdown menu

-the first item, and default selected item should be empty at all times.

-When a class is selected in the above dropdown, another dropdowns hould be shown with all available knobs on that node
class - again sorted.

-Under this there should be a simple text line where you can type a value, and a button that says 'Set'
For whatever knob is selected in this second dropdown, when the user types something into the line and presses 'Set', you
should attempt to set that knob on all nodes of the matching class to the users value
"""
import sys
import nuke

try:
    from PySide import QtGui, QtCore
except:
    from PySide2 import QtGui, QtCore, QtWidgets


def all_classes():
    classes = set()
    for node in nuke.allNodes():
        classes.add(node.Class())

    return sorted(classes)


def all_class_knobs(cls):
    for node in nuke.allNodes(cls):
        return sorted([name for name, item in node.knobs().items()])

    return []


class CustomLineEdit(QtWidgets.QLineEdit):
    def __init__(self, populate):
        super(CustomLineEdit, self).__init__()
        self.populate = populate
        self.items = list()

    def mousePressEvent(self, event):
        self.items = self.populate()
        completer = QtWidgets.QCompleter(self.items)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setCompleter(completer)

        self.completer().setCompletionPrefix(self.text() or "")
        self.completer().complete()


class GatherAndSet(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(GatherAndSet, self).__init__(parent or QtWidgets.QApplication.activeWindow())
        self.resize(350, 150)

        self.setLayout(self.master_layout())
        self.connection()

    @property
    def classes(self):
        return self.class_dropdown.items

    @property
    def class_name(self):
        return self.class_dropdown.text()

    @property
    def knob_name(self):
        return self.knob_dropdown.text()

    @property
    def knobs(self):
        return self.knob_dropdown.items

    @property
    def value(self):
        return self.value_lineedit.text()

    def connection(self):
        self.close_button.pressed.connect(self.close)
        self.set_button.pressed.connect(self.set_values)

    def set_values(self):
        if not all([self.class_name in self.classes, self.knob_name in self.knobs]):
            # do message
            return False

        for node in nuke.allNodes(self.class_name):
            node.knob(self.knob_name).setValue(self.value)




    def base_layout(self):
        self.class_dropdown = CustomLineEdit(all_classes)
        self.class_dropdown.setPlaceholderText("Selected Node Class!")

        self.knob_dropdown = CustomLineEdit(lambda: all_class_knobs(self.class_dropdown.text()))
        self.knob_dropdown.setPlaceholderText("Selected Class knob!")

        self.value_lineedit = QtWidgets.QLineEdit()
        self.value_lineedit.setPlaceholderText("Add value or expression!")

        layout = QtWidgets.QGridLayout()
        layout.addWidget(QtWidgets.QLabel("Class"), 0, 0)
        layout.addWidget(self.class_dropdown, 0, 1)
        layout.addWidget(QtWidgets.QLabel("Knob"), 1, 0)
        layout.addWidget(self.knob_dropdown)
        layout.addWidget(QtWidgets.QLabel("Value"), 2, 0)
        layout.addWidget(self.value_lineedit)

        return layout

    def button_layout(self):
        self.set_button = QtWidgets.QPushButton("Set")
        self.close_button = QtWidgets.QPushButton("Close")

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.set_button, alignment=QtCore.Qt.AlignTop)
        layout.addWidget(self.close_button)

        return layout

    def master_layout(self):
        layout = QtWidgets.QVBoxLayout()

        layout.addLayout(self.base_layout())
        layout.addSpacing(30)
        layout.addLayout(self.button_layout())

        return layout



def run_in_nuke():
    g = GatherAndSet()
    g.show()

    return True


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    g = GatherAndSet()
    g.show()
    sys.exit(app.exec_())