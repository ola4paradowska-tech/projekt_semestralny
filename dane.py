import pandas as pd

import sys
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QMessageBox
)

class CsvViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Podgląd CSV")
        self.resize(800, 600)

        self.button = QPushButton("Wczytaj dane")
        self.button.clicked.connect(self.load_csv)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.text_area)
        self.setLayout(layout)

    def load_csv(self):
        try:
            with open("patients_data_v3.csv", "r", encoding="utf-8") as f:
                self.text_area.setPlainText(f.read())
        except FileNotFoundError:
            QMessageBox.critical(
                self,
                "Błąd",
                "Nie znaleziono pliku patients_data_v3.csv"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Błąd",
                str(e)
            )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CsvViewer()
    window.show()
    sys.exit(app.exec())