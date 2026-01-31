import sys
import csv
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QMessageBox,
    QComboBox,
    QHBoxLayout,
    QLineEdit
)
from PyQt6.QtCore import Qt

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

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)

        # --- FILTRY ---
        self.filter_column = QComboBox()
        self.filter_value = QLineEdit()
        self.filter_value.setPlaceholderText("Wpisz wartość (np. Female)")

        self.filter_button = QPushButton("Filtruj")
        self.filter_button.clicked.connect(self.apply_filter)

        self.clear_filter_button = QPushButton("Wyczyść filtr")
        self.clear_filter_button.clicked.connect(self.clear_filter)

        self.back_button = QPushButton("Powrót do menu")
        self.back_button.clicked.connect(self.back_to_menu)

        # --- layout filtrów ---
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(self.filter_column)
        filter_layout.addWidget(self.filter_value)
        filter_layout.addWidget(self.filter_button)
        filter_layout.addWidget(self.clear_filter_button)
        filter_layout.addWidget(self.back_button)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)

        # --- menu startowe ---
        self.filter_column.hide()
        self.filter_value.hide()
        self.filter_button.hide()
        self.clear_filter_button.hide()
        self.table.hide()
        self.back_button.hide()

        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addLayout(filter_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_csv(self):
        try:
            with open("patients_data_pl.csv", newline="", encoding="utf-8") as file:
                reader = csv.reader(file)
                data = list(reader)

            headers = data[0]
            rows = data[1:]

            self.table.setSortingEnabled(False)
            self.table.setColumnCount(len(headers))
            self.table.setRowCount(len(rows))
            self.table.setHorizontalHeaderLabels(headers)
            self.filter_column.clear()
            self.filter_column.addItems(headers)

            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    self.table.setItem(
                        row_idx,
                        col_idx,
                        NumericItem(value)
                    )
            self.filter_column.show()
            self.filter_value.show()
            self.filter_button.show()
            self.clear_filter_button.show()

            self.table.resizeColumnsToContents()
            self.table.show()
            self.back_button.show()

            self.button.setText("Dane wczytane")
            self.button.setEnabled(False)
            self.table.setSortingEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    def apply_filter(self):
        col_index = self.filter_column.currentIndex()
        value = self.filter_value.text().strip().lower()

        if not value:
            return

        for row in range(self.table.rowCount()):
            item = self.table.item(row, col_index)
            if item and value in item.text().lower():
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)

    def clear_filter(self):
        self.filter_value.clear()
        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, False)

    def sort_table(self):
        col_index = self.column_select.currentIndex()
        order_text = self.order_select.currentText()

        order = (
            Qt.SortOrder.AscendingOrder
            if order_text == "Rosnąco"
            else Qt.SortOrder.DescendingOrder
        )

        self.table.sortItems(col_index, order)

    def back_to_menu(self):
        self.column_select.hide()
        self.order_select.hide()
        self.sort_button.hide()
        self.table.hide()
        self.back_button.hide()

        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

        self.button.setText("Wczytaj dane")
        self.button.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CsvTableViewer()
    window.show()
    sys.exit(app.exec())