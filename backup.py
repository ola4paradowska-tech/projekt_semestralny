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

    def find_col(self, key):
        key = key.lower()
        for i, h in enumerate(self.headers):
            if key in h.lower():
                return i
        return None

    def load_data(self):
        self.table.setColumnCount(len(self.headers))
        self.table.setRowCount(len(self.data))
        self.table.setHorizontalHeaderLabels(self.headers)

        for r, row in enumerate(self.data):
            for c, value in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(value)))

        self.table.resizeColumnsToContents()


# ===================== FILTER VIEW =====================

class FilterWidget(QWidget):
    def __init__(self, headers, data, go_back):
        super().__init__()

        self.headers = headers
        self.data = data
        self.go_back = go_back

        # --- mapowanie kolumn ---
        self.col_map = {
            "age": self.find_col("wiek"),
            "gender": self.find_col("płeć"),
            "bp": self.find_col("ciśn"),
            "hr": self.find_col("tęt"),
            "symptoms": self.find_col("objaw"),
        }

        # --- LAYOUT ---
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        back_btn = QPushButton("← Wróć")
        back_btn.setFixedWidth(120)
        back_btn.clicked.connect(self.go_back)

        title = QLabel("Filtrowanie danych")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- POLA FILTRÓW ---
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("Wiek (np. <30; 70)")

        self.gender_input = QLineEdit()
        self.gender_input.setPlaceholderText("Płeć (np. kobieta)")

        self.bp_input = QLineEdit()
        self.bp_input.setPlaceholderText("Ciśnienie (np. >120)")

        self.hr_input = QLineEdit()
        self.hr_input.setPlaceholderText("Tętno (np. >80;74)")

        self.symptoms_input = QLineEdit()
        self.symptoms_input.setPlaceholderText("Objawy (np. zmęczenie; nudności)")

        for w in (
            self.age_input,
            self.gender_input,
            self.bp_input,
            self.hr_input,
            self.symptoms_input,
        ):
            w.setFixedWidth(220)

        filter_btn = QPushButton("Zastosuj filtry")
        filter_btn.setFixedWidth(220)
        filter_btn.clicked.connect(self.apply_filter)

        clear_btn = QPushButton("Wyczyść filtry")
        clear_btn.setFixedWidth(220)
        clear_btn.clicked.connect(self.clear_filters)

        self.table = QTableWidget()
        self.table.setSortingEnabled(True)

        self.load_data()

        # --- UKŁAD ---
        layout.addWidget(back_btn)
        layout.addWidget(title)
        layout.addWidget(self.age_input)
        layout.addWidget(self.gender_input)
        layout.addWidget(self.bp_input)
        layout.addWidget(self.hr_input)
        layout.addWidget(self.symptoms_input)
        layout.addWidget(filter_btn)
        layout.addWidget(clear_btn)
        layout.addWidget(self.table)

    # ================= METODY =================

    def find_col(self, fragment):
        fragment = fragment.lower()
        for i, h in enumerate(self.headers):
            if fragment in h.lower():
                return i
        return None

    def load_data(self):
        self.table.setColumnCount(len(self.headers))
        self.table.setRowCount(len(self.data))
        self.table.setHorizontalHeaderLabels(self.headers)

        for r, row in enumerate(self.data):
            for c, value in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(value)))

        self.table.resizeColumnsToContents()

    def parse_numeric_filter(self, text):
        text = text.replace(" ", "")
        for op in (">=", "<=", ">", "<", "="):
            if text.startswith(op):
                try:
                    return op, float(text[len(op):])
                except ValueError:
                    return None, None
        try:
            return "=", float(text)
        except ValueError:
            return None, None

    def match_single_numeric(self, value, raw):
        op, number = self.parse_numeric_filter(raw)
        if op is None:
            return False

        ops = {
            ">": value > number,
            "<": value < number,
            ">=": value >= number,
            "<=": value <= number,
            "=": value == number,
        }

        return ops.get(op, False)

    def match_numeric(self, row, col, raw):
        if not raw.strip():
            return True

        item = self.table.item(row, col)
        if not item:
            return False

        text = item.text()

        # wartość z komórki (liczba lub ciśnienie 120/80 → 120)
        if "/" in text:
            try:
                value = float(text.split("/")[0])
            except ValueError:
                return False
        else:
            digits = "".join(ch for ch in text if ch.isdigit() or ch == ".")
            if not digits:
                return False
            value = float(digits)

        # wiele warunków oddzielonych ;
        parts = [p.strip() for p in raw.split(";") if p.strip()]

        for part in parts:
            if self.match_single_numeric(value, part):
                return True

        return False

    def apply_filter(self):
        for r in range(self.table.rowCount()):
            visible = True

            if self.col_map["age"] is not None and self.age_input.text():
                visible &= self.match_numeric(r, self.col_map["age"], self.age_input.text())

            if self.col_map["gender"] is not None and self.gender_input.text():
                item = self.table.item(r, self.col_map["gender"])
                text = item.text().lower() if item else ""
                visible &= self.gender_input.text().lower() in text

            if self.col_map["bp"] is not None and self.bp_input.text():
                visible &= self.match_numeric(r, self.col_map["bp"], self.bp_input.text())

            if self.col_map["hr"] is not None and self.hr_input.text():
                visible &= self.match_numeric(r, self.col_map["hr"], self.hr_input.text())

            if self.col_map["symptoms"] is not None and self.symptoms_input.text():
                item = self.table.item(r, self.col_map["symptoms"])
                text = item.text().lower() if item else ""
                visible &= self.symptoms_input.text().lower() in text

            self.table.setRowHidden(r, not visible)

    def clear_filters(self):
        self.age_input.clear()
        self.gender_input.clear()
        self.bp_input.clear()
        self.hr_input.clear()
        self.symptoms_input.clear()

        for r in range(self.table.rowCount()):
            self.table.setRowHidden(r, False)


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
