#!/usr/bin/python

# Import PySide classes
import sys
from PySide.QtCore import *
from PySide.QtGui import *

from collections import OrderedDict

OPERATIONS = OrderedDict((("=", '='),
                          ('!=', '!='),
                          ('>', '>'),
                          ('<', '<'),
                          ))

class NewConnection(QDialog):

    def __init__(self, parent=None):
        super(NewConnection, self).__init__(parent)
        self.setWindowTitle("New Connection")

        self.connect_string = ""

        rows = QVBoxLayout()
        self.setLayout(rows)

        # Add the connection options.
        self.dialect = QComboBox()
        self.dialect.addItems(("sqlite", "mysql", "postgresql", "drizzle", "firebird", "informix", "mssql", "oracle", "sybase"))
        rows.addWidget(self.dialect)

        # TODO: Load this from ~/.sequelpy
        for info in ('hostname', 'username', 'password', 'database'):
            edit = QLineEdit(self)
            if info == "password":
                edit.setEchoMode(QLineEdit.Password)

            # XXX: Sample data, for ease of entry.
            if info == "database":
                edit.setText("sample.db")

            setattr(self, info, edit)
            label = QLabel("&{}:".format(info.title()), self)
            label.setBuddy(edit)

            rows.addWidget(label)
            rows.addWidget(edit)

        # Add the buttons.
        buttonholder = QWidget()
        buttons = QHBoxLayout()
        buttonholder.setLayout(buttons)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect)
        self.connect_button.setDefault(True)
        buttons.addWidget(self.connect_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel)
        buttons.addWidget(self.cancel_button)

        rows.addWidget(buttonholder)


    def connect(self):
        dialect = self.dialect.currentText()
        user = self.username.text()
        password = self.password.text()
        host = self.hostname.text()
        dbname = self.database.text()
        if user:
            if password:
                userpass = "{user}:{password}".format(user=user, password=password)
            else:
                userpass = user
        else:
            userpass = ""

        if host:
            if userpass:
                # Combine user/pass and host
                hostname = "{userpass}@{host}".format(userpass=userpass, host=host)
            else:
                # No user/pass so just use hostname
                hostname = host
        else:
            # No host, so no need for user/pass
            hostname = ""

        self.connect_string = "{dialect}://{hostname}/{dbname}".format(dialect=dialect,
                                                                        hostname=hostname,
                                                                        dbname=dbname)

        self.viewer = Viewer(self.connect_string)
        self.viewer.showMaximized()
        self.viewer.raise_()
        self.viewer.activateWindow()

        self.accept()

    def cancel(self):
        print "cancel!"
        self.reject()

class Viewer(QMainWindow):

    def __init__(self, connect_string, parent=None):
        super(Viewer, self).__init__(parent)
        self.connect_string = connect_string
        self.setWindowTitle(self.connect_string)
        center = QWidget()
        self.setCentralWidget(center)

        rows = QHBoxLayout()
        center.setLayout(rows)

        from sqlalchemy import create_engine
        from sqlalchemy.ext.declarative import declarative_base
        self.engine = create_engine(connect_string)
        self.Base = declarative_base()
        self.metadata = self.Base.metadata
        self.metadata.reflect(self.engine)

        self.tables = self.metadata.tables

        # The list of tables
        self.tables_listing = QListWidget(self)
        self.tables_listing.addItems(self.tables.keys())
        rows.addWidget(self.tables_listing)
        self.tables_listing.itemSelectionChanged.connect(self.populate)

        # The filter bar
        self.right_column_container = QWidget()
        self.right_column = QVBoxLayout()
        self.right_column_container.setLayout(self.right_column)
        rows.addWidget(self.right_column_container)
        self.filterbar = QWidget()
        self.right_column.addWidget(self.filterbar)
        buttons = QHBoxLayout()
        self.filterbar.setLayout(buttons)

        # "Filter:" label
        self.filter_label = QLabel("Filter:")
        buttons.addWidget(self.filter_label)

        # columns
        self.filter_columns = QComboBox()
        buttons.addWidget(self.filter_columns)

        # operator
        self.filter_operators = QComboBox()
        self.filter_operators.addItems(OPERATIONS.keys())
        buttons.addWidget(self.filter_operators)

        # text
        self.filter_text = QLineEdit()
        buttons.addWidget(self.filter_text)

        # filter button
        self.filter_button = QPushButton('Filter')
        buttons.addWidget(self.filter_button)

        # The actual contents of the selected table.
        self.table = QTableWidget(self)
        self.table.horizontalHeader().setVisible(True)
        self.right_column.addWidget(self.table)

    def populate(self):
        table = self.tables_listing.selectedItems()[0].text()
        columns = self.tables[table].columns.keys()
        rows = self.engine.execute(self.tables[table].select()).fetchall()

        self.table.clear()
        self.table.setColumnCount(len(columns))
        self.table.setRowCount(30 if len(rows) > 30 else len(rows))
        self.table.setHorizontalHeaderLabels(columns)

        self.filter_columns.addItems(columns)

        r = 0
        for row in rows:
            for i, column in enumerate(row):
                self.table.setItem(r, i, QTableWidgetItem(str(column)))
            r += 1


def main():
    # Create a Qt application
    app = QApplication(sys.argv)

    # Open a new connection by default
    win = NewConnection()
    win.show()
    win.raise_()
    win.activateWindow()

    # Enter Qt application main loop
    app.exec_()

if __name__ == "__main__":
    main()
