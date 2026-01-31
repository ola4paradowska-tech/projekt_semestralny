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
    QHBoxLayout
)
from PyQt6.QtCore import Qt

class CsvTableViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dane pacjentów")
        self.resize(900, 600)

        self.button = QPushButton("Wczytaj dane")
        self.button.clicked.connect(self.load_csv)

        self.column_select = QComboBox()
        self.order_select = QComboBox()
        self.order_select.addItems(["Rosnąco", "Malejąco"])

        self.sort_button = QPushButton("Sortuj")
        self.sort_button.clicked.connect(self.sort_table)

        sort_layout = QHBoxLayout()
        sort_layout.addWidget(self.column_select)
        sort_layout.addWidget(self.order_select)
        sort_layout.addWidget(self.sort_button)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)

        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addLayout(sort_layout)  # ⬅ TU
        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_csv(self):
        try:
            with open("patients_data_v3.csv", newline="", encoding="utf-8") as file:
                reader = csv.reader(file)
                data = list(reader)

            headers = data[0]
            rows = data[1:]

            self.table.setColumnCount(len(headers))
            self.table.setRowCount(len(rows))
            self.table.setHorizontalHeaderLabels(headers)
            self.column_select.clear()
            self.column_select.addItems(headers)

            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    self.table.setItem(
                        row_idx,
                        col_idx,
                        QTableWidgetItem(value)
                    )

            self.table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    def sort_table(self):
        col_index = self.column_select.currentIndex()
        order_text = self.order_select.currentText()

        order = (
            Qt.SortOrder.AscendingOrder
            if order_text == "Rosnąco"
            else Qt.SortOrder.DescendingOrder
        )

        self.table.sortItems(col_index, order)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CsvTableViewer()
    window.show()
    sys.exit(app.exec())