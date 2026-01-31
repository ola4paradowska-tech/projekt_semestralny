import sys
import csv
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QMessageBox
)

class CsvTableViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dane pacjentów")
        self.resize(900, 600)

        self.button = QPushButton("Wczytaj dane")
        self.button.clicked.connect(self.load_csv)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)

        layout = QVBoxLayout()
        layout.addWidget(self.button)
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CsvTableViewer()
    window.show()
    sys.exit(app.exec())