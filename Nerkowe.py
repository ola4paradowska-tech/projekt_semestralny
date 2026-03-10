import sys
import pandas as pd
import numpy as np
import locale
locale.setlocale(locale.LC_COLLATE, "pl_PL.UTF-8")
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QStackedWidget,
    QMessageBox, QTableView, QComboBox, QLineEdit, QGridLayout, QCheckBox
)
from PyQt6.QtCore import Qt, QAbstractTableModel

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_pdf import PdfPages


# =========================
# MODEL DANYCH
# =========================

class PandasModel(QAbstractTableModel):

    def __init__(self, df=pd.DataFrame(), ranges=None):
        super().__init__()
        self._df = df
        self.ranges = ranges or {}

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

            if pd.isna(value):
                return "—"

            if isinstance(value, (int, float)):
                display_value = f"{value:.2f}"
            else:
                display_value = str(value)

            # sprawdzamy tylko jeśli mamy kolumnę Gatunek
            if "Gatunek" in self._df.columns:
                species = str(self._df.iloc[index.row()]["Gatunek"]).strip()
                column_name = self._df.columns[index.column()]

                if (
                        species in self.ranges
                        and column_name in self.ranges[species]
                        and isinstance(value, (int, float))
                ):
                    min_val, max_val = self.ranges[species][column_name]

                    if value < min_val:
                        return display_value + " ↓"
                    elif value > max_val:
                        return display_value + " ↑"

            return display_value

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._df.columns[section])
            else:
                return str(section + 1)

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

class MultiSelectComboBox(QComboBox):

        def __init__(self):
            super().__init__()

            self.setEditable(True)
            self.lineEdit().setReadOnly(True)

            model = self.model()

            model.itemChanged.connect(self.update_text)

        def addItems(self, items):
            for text in items:
                self.addItem(text)

                item = self.model().item(self.count() - 1, 0)
                item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                item.setCheckState(Qt.CheckState.Unchecked)

        def checked_items(self):
            checked = []
            for i in range(self.count()):
                item = self.model().item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    checked.append(item.text())
            return checked

        def update_text(self):
            checked = self.checked_items()
            self.lineEdit().setText(", ".join(checked))


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
        self.ranges = {}

        # STAŁE LISTY
        self.param_names = [
            "Mocznik", "Kreatynina", "Fosfor", "Sód", "Potas",
            "Wapń", "Albuminy", "Białko całkowite", "Stosunek Na/K"
        ]

        self.param_map = {
            "Mocznik": "Mocznik [mg/dl]",
            "Kreatynina": "Kreatynina [mg/dl]",
            "Fosfor": "Fosfor [mg/dl]",
            "Sód": "Sód [mg/dl]",
            "Potas": "Potas [mg/dl]",
            "Wapń": "Wapń [mg/dl]",
            "Albuminy": "Albuminy [g/dl]",
            "Białko całkowite": "Białko całkowite [g/dl]",
            "Stosunek Na/K": "Stosunek Sodu do Potasu"
        }

        self.stats_map = {
            "średnia": "mean",
            "mediana": "median",
            "odchylenie standardowe": "std"
        }
        self.status_list = [
            "Wszystkie",
            "Zdrowy",
            "Łagodnie Chory",
            "Umiarkowanie Chory",
            "Ciężko Chory"
        ]

        self.param_colors = {
            "Mocznik": "#E8D52E",  # żółty (gold)
            "Kreatynina": "#B32222",  # czerwony
            "Fosfor": "#4E8BCF",  # niebieski
            "Sód": "#E3983B",  # pomarańczowy
            "Potas": "#D184CF",  # różowy
            "Wapń": "#6BD6CB",  # turkusowy
            "Albuminy": "#D1DB63",  # zielono-żółty
            "Białko całkowite": "#297347",  # ciemno zielony
            "Stosunek Na/K": "#7F7F7F"  # szary
        }

        self.load_ranges()
        self.init_ui()

    def load_ranges(self):
        try:
            ranges_df = pd.read_excel("zakresy.xlsx", engine="openpyxl", header=1)
        except Exception:
            self.ranges = {}
            return

        ranges_df.columns = ranges_df.columns.str.strip()

        self.ranges = {}

        # grupujemy po gatunku
        for species in ranges_df["Gatunek"].unique():

            species_rows = ranges_df[ranges_df["Gatunek"] == species]

            min_row = species_rows[species_rows["Zakres"] == "Min"]
            max_row = species_rows[species_rows["Zakres"] == "Max"]

            if min_row.empty or max_row.empty:
                continue

            min_row = min_row.iloc[0]
            max_row = max_row.iloc[0]

            self.ranges.setdefault(species, {})

            for column in ranges_df.columns:
                if column in ["Gatunek", "Zakres"]:
                    continue

                try:
                    min_val = float(str(min_row[column]).replace(",", "."))
                    max_val = float(str(max_row[column]).replace(",", "."))

                    self.ranges[species][column] = (min_val, max_val)
                except:
                    continue

    def calculate_status(self, df):

        statuses = []

        for _, row in df.iterrows():
            species = str(row["Gatunek"]).strip()

            if species not in self.ranges:
                statuses.append("Brak zakresu")
                continue

            abnormal_count = 0

            for param, (min_val, max_val) in self.ranges[species].items():
                if param not in df.columns:
                    continue

                try:
                    value = float(row[param])
                except:
                    continue

                if value < min_val or value > max_val:
                    abnormal_count += 1

            # klasyfikacja
            if abnormal_count == 0:
                statuses.append("Zdrowy")
            elif abnormal_count == 1:
                statuses.append("Łagodnie Chory")
            elif 2 <= abnormal_count <= 4:
                statuses.append("Umiarkowanie Chory")
            else:
                statuses.append("Ciężko Chory")

        df_with_status = df.copy()
        df_with_status["Status"] = statuses

        return df_with_status

    def calculate_abnormal_percent(self, df, params):

        results = []

        for species, group in df.groupby("Gatunek"):

            for param in params:

                if param not in self.ranges.get(species, {}):
                    continue

                min_val, max_val = self.ranges[species][param]

                values = pd.to_numeric(group[param], errors="coerce").dropna()

                if len(values) == 0:
                    continue

                above = (values > max_val).sum()
                below = (values < min_val).sum()
                total = len(values)

                results.append({
                    "Gatunek": species,
                    "Parametr": param.split("[")[0].strip(),
                    "% powyżej normy": round(100 * above / total, 2),
                    "% poniżej normy": round(100 * below / total, 2)
                })

        return pd.DataFrame(results)

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # ===== LEWY PANEL =====
        sidebar = QVBoxLayout()

        self.btn_load = QPushButton("Wczytaj plik")
        self.btn_preview = QPushButton("Podgląd danych")
        self.btn_filter = QPushButton("Filtrowanie danych")
        self.btn_stats = QPushButton("Analiza statystyczna")
        self.btn_plots = QPushButton("Wykresy")
        self.btn_export_csv = QPushButton("Eksport CSV")
        self.btn_export_pdf = QPushButton("Eksport PDF")

        for btn in [
            self.btn_load,
            self.btn_preview,
            self.btn_filter,
            self.btn_stats,
            self.btn_plots,
            self.btn_export_csv,
            self.btn_export_pdf
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
        self.btn_export_csv.clicked.connect(self.export_csv)
        self.btn_export_pdf.clicked.connect(self.export_pdf)

    def calculate_stats(self):

        if self.filtered_df is None:
            return

        df = self.original_df.copy()

        species = self.stats_species.checked_items()
        status = self.stats_status.currentText()
        params_gui = self.stats_param.checked_items()
        stats_gui = self.stats_stats.checked_items()

        params = [self.param_map[p] for p in params_gui]
        stats = [self.stats_map[s] for s in stats_gui]

        if not params:
            QMessageBox.warning(self, "Błąd", "Wybierz przynajmniej jeden parametr")
            return

        if not stats:
            QMessageBox.warning(self, "Błąd", "Wybierz przynajmniej jedną statystykę")
            return

        if species:
            df = df[df["Gatunek"].isin(species)]

        if status != "Wszystkie":
            df = df[df["Status"] == status]

        if df.empty:
            QMessageBox.warning(self, "Brak danych", "Brak danych dla wybranych filtrów")
            return

        for p in params:
            df[p] = pd.to_numeric(df[p], errors="coerce")

        result = df.groupby("Gatunek")[params].agg(stats)

        if result.empty:
            QMessageBox.warning(self, "Brak danych", "Nie można policzyć statystyk")
            return

        abnormal = self.calculate_abnormal_percent(df, params)

        result = result.stack(level=0, future_stack=True).reset_index()
        result = result.rename(columns={"level_1": "Parametr"})
        result["Parametr"] = result["Parametr"].str.split("[", regex=False).str[0].str.strip()

        stat_labels = {
            "mean": "średnia",
            "median": "mediana",
            "std": "odchylenie standardowe"
        }

        result = result.rename(columns=stat_labels)
        result = result.sort_values(["Parametr", "Gatunek"]).reset_index(drop=True)

        if not abnormal.empty:
            result = result.merge(
                abnormal,
                on=["Gatunek", "Parametr"],
                how="left"
            )

        self.stats_view.setModel(PandasModel(result))

    def generate_line_plot(self):

        if self.filtered_df is None:
            return

        df = self.original_df.copy()

        species = self.line_species.currentText()
        x_gui = self.line_x_param.currentText()
        y_params_gui = self.line_y_params.checked_items()
        status = self.line_status.currentText()

        if len(y_params_gui) == 0:
            QMessageBox.warning(self, "Błąd", "Wybierz przynajmniej jeden parametr Y")
            return
        if x_gui in y_params_gui:
            QMessageBox.warning(self, "Błąd", "Parametr X nie może być jednocześnie parametrem Y")
            return

        df = df[df["Gatunek"] == species]

        if status != "Wszystkie":
            df = df[df["Status"] == status]

        x_param = self.param_map[x_gui]

        self.line_figure.clear()
        ax = self.line_figure.add_subplot(111)

        x = pd.to_numeric(df[x_param], errors="coerce")

        for param_gui in y_params_gui:

            param = self.param_map[param_gui]

            y = pd.to_numeric(df[param], errors="coerce")

            data = pd.DataFrame({"x": x, "y": y}).dropna()
            if self.line_remove_outliers.isChecked():
                data = self.remove_outliers_iqr(data, "x", "y")
            if len(data) < 2:
                continue

            x_valid = data["x"]
            y_valid = data["y"]

            # punkty pomiarowe
            color = self.param_colors.get(param_gui, "black")

            ax.scatter(x_valid, y_valid, color=color, label=param_gui)

            # linia regresji
            coef = np.polyfit(x_valid, y_valid, 1)
            poly = np.poly1d(coef)

            x_line = np.linspace(x_valid.min(), x_valid.max(), 100)
            y_line = poly(x_line)

            ax.plot(x_line, y_line, color=color)

        ax.set_xlabel(x_gui)
        ax.set_ylabel("Stężenie [mg/dl]")
        ax.legend()
        ax.grid(True)

        self.line_canvas.draw()

    def remove_outliers_iqr(self, df, x_col, y_col):

        Q1_x = df[x_col].quantile(0.25)
        Q3_x = df[x_col].quantile(0.75)
        IQR_x = Q3_x - Q1_x

        Q1_y = df[y_col].quantile(0.25)
        Q3_y = df[y_col].quantile(0.75)
        IQR_y = Q3_y - Q1_y

        mask = (
                (df[x_col] >= Q1_x - 1.5 * IQR_x) &
                (df[x_col] <= Q3_x + 1.5 * IQR_x) &
                (df[y_col] >= Q1_y - 1.5 * IQR_y) &
                (df[y_col] <= Q3_y + 1.5 * IQR_y)
        )

        return df[mask]

    def generate_bar_plot(self):

        if self.filtered_df is None:
            return

        df = self.original_df.copy()

        param_gui = self.bar_param.currentText()
        status = self.bar_status.currentText()

        param = self.param_map[param_gui]

        if status != "Wszystkie":
            df = df[df["Status"] == status]

        df[param] = pd.to_numeric(df[param], errors="coerce")

        stats = df.groupby("Gatunek")[param].agg(["mean", "std"])

        self.bar_figure.clear()
        ax = self.bar_figure.add_subplot(111)

        color = self.param_colors.get(param_gui, "gray")

        ax.bar(
            stats.index,
            stats["mean"],
            yerr=stats["std"],
            capsize=5,
            color=color
        )

        ax.set_title(param_gui)
        ax.set_ylabel("Średnia ± odchylenie standardowe")

        self.bar_canvas.draw()

    def generate_box_plot(self):

        if self.filtered_df is None:
            return

        df = self.original_df.copy()

        param_gui = self.box_param.currentText()
        status = self.box_status.currentText()

        param = self.param_map[param_gui]

        if status != "Wszystkie":
            df = df[df["Status"] == status]

        self.box_figure.clear()
        ax = self.box_figure.add_subplot(111)

        data = []
        species_list = []

        for species, group in df.groupby("Gatunek"):
            values = pd.to_numeric(group[param], errors="coerce").dropna()

            data.append(values)
            species_list.append(species)

        color = self.param_colors.get(param_gui, "gray")

        box = ax.boxplot(
            data,
            tick_labels=species_list,
            patch_artist=True,
            medianprops=dict(color="black", linewidth=2)
        )

        for patch in box['boxes']:
            patch.set_facecolor(color)

        ax.set_title(param_gui)

        if param_gui == "Stosunek Na/K":
            ax.set_ylabel("Stosunek Na/K")
        else:
            ax.set_ylabel("Stężenie [mg/dl]")
        ax.grid(axis="y", linestyle="--", alpha=0.6)

        if param_gui == "Stosunek Na/K":
            ax.set_ylim(0, 50)

        self.box_canvas.draw()

    def update_line_y_params(self):

        selected_x = self.line_x_param.currentText()

        self.line_y_params.clear()

        params = [p for p in self.param_names if p != "Stosunek Na/K"]

        if selected_x in params:
            params.remove(selected_x)

        self.line_y_params.addItems(params)

    def export_csv(self):

        if self.filtered_df is None:
            QMessageBox.warning(self, "Błąd", "Brak danych do eksportu")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Zapisz CSV",
            "",
            "CSV (*.csv)"
        )

        if not path:
            return

        try:
            self.filtered_df.to_csv(path, index=False)
            QMessageBox.information(self, "Sukces", "Dane zapisane do CSV")

        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    def export_pdf(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Zapisz wykres",
            "",
            "PDF (*.pdf)"
        )

        if not path:
            return

        try:

            with PdfPages(path) as pdf:

                if hasattr(self, "line_figure") and self.line_figure.axes:
                    pdf.savefig(self.line_figure)

                elif hasattr(self, "bar_figure") and self.bar_figure.axes:
                    pdf.savefig(self.bar_figure)

                elif hasattr(self, "box_figure") and self.box_figure.axes:
                    pdf.savefig(self.box_figure)

                else:
                    QMessageBox.warning(self, "Błąd", "Brak wygenerowanego wykresu")
                    return

            QMessageBox.information(self, "Sukces", "Wykres zapisany do PDF")

        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))
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

        self.status_combo = QComboBox()
        self.status_combo.addItems(self.status_list)

        species_layout.addWidget(QLabel("Stan:"))
        species_layout.addWidget(self.status_combo)

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

        controls = QHBoxLayout()

        self.stats_species = MultiSelectComboBox()
        self.stats_species.addItems(["Pies", "Kot", "Koń"])


        self.stats_param = MultiSelectComboBox()
        self.stats_param.addItems(self.param_names)

        self.stats_stats = MultiSelectComboBox()
        self.stats_stats.addItems(["średnia", "mediana", "odchylenie standardowe"])

        self.stats_status = QComboBox()
        self.stats_status.addItems(self.status_list)

        self.btn_stats_calc = QPushButton("Oblicz")

        controls.addWidget(QLabel("Gatunek"))
        controls.addWidget(self.stats_species)

        controls.addWidget(QLabel("Status"))
        controls.addWidget(self.stats_status)

        controls.addWidget(QLabel("Parametry"))
        controls.addWidget(self.stats_param)

        controls.addWidget(QLabel("Statystyki"))
        controls.addWidget(self.stats_stats)

        controls.addWidget(self.btn_stats_calc)

        layout.addLayout(controls)

        self.stats_view = QTableView()
        self.stats_view.setSortingEnabled(True)

        layout.addWidget(self.stats_view)

        self.btn_stats_calc.clicked.connect(self.calculate_stats)

        return page

    def create_plots_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)

        self.plot_stack = QStackedWidget()

        # ===== MENU WYBORU WYKRESU =====
        menu_page = QWidget()
        menu_layout = QVBoxLayout(menu_page)
        self.plot_menu_page = menu_page

        self.btn_plot_line = QPushButton("Wykres liniowy\n(zależność parametrów)")
        self.btn_plot_bar = QPushButton("Wykres słupkowy\n(porównanie gatunków)")
        self.btn_plot_box = QPushButton("Wykres pudełkowy\n(rozkład parametrów)")

        for btn in [self.btn_plot_line, self.btn_plot_bar, self.btn_plot_box]:
            btn.setMinimumHeight(80)
            menu_layout.addWidget(btn)

        menu_layout.addStretch()

        # ===== STRONA LINIOWA =====
        self.line_page = self.generate_line_plot_page()

        # ===== STRONA SŁUPKOWA =====
        self.bar_page = self.generate_bar_plot_page()

        # ===== STRONA PUDEŁKOWA =====
        self.box_page = self.generate_box_plot_page()

        # ===== DODANIE DO STACK =====
        self.plot_stack.addWidget(menu_page)
        self.plot_stack.addWidget(self.line_page)
        self.plot_stack.addWidget(self.bar_page)
        self.plot_stack.addWidget(self.box_page)

        layout.addWidget(self.plot_stack)

        # ===== POŁĄCZENIA =====
        self.btn_plot_line.clicked.connect(lambda: self.plot_stack.setCurrentWidget(self.line_page))
        self.btn_plot_bar.clicked.connect(lambda: self.plot_stack.setCurrentWidget(self.bar_page))
        self.btn_plot_box.clicked.connect(lambda: self.plot_stack.setCurrentWidget(self.box_page))

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
                df = pd.read_csv(file_path)

            else:
                return

            df["Gatunek"] = df["Gatunek"].astype(str).str.strip()

            self.original_df = self.calculate_status(df)
            self.filtered_df = self.original_df.copy()
            self.preview_model = PandasModel(self.original_df, self.ranges)
            self.filter_model = PandasModel(self.filtered_df, self.ranges)

            self.preview_view.setModel(self.preview_model)
            self.filter_view.setModel(self.filter_model)

        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    def apply_filter(self):
        if self.original_df is None:
            return

        df = self.original_df.drop(columns=["Status"], errors="ignore").copy()

        # Gatunek
        species = self.species_combo.currentText()
        if species != "Wszystkie":
            df = df[df["Gatunek"] == species]

        # Filtry liczbowe
        for column, widget in self.numeric_filters.items():
            condition = widget.text().strip()
            if condition:
                df = self.apply_numeric_filter(df, column, condition)

        # Liczymy status
        df = self.calculate_status(df)

        # Filtrujemy po nowym statusie (4 poziomy)
        status = self.status_combo.currentText()
        if status != "Wszystkie":
            df = df[df["Status"] == status]

        self.filtered_df = df
        self.filter_model.update_data(self.filtered_df)

    def apply_numeric_filter(self, df, column_name, condition):
        series = pd.to_numeric(df[column_name], errors="coerce")
        parts = [p.strip() for p in condition.split(";") if p.strip()]

        mask = pd.Series(False, index=df.index)

        for part in parts:

            # zakres
            if "-" in part and not part.startswith("-"):
                try:
                    min_val, max_val = part.split("-")
                    min_val = float(min_val.strip())
                    max_val = float(max_val.strip())
                    mask |= (series >= min_val) & (series <= max_val)
                except:
                    continue

            elif part.startswith(">"):
                try:
                    value = float(part[1:])
                    mask |= series > value
                except:
                    continue

            elif part.startswith("<"):
                try:
                    value = float(part[1:])
                    mask |= series < value
                except:
                    continue

            else:
                try:
                    value = float(part)
                    mask |= series == value
                except:
                    continue

        return df[mask | series.isna()]

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
        self.stack.setCurrentWidget(self.stats_page)

    def generate_line_plot_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)

        controls = QHBoxLayout()
        self.btn_line_back = QPushButton("← Powrót")
        layout.addWidget(self.btn_line_back)
        self.line_species = QComboBox()
        self.line_species.addItems(["Pies", "Kot", "Koń"])

        line_params = [p for p in self.param_names if p != "Stosunek Na/K"]

        self.line_x_param = QComboBox()
        self.line_x_param.addItems(line_params)

        self.line_y_params = MultiSelectComboBox()
        self.line_y_params.addItems(line_params)

        self.line_status = QComboBox()
        self.line_status.addItems(self.status_list)

        self.btn_line_generate = QPushButton("Generuj wykres")

        self.line_remove_outliers = QCheckBox("Usuń wartości odstające")
        controls.addWidget(self.line_remove_outliers)

        controls.addWidget(QLabel("Gatunek"))
        controls.addWidget(self.line_species)

        controls.addWidget(QLabel("Parametr X"))
        controls.addWidget(self.line_x_param)

        controls.addWidget(QLabel("Parametry Y"))
        controls.addWidget(self.line_y_params)

        controls.addWidget(QLabel("Status"))
        controls.addWidget(self.line_status)

        controls.addWidget(self.btn_line_generate)

        layout.addLayout(controls)

        self.line_x_param.currentTextChanged.connect(self.update_line_y_params)

        self.line_figure = Figure()
        self.line_canvas = FigureCanvas(self.line_figure)

        layout.addWidget(self.line_canvas)

        self.btn_line_generate.clicked.connect(self.generate_line_plot)
        self.btn_line_back.clicked.connect(lambda: self.plot_stack.setCurrentIndex(0))
        return page

    def generate_bar_plot_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)
        self.btn_bar_back = QPushButton("← Powrót")
        layout.addWidget(self.btn_bar_back)
        controls = QHBoxLayout()

        self.bar_param = QComboBox()
        self.bar_param.addItems(self.param_names)

        self.bar_status = QComboBox()
        self.bar_status.addItems(self.status_list)

        self.btn_bar_generate = QPushButton("Generuj wykres")

        controls.addWidget(QLabel("Parametr"))
        controls.addWidget(self.bar_param)

        controls.addWidget(QLabel("Status"))
        controls.addWidget(self.bar_status)

        controls.addWidget(self.btn_bar_generate)

        layout.addLayout(controls)

        self.bar_figure = Figure()
        self.bar_canvas = FigureCanvas(self.bar_figure)

        layout.addWidget(self.bar_canvas)

        self.btn_bar_generate.clicked.connect(self.generate_bar_plot)
        self.btn_bar_back.clicked.connect(lambda: self.plot_stack.setCurrentIndex(0))
        return page

    def generate_box_plot_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)

        controls = QHBoxLayout()
        self.btn_box_back = QPushButton("← Powrót")
        layout.addWidget(self.btn_box_back)
        self.box_param = QComboBox()
        self.box_param.addItems(self.param_names)

        self.box_status = QComboBox()
        self.box_status.addItems(self.status_list)

        self.btn_box_generate = QPushButton("Generuj wykres")

        controls.addWidget(QLabel("Parametr"))
        controls.addWidget(self.box_param)

        controls.addWidget(QLabel("Status"))
        controls.addWidget(self.box_status)

        controls.addWidget(self.btn_box_generate)

        layout.addLayout(controls)

        self.box_figure = Figure()
        self.box_canvas = FigureCanvas(self.box_figure)

        layout.addWidget(self.box_canvas)

        self.btn_box_generate.clicked.connect(self.generate_box_plot)
        self.btn_box_back.clicked.connect(lambda: self.plot_stack.setCurrentIndex(0))
        return page


# =========================
# START
# =========================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DataApp()
    window.show()
    sys.exit(app.exec())