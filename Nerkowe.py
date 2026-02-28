import sys
import os
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QTableWidget,
    QTableWidgetItem, QStackedWidget, QMessageBox
)
from PyQt6.QtCore import Qt

class DataApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analiza danych")
        self.setGeometry(100, 100, 1200, 700)

        self.data = None

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # LEWY PANEL (STAŁE MENU)
        self.sidebar = QVBoxLayout()

        self.btn_load = QPushButton("Wybierz folder")
        self.btn_preview = QPushButton("Podgląd danych")
        self.btn_filter = QPushButton("Filtrowanie danych")
        self.btn_stats = QPushButton("Analiza statystyczna")
        self.btn_compare = QPushButton("Porównanie grup")
        self.btn_export = QPushButton("Eksport wyników")

        for btn in [
            self.btn_load,
            self.btn_preview,
            self.btn_filter,
            self.btn_stats,
            self.btn_compare,
            self.btn_export
        ]:
            btn.setFixedHeight(40)
            self.sidebar.addWidget(btn)

        self.sidebar.addStretch()

        # PRAWA CZĘŚĆ (OBSZAR DANYCH)
        self.content_area = QVBoxLayout()
        self.content_label = QLabel("Tutaj będą wyświetlane dane")
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.table = QTableWidget()

        self.content_area.addWidget(self.content_label)
        self.content_area.addWidget(self.table)

        # DODANIE DO GŁÓWNEGO UKŁADU
        main_layout.addLayout(self.sidebar, 1)
        main_layout.addLayout(self.content_area, 4)

        # POŁĄCZENIA
        self.btn_load.clicked.connect(self.load_folder)
        self.btn_preview.clicked.connect(self.preview_data)
        self.btn_stats.clicked.connect(self.show_statistics)

    def load_folder(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz plik",
            "",
            "Pliki Excel (*.xlsx *.xls);;Pliki CSV (*.csv)"
        )

        if not file_path:
            return

        try:
            if file_path.lower().endswith(".xlsx"):
                self.data = pd.read_excel(file_path, engine="openpyxl", header=1)
            elif file_path.lower().endswith(".xls"):
                self.data = pd.read_excel(file_path)
            elif file_path.lower().endswith(".csv"):
                self.data = pd.read_csv(file_path)
            else:
                QMessageBox.warning(self, "Błąd", "Nieobsługiwany format pliku")
                return

            self.content_label.setText(
                f"Wczytano plik: {os.path.basename(file_path)}"
            )

            return

        except Exception as e:
            QMessageBox.critical(self, "Błąd wczytywania", str(e))
            return

    def preview_data(self):
        if self.data is None:
            return

        self.table.setRowCount(len(self.data))
        self.table.setColumnCount(len(self.data.columns))
        self.table.setHorizontalHeaderLabels(self.data.columns)

        for row in range(len(self.data)):
            for col in range(len(self.data.columns)):
                value = self.data.iat[row, col]

                if isinstance(value, float):
                    display_value = f"{value:.1f}"
                else:
                    display_value = str(value)

                self.table.setItem(row, col, QTableWidgetItem(display_value))

    def show_statistics(self):
        if self.data is None:
            return

        stats = self.data.describe()
        self.table.setRowCount(len(stats))
        self.table.setColumnCount(len(stats.columns))
        self.table.setHorizontalHeaderLabels(stats.columns)
        self.table.setVerticalHeaderLabels(stats.index.astype(str))

        for row in range(len(stats)):
            for col in range(len(stats.columns)):
                self.table.setItem(
                    row,
                    col,
                    QTableWidgetItem(str(round(stats.iat[row, col], 4)))
                )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DataApp()
    window.show()
    sys.exit(app.exec())