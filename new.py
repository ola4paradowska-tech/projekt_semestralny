import sys, csv

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QMessageBox, QComboBox, QHBoxLayout, QLineEdit,
    QStackedWidget, QLabel
)

NUMERIC_COLS = {"age", "id_pacjenta", "heartrate"}
OPS = {
    ">":  lambda a, b: a > b,
    "<":  lambda a, b: a < b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "=":  lambda a, b: a == b,
}

class FilterWidget(QWidget):
    def __init__(self, headers, data):
        super().__init__()
        self.headers = headers
        self.data = data

        self.table = QTableWidget()
        self.filter_column = QComboBox()
        self.filter_column.addItems(headers)

        self.filter_value = QLineEdit()
        self.filter_value.setPlaceholderText("np. Female lub >30")

        self.filter_button = QPushButton("Filtruj")
        self.filter_button.clicked.connect(self.apply_filter)

        layout = QVBoxLayout(self)
        layout.addWidget(self.filter_column)
        layout.addWidget(self.filter_value)
        layout.addWidget(self.filter_button)
        layout.addWidget(self.table)

        self.load_data()

    def load_data(self):
        self.table.setColumnCount(len(self.headers))
        self.table.setRowCount(len(self.data))
        self.table.setHorizontalHeaderLabels(self.headers)

        for r, row in enumerate(self.data):
            for c, value in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(value))

    def apply_filter(self):
        col = self.filter_column.currentIndex()
        value = self.filter_value.text().lower()

        for row in range(self.table.rowCount()):
            text = self.table.item(row, col).text().lower()
            self.table.setRowHidden(row, value not in text)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analiza danych pacjentów")
        self.resize(1000, 600)

        self.data = None
        self.headers = None

        self.load_button = QPushButton("Wczytaj dane CSV")
        self.load_button.clicked.connect(self.load_csv)

        self.menu_layout = QVBoxLayout()
        self.menu_layout.addWidget(self.load_button)

        self.stack = QStackedWidget()

        layout = QHBoxLayout(self)
        layout.addLayout(self.menu_layout)
        layout.addWidget(self.stack)

    def load_csv(self):
        with open("patients_data_pl.csv", encoding="utf-8") as f:
            rows = list(csv.reader(f))

        self.headers = rows[0]
        self.data = rows[1:]

        self.build_menu()

    def build_menu(self):
        self.menu_layout.addWidget(QLabel("Funkcje:"))

        self.add_menu_button("Podgląd danych", self.open_preview)
        self.add_menu_button("Filtrowanie danych", self.open_filter)
        self.add_menu_button("Analiza statystyczna", self.open_stats)
        self.add_menu_button("Porównanie grup", self.open_compare)
        self.add_menu_button("Eksport wyników", self.open_export)

    def add_menu_button(self, text, handler):
        btn = QPushButton(text)
        btn.clicked.connect(handler)
        self.menu_layout.addWidget(btn)

    def open_filter(self):
        widget = FilterWidget(self.headers, self.data)
        self.stack.addWidget(widget)
        self.stack.setCurrentWidget(widget)

    def open_preview(self):
        QMessageBox.information(self, "Info", "Podgląd – do zrobienia")

    def open_stats(self):
        QMessageBox.information(self, "Info", "Statystyka – do zrobienia")

    def open_compare(self):
        QMessageBox.information(self, "Info", "Porównanie – do zrobienia")

    def open_export(self):
        QMessageBox.information(self, "Info", "Eksport – do zrobienia")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
