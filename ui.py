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
import re

try:
    from PySide import QtGui, QtCore
    QtWidgets = QtGui
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


def is_int_or_str(attr):
    """
    Custom type check to see if the attribute is a string or int.

    Args:
        attr(str):      String type

    Returns:
        (int|str)
    """
    if attr.isdigit():
        return int(attr)

    return str(attr)

def filter_format(attr):
    """
    Find the format by int list
    Args:
        attr:

    Returns:

    """
    if not attr.isdigit():
        raise TypeError("Please provide an int value!")

    if int(attr) == 0:
        return nuke.root().format().name()

    nuke_format = nuke.formats()[int(attr)-1]
    return nuke_format.name()


class CustomLineEdit(QtWidgets.QLineEdit):
    """
    Custom line edit, that populates the completer on click. The
    populate functions required to return a list of string to fill
    in the completer.

    Attributes:
        items(list):        List of completer items
    """
    def __init__(self, populate):
        """
        Init constructor.

        Args:
            populate(function):         Callable function that returns a list
        """
        super(CustomLineEdit, self).__init__()
        self.populate = populate
        self.items = list()
        # Populate if you can on init
        self.mousePressEvent()

    def mousePressEvent(self, *args, **kwargs):
        """
        On mouse click, if there is a value highlight the text input, update the completer
        from the populate function.
        """
        # Select the input, making it easier to remove/override the input text
        self.selectAll()
        # Set the list of string from the populate function, list of classes or knobs
        self.items = self.populate()
        # Create and set the completer
        completer = QtWidgets.QCompleter(self.items)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setCompleter(completer)
        self.completer().setCompletionPrefix(self.text() or "")
        # Pop up the completer
        self.completer().complete()

        return None


class GatherAndSet(QtWidgets.QDialog):
    __KNOB_TYPES = \
        {
            "Boolean_Knob": int,
            "ChannelMask_Knob": str,
            "Enumeration_Knob": is_int_or_str,
            "Int_Knob": int,
            "Format_Knob": filter_format,
        }
    __PATTERN = re.compile(r"\w+")

    def __init__(self, parent=None):
        """
        Set the layout and connection on launch.

        Args:
            parent(object):        Parent QWidget, or app application
        """

        super(GatherAndSet, self).__init__(parent or QtWidgets.QApplication.activeWindow())
        self.resize(350, 150)

        self.setLayout(self.master_layout())
        self.connection()

    @property
    def classes(self):
        """ (list) of class names. """
        return self.class_dropdown.items

    @property
    def class_name(self):
        """ (str) Current class name. """
        return self.class_dropdown.text()

    @property
    def knob_name(self):
        """ (list) of knob names. """
        return self.knob_dropdown.text()

    @property
    def knobs(self):
        """ (str) Current knob name. """
        return self.knob_dropdown.items

    @property
    def value(self):
        """ (str) User input value. """
        return self.value_lineedit.text()

    def base_layout(self):
        """
        Creating the class, knob, and input value line edits, adding the
        widgets to the grid layout.

        Returns:
            (QtWidgets.QGridLayout)
        """
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
        """
        Creating the set, and closepush buttons, appending the button to the
        layout.

        Returns:
            (QtWidgets.QHBoxLayout)
        """
        self.set_button = QtWidgets.QPushButton("Set")
        self.close_button = QtWidgets.QPushButton("Close")

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.set_button, alignment=QtCore.Qt.AlignTop)
        layout.addWidget(self.close_button)

        return layout

    def connection(self):
        """
        Handling the signal connections for the ui.
        """
        self.close_button.pressed.connect(self.close)
        self.set_button.pressed.connect(self.set_values)

        return None

    def master_layout(self):
        """
        Combining all the layouts into the master.

        Returns:
            (QtWidgets.QVBoxLayout)
        """
        layout = QtWidgets.QVBoxLayout()

        layout.addLayout(self.base_layout())
        layout.addSpacing(30)
        layout.addLayout(self.button_layout())

        return layout

    def set_values(self):
        if not all([self.class_name in self.classes, self.knob_name in self.knobs]):
            msg = "Please select valid class and knob!"
            QtWidgets.QMessageBox(self, text=msg, icon=QtWidgets.QMessageBox.Warning).exec_()
            return False

        if not self.value:
            msg = "Value required for the set operation, read tooltip for more information!"
            QtWidgets.QMessageBox(self, text=msg, icon=QtWidgets.QMessageBox.Warning).exec_()

        try:
            for node in nuke.allNodes(self.class_name):
                knob = node.knob(self.knob_name)
                knob_type = self.__KNOB_TYPES.get(knob.Class(), str)
                # Check the about of array
                print knob
                if hasattr(knob, "arraySize"):
                    array = knob.arraySize()
                    value = self.__PATTERN.findall(self.value)

                    if array == 1:
                        value = knob_type(self.value)
                    elif len(value) != array and len(value) == 1:
                        value = [self.value] * array
                    elif array != len(value):
                        raise TypeError("Array doesnt match! Expected array length of {}, {} provided!".format(
                            array, len(value)))
                else:
                    value = knob_type(self.value)

                node.knob(self.knob_name).setValue(value)

        except Exception as e:
            import logging
            logging.exception("")
            QtWidgets.QMessageBox(self, text=e.message.title(), icon=QtWidgets.QMessageBox.Information).exec_()


def run_in_nuke():
    g = GatherAndSet()
    g.show()

    return True

