import sys
import csv
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit,
    QMessageBox, QStackedWidget
)
from PyQt6.QtCore import Qt

class NumericItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            return self.text() < other.text()
# ===================== Dane =====================
class PreviewWidget(QWidget):
    def __init__(self, headers, data, go_back):
        super().__init__()
        self.headers = headers
        self.data = data
        self.go_back = go_back

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        back_btn = QPushButton("← Wróć")
        back_btn.setFixedWidth(120)
        back_btn.clicked.connect(self.go_back)

        title = QLabel("Podgląd danych")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)

        self.load_data()

        layout.addWidget(back_btn)
        layout.addWidget(title)
        layout.addWidget(self.table)

    def load_data(self):
        self.table.setColumnCount(len(self.headers))
        self.table.setRowCount(len(self.data))
        self.table.setHorizontalHeaderLabels(self.headers)

        for r, row in enumerate(self.data):
            for c, value in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(value))

        self.table.resizeColumnsToContents()

# ===================== FILTER VIEW =====================

class FilterWidget(QWidget):
    def __init__(self, headers, data, go_back):
        super().__init__()
        self.headers = headers
        self.data = data
        self.go_back = go_back

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        back_btn = QPushButton("← Wróć")
        back_btn.setFixedWidth(120)
        back_btn.clicked.connect(self.go_back)

        title = QLabel("Filtrowanie danych")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.filter_column = QComboBox()
        self.filter_column.addItems(headers)
        self.filter_column.setFixedWidth(200)

        self.filter_value = QLineEdit()
        self.filter_value.setPlaceholderText("np. Female lub 30")
        self.filter_value.setFixedWidth(200)

        filter_btn = QPushButton("Filtruj")
        filter_btn.setFixedWidth(200)
        filter_btn.clicked.connect(self.apply_filter)

        self.table = QTableWidget()
        self.table.setSortingEnabled(True)
        self.load_data()

        layout.addWidget(back_btn)
        layout.addWidget(title)
        layout.addWidget(self.filter_column)
        layout.addWidget(self.filter_value)
        layout.addWidget(filter_btn)
        layout.addWidget(self.table)

    def load_data(self):
        self.table.setColumnCount(len(self.headers))
        self.table.setRowCount(len(self.data))
        self.table.setHorizontalHeaderLabels(self.headers)

        for r, row in enumerate(self.data):
            for c, value in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(value))

        self.table.resizeColumnsToContents()

    def parse_numeric_filter(self, text):
        text = text.replace(" ", "")
        for op in (">=", "<=", ">", "<", "="):
            if text.startswith(op):
                try:
                    return op, float(text[len(op):])
                except ValueError:
                    return None, None
        return None, None

    def apply_filter(self):
        col = self.filter_column.currentIndex()
        raw = self.filter_value.text().strip().lower()

        if not raw:
            return

        op, number = self.parse_numeric_filter(raw)

        for r in range(self.table.rowCount()):
            item = self.table.item(r, col)
            if not item:
                self.table.setRowHidden(r, True)
                continue

            text = item.text().lower()
            show = False

            # --- FILTR LICZBOWY ---
            if op is not None:
                try:
                    value = float(text)
                    if op == ">" and value > number:
                        show = True
                    elif op == "<" and value < number:
                        show = True
                    elif op == ">=" and value >= number:
                        show = True
                    elif op == "<=" and value <= number:
                        show = True
                    elif op == "=" and value == number:
                        show = True
                except ValueError:
                    show = False

            # --- FILTR TEKSTOWY ---
            else:
                show = raw in text

            self.table.setRowHidden(r, not show)


# ===================== MENU VIEW =====================

class MenuWidget(QWidget):
    def __init__(self, callbacks):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        title = QLabel("Funkcje")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        for text, callback in callbacks.items():
            btn = QPushButton(text)
            btn.setFixedWidth(240)
            btn.clicked.connect(callback)
            layout.addWidget(btn)


# ===================== MAIN WINDOW =====================

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analiza danych pacjentów")
        self.resize(1000, 600)

        self.headers = None
        self.data = None

        self.stack = QStackedWidget()

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.stack)

        self.stack.addWidget(self.build_load_screen())

    # ---------- START SCREEN ----------

    def build_load_screen(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn = QPushButton("Wczytaj dane CSV")
        btn.setFixedWidth(240)
        btn.clicked.connect(self.load_csv)

        layout.addWidget(btn)
        return w

    # ---------- DATA LOADING ----------

    def load_csv(self):
        try:
            with open("patients_data_pl.csv", encoding="utf-8") as f:
                rows = list(csv.reader(f))

            self.headers = rows[0]
            self.data = rows[1:]
            self.show_menu()

        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    # ---------- MENU ----------

    def show_menu(self):
        menu = MenuWidget({
            "Podgląd danych": self.open_preview,
            "Filtrowanie danych": self.open_filter,
            "Analiza statystyczna": self.open_stats,
            "Porównanie grup": self.open_compare,
            "Eksport wyników": self.open_export,
        })

        self.stack.addWidget(menu)
        self.stack.setCurrentWidget(menu)

    # ---------- NAVIGATION ----------

    def push(self, widget):
        self.stack.addWidget(widget)
        self.stack.setCurrentWidget(widget)

    def pop(self):
        current = self.stack.currentWidget()
        self.stack.removeWidget(current)
        current.deleteLater()

    # ---------- FEATURES ----------

    def open_filter(self):
        self.push(FilterWidget(self.headers, self.data, self.pop))

    def open_preview(self):
        self.push(PreviewWidget(self.headers, self.data, self.pop))


    def open_stats(self):
        QMessageBox.information(self, "Statystyka", "Tu będzie analiza statystyczna.")

    def open_compare(self):
        QMessageBox.information(self, "Porównanie", "Tu będzie porównanie grup.")

    def open_export(self):
        QMessageBox.information(self, "Eksport", "Tu będzie eksport wyników.")


# ===================== APP START =====================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
