import sys, csv
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QMessageBox, QComboBox, QHBoxLayout, QLineEdit
)

NUMERIC_COLS = {"age", "id_pacjenta", "heartrate"}
OPS = {
    ">":  lambda a, b: a > b,
    "<":  lambda a, b: a < b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "=":  lambda a, b: a == b,
}

class NumericItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            return self.text() < other.text()

class CsvTableViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dane pacjentów")
        self.resize(900, 600)

        self.button = QPushButton("Wczytaj dane")
        self.button.clicked.connect(self.load_csv)

        self.stats_button = QPushButton("Statystyka")
        self.stats_button.clicked.connect(self.open_statistics)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)

        self.filter_column = QComboBox()
        self.filter_value = QLineEdit()
        self.filter_value.setPlaceholderText("Wpisz wartość (np. Female)")

        self.filter_button = QPushButton("Filtruj")
        self.filter_button.clicked.connect(self.apply_filter)

        self.clear_filter_button = QPushButton("Wyczyść filtr")
        self.clear_filter_button.clicked.connect(self.clear_filter)

        self.back_button = QPushButton("Powrót do menu")
        self.back_button.clicked.connect(self.back_to_menu)

        filter_layout = QHBoxLayout()
        for w in (
            self.filter_column, self.filter_value,
            self.filter_button, self.clear_filter_button, self.back_button
        ):
            filter_layout.addWidget(w)

        top_buttons = QHBoxLayout()
        top_buttons.addWidget(self.button)
        top_buttons.addWidget(self.stats_button)

        layout = QVBoxLayout(self)
        layout.addLayout(top_buttons)
        layout.addLayout(filter_layout)
        layout.addWidget(self.table)

        self.set_ui_visible(False)

    def set_ui_visible(self, visible: bool):
        for w in (
            self.filter_column, self.filter_value,
            self.filter_button, self.clear_filter_button,
            self.table, self.back_button
        ):
            w.setVisible(visible)

    def parse_numeric_filter(self, text):
        text = text.replace(" ", "")
        for op in OPS:
            if text.startswith(op):
                try:
                    return op, float(text[len(op):])
                except ValueError:
                    pass
        return None, None

    def load_csv(self):
        try:
            with open("patients_data_pl.csv", encoding="utf-8") as f:
                data = list(csv.reader(f))

            headers, rows = data[0], data[1:]

            self.table.setSortingEnabled(False)
            self.table.setColumnCount(len(headers))
            self.table.setRowCount(len(rows))
            self.table.setHorizontalHeaderLabels(headers)

            self.filter_column.clear()
            self.filter_column.addItems(headers)

            for r, row in enumerate(rows):
                for c, value in enumerate(row):
                    item = NumericItem(value) if headers[c].lower() in NUMERIC_COLS else QTableWidgetItem(value)
                    self.table.setItem(r, c, item)

            self.table.resizeColumnsToContents()
            self.set_ui_visible(True)

            self.button.setText("Dane wczytane")
            self.button.setEnabled(False)
            self.table.setSortingEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    def apply_filter(self):
        col = self.filter_column.currentIndex()
        raw = self.filter_value.text().strip().lower()
        if not raw:
            return

        op, num = self.parse_numeric_filter(raw)

        for row in range(self.table.rowCount()):
            item = self.table.item(row, col)
            if not item:
                self.table.setRowHidden(row, True)
                continue

            text = item.text().lower()
            show = False

            if op:
                try:
                    show = OPS[op](float(text), num)
                except ValueError:
                    pass
            else:
                show = raw in text

            self.table.setRowHidden(row, not show)

    def clear_filter(self):
        self.filter_value.clear()
        for r in range(self.table.rowCount()):
            self.table.setRowHidden(r, False)

    def back_to_menu(self):
        self.set_ui_visible(False)
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.button.setText("Wczytaj dane")
        self.button.setEnabled(True)

    def open_statistics(self):
        QMessageBox.information(self, "Statystyka", "Placeholder statystyk.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CsvTableViewer()
    window.show()
    sys.exit(app.exec())