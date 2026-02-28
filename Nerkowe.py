import sys
import pandas as pd
import locale
locale.setlocale(locale.LC_COLLATE, "pl_PL.UTF-8")
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QStackedWidget,
    QMessageBox, QTableView, QComboBox, QLineEdit, QGridLayout
)
from PyQt6.QtCore import Qt, QAbstractTableModel

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# =========================
# MODEL DANYCH
# =========================

class PandasModel(QAbstractTableModel):
    def __init__(self, df=pd.DataFrame()):
        super().__init__()
        self._df = df

    def update_data(self, df):
        self.layoutAboutToBeChanged.emit()
        self._df = df
        self.layoutChanged.emit()

    def rowCount(self, parent=None):
        return len(self._df)

    def columnCount(self, parent=None):
        return len(self._df.columns)

    def data(self, index, role):
        if not index.isValid():
            return None

        value = self._df.iloc[index.row(), index.column()]

        if role == Qt.ItemDataRole.DisplayRole:
            if isinstance(value, float):
                return f"{value:.2f}"
            return str(value)

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._df.columns[section])
            else:
                return str(section)

    def sort(self, column, order):
        col = self._df.columns[column]
        ascending = order == Qt.SortOrder.AscendingOrder

        self.layoutAboutToBeChanged.emit()

        try:
            numeric_series = pd.to_numeric(self._df[col], errors="coerce")

            if not numeric_series.isna().all():
                sorted_df = self._df.assign(_sort_col=numeric_series) \
                    .sort_values("_sort_col", ascending=ascending) \
                    .drop(columns="_sort_col")
            else:
                sorted_df = self._df.assign(
                    _sort_col=self._df[col].astype(str).map(locale.strxfrm)
                ).sort_values("_sort_col", ascending=ascending) \
                    .drop(columns="_sort_col")

        except:
            sorted_df = self._df.sort_values(col, ascending=ascending)

        self._df = sorted_df.reset_index(drop=True)

        self.layoutChanged.emit()

# =========================
# APLIKACJA
# =========================

class DataApp(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analiza danych")
        self.setGeometry(100, 100, 1300, 800)

        self.original_df = None
        self.filtered_df = None

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # ===== LEWY PANEL =====
        sidebar = QVBoxLayout()

        self.btn_load = QPushButton("Wczytaj plik")
        self.btn_preview = QPushButton("Podgląd danych")
        self.btn_filter = QPushButton("Filtrowanie danych")
        self.btn_stats = QPushButton("Analiza statystyczna")
        self.btn_plots = QPushButton("Wykresy")

        for btn in [
            self.btn_load,
            self.btn_preview,
            self.btn_filter,
            self.btn_stats,
            self.btn_plots,
        ]:
            btn.setFixedHeight(40)
            sidebar.addWidget(btn)

        sidebar.addStretch()

        # ===== STACK =====
        self.stack = QStackedWidget()

        self.preview_page = self.create_preview_page()
        self.filter_page = self.create_filter_page()
        self.stats_page = self.create_stats_page()
        self.plots_page = self.create_plots_page()

        self.stack.addWidget(self.preview_page)
        self.stack.addWidget(self.filter_page)
        self.stack.addWidget(self.stats_page)
        self.stack.addWidget(self.plots_page)

        main_layout.addLayout(sidebar, 1)
        main_layout.addWidget(self.stack, 4)

        # ===== POŁĄCZENIA =====
        self.btn_load.clicked.connect(self.load_file)
        self.btn_preview.clicked.connect(lambda: self.stack.setCurrentWidget(self.preview_page))
        self.btn_filter.clicked.connect(lambda: self.stack.setCurrentWidget(self.filter_page))
        self.btn_stats.clicked.connect(self.show_stats)
        self.btn_plots.clicked.connect(lambda: self.stack.setCurrentWidget(self.plots_page))

    # =========================
    # STRONY
    # =========================

    def create_preview_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        self.preview_view = QTableView()
        self.preview_view.setSortingEnabled(True)

        layout.addWidget(self.preview_view)
        return page

    def create_filter_page(self):
        page = QWidget()
        main_layout = QVBoxLayout(page)

        # ===== GATUNEK + PODPOWIEDŹ W JEDNEJ LINII =====
        species_layout = QHBoxLayout()

        label = QLabel("Gatunek:")
        self.species_combo = QComboBox()
        self.species_combo.addItems(["Wszystkie", "Pies", "Kot", "Koń"])

        help_button = QPushButton("?")
        help_button.setFixedSize(24, 24)
        help_button.setCursor(Qt.CursorShape.PointingHandCursor)
        help_button.clicked.connect(self.show_filter_help)

        species_layout.addWidget(label)
        species_layout.addWidget(self.species_combo)
        species_layout.addWidget(help_button)
        species_layout.addStretch()

        main_layout.addLayout(species_layout)

        # ===== SIATKA 3x3 =====
        grid = QGridLayout()

        self.numeric_filters = {}

        # tu wpisz 9 kolumn, które chcesz filtrować
        numeric_columns = [
            "Mocznik [mg/dl]",
            "Kreatynina [mg/dl]",
            "Fosfor [mg/dl]",
            "Sód [mg/dl]",
            "Potas [mg/dl]",
            "Wapń [mg/dl]",
            "Albuminy [g/dl]",
            "Białko całkowite [g/dl]",
            "Stosunek Sodu do Potasu"
        ]

        row = 0
        col = 0

        for column in numeric_columns:
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(f"{column}")

            grid.addWidget(line_edit, row, col)

            self.numeric_filters[column] = line_edit

            col += 1
            if col == 3:
                col = 0
                row += 1

        main_layout.addLayout(grid)

        # ===== PRZYCISKI =====
        self.apply_button = QPushButton("Zastosuj filtry")
        self.clear_button = QPushButton("Wyczyść filtry")

        main_layout.addWidget(self.apply_button)
        main_layout.addWidget(self.clear_button)

        # ===== TABELA =====
        self.filter_view = QTableView()
        self.filter_view.setSortingEnabled(True)
        main_layout.addWidget(self.filter_view)

        self.apply_button.clicked.connect(self.apply_filter)
        self.clear_button.clicked.connect(self.clear_filters)

        return page

    def create_stats_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        self.stats_view = QTableView()
        layout.addWidget(self.stats_view)

        return page

    def create_plots_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        self.combo_x = QComboBox()
        self.combo_y = QComboBox()
        self.btn_generate_plot = QPushButton("Generuj wykres")

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        layout.addWidget(self.combo_x)
        layout.addWidget(self.combo_y)
        layout.addWidget(self.btn_generate_plot)
        layout.addWidget(self.canvas)

        self.btn_generate_plot.clicked.connect(self.generate_plot)

        return page

    # =========================
    # LOGIKA
    # =========================

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz plik",
            "",
            "Pliki Excel (*.xlsx *.xls);;Pliki CSV (*.csv)"
        )

        if not file_path:
            return

        try:
            if file_path.endswith(".xlsx"):
                df = pd.read_excel(file_path, engine="openpyxl", header=1)
            elif file_path.endswith(".csv"):
                self.data = pd.read_csv(file_path)
            else:
                return

            self.original_df = df
            self.original_df["Gatunek"] = (
                self.original_df["Gatunek"]
                .astype(str)
                .str.strip()
            )
            self.filtered_df = df.copy()

            self.preview_model = PandasModel(self.original_df)
            self.filter_model = PandasModel(self.filtered_df)

            self.preview_view.setModel(self.preview_model)
            self.filter_view.setModel(self.filter_model)

            self.combo_x.clear()
            self.combo_y.clear()
            self.combo_x.addItems(df.columns)
            self.combo_y.addItems(df.columns)

        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    def apply_filter(self):
        if self.original_df is None:
            return

        df = self.original_df.copy()

        species = self.species_combo.currentText()
        if species != "Wszystkie":
            df = df[df["Gatunek"] == species]

        for column, widget in self.numeric_filters.items():
            condition = widget.text().strip()
            if condition:
                df = self.apply_numeric_filter(df, column, condition)

        self.filtered_df = df
        self.filter_model.update_data(self.filtered_df)

    def apply_numeric_filter(self, df, column_name, condition):
        series = pd.to_numeric(df[column_name], errors="coerce")
        parts = condition.split(";")

        for part in parts:
            part = part.strip()

            # zakres
            if "-" in part and not part.startswith("-"):
                try:
                    min_val, max_val = part.split("-")
                    min_val = float(min_val.strip())
                    max_val = float(max_val.strip())

                    df = df[
                        ((series >= min_val) & (series <= max_val))
                        | (series.isna())
                        ]
                except:
                    pass

            elif part.startswith(">"):
                value = float(part[1:])
                df = df[(series > value) | (series.isna())]

            elif part.startswith("<"):
                value = float(part[1:])
                df = df[(series < value) | (series.isna())]

            else:
                value = float(part)
                df = df[(series == value) | (series.isna())]

            series = pd.to_numeric(df[column_name], errors="coerce")

        return df

    def clear_filters(self):
        if self.original_df is None:
            return

        self.species_combo.setCurrentIndex(0)

        for widget in self.numeric_filters.values():
            widget.clear()

        self.filtered_df = self.original_df.copy()
        self.filter_model.update_data(self.filtered_df)

    def show_filter_help(self):
        QMessageBox.information(
            self,
            "Jak działa filtrowanie?",
            "Możliwe formaty:\n\n"
            ">5  — większe niż 5\n"
            "<3  — mniejsze niż 3\n"
            "7   — równe 7\n"
            "4-10 — zakres 4 do 10\n"
            ">5; <10 — wiele warunków\n"
            "4-10; >20 — kombinacje\n\n"
            "Brak danych (NaN) nie jest usuwany."
        )

    def show_stats(self):
        if self.filtered_df is None:
            return

        stats = self.filtered_df.describe()
        self.stats_view.setModel(PandasModel(stats))
        self.stack.setCurrentWidget(self.stats_page)

    def generate_plot(self):
        if self.filtered_df is None:
            return

        x_col = self.combo_x.currentText()
        y_col = self.combo_y.currentText()

        df = self.filtered_df

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.scatter(df[x_col], df[y_col])
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        self.canvas.draw()


# =========================
# START
# =========================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DataApp()
    window.show()
    sys.exit(app.exec())