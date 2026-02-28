import sys
import os
import pandas as pd

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QStackedWidget,
    QMessageBox, QTableView, QComboBox
)
from PyQt6.QtCore import Qt, QAbstractTableModel

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


#MODEL DANYCH - JAK SĄ POBIERANE Z TABELI
class PandasModel(QAbstractTableModel):
    def __init__(self, df=pd.DataFrame()):
        super().__init__()
        self._df = df

    def rowCount(self, parent=None):
        return len(self._df)

    def columnCount(self, parent=None):
        return len(self._df.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._df.iloc[index.row(), index.column()]
            if isinstance(value, float):
                return f"{value:.1f}"
            return str(value)

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._df.columns[section])
            else:
                return str(self._df.index[section])


#GŁÓWNA APLIKACJA
class DataApp(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analiza danych")
        self.setGeometry(100, 100, 1300, 800)

        self.data = None
        self.filtered_data = None

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

#LEWY PANEL
        sidebar = QVBoxLayout()

        self.btn_load = QPushButton("Wczytaj plik")
        self.btn_preview = QPushButton("Podgląd danych")
        self.btn_filter = QPushButton("Filtrowanie danych")
        self.btn_stats = QPushButton("Analiza statystyczna")
        self.btn_plots = QPushButton("Wykresy")
        self.btn_export = QPushButton("Eksport PDF")

        for btn in [
            self.btn_load,
            self.btn_preview,
            self.btn_filter,
            self.btn_stats,
            self.btn_plots,
            self.btn_export
        ]:
            btn.setFixedHeight(40)
            sidebar.addWidget(btn)

        sidebar.addStretch()

#STACK - żEBY BYŁY WIDOCZNE PO KLIKNIĘCIU PANELI
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

#POŁĄCZENIA - PRZEŁĄCZA STAKI
        self.btn_load.clicked.connect(self.load_file)
        self.btn_preview.clicked.connect(lambda: self.stack.setCurrentWidget(self.preview_page))
        self.btn_filter.clicked.connect(lambda: self.stack.setCurrentWidget(self.filter_page))
        self.btn_stats.clicked.connect(self.show_stats)
        self.btn_plots.clicked.connect(lambda: self.stack.setCurrentWidget(self.plots_page))
        self.btn_export.clicked.connect(self.export_pdf)

#STRONY - TWORZY PODSTRONY DLA KOLUMN

    def create_preview_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        self.preview_view = QTableView()
        self.preview_view.setSortingEnabled(True)

        layout.addWidget(self.preview_view)
        page.setLayout(layout)
        return page

    def create_filter_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        self.filter_view = QTableView()
        self.filter_view.setSortingEnabled(True)
        self.filter_view.horizontalHeader().setSectionsMovable(True)

        layout.addWidget(self.filter_view)
        page.setLayout(layout)
        return page

    def create_stats_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        self.stats_view = QTableView()

        layout.addWidget(self.stats_view)
        page.setLayout(layout)
        return page

    def create_plots_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        self.combo_x = QComboBox()
        self.combo_y = QComboBox()
        self.btn_generate_plot = QPushButton("Generuj wykres")

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        layout.addWidget(self.combo_x)
        layout.addWidget(self.combo_y)
        layout.addWidget(self.btn_generate_plot)
        layout.addWidget(self.canvas)

        page.setLayout(layout)

        self.btn_generate_plot.clicked.connect(self.generate_plot)

        return page

#WCZYTANIE PLIKU

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
                self.data = pd.read_excel(file_path, engine="openpyxl", header=1)
            elif file_path.endswith(".csv"):
                self.data = pd.read_csv(file_path)

            self.filtered_data = self.data.copy()

            model = PandasModel(self.data)
            self.preview_view.setModel(model)
            self.filter_view.setModel(PandasModel(self.filtered_data))

            self.combo_x.clear()
            self.combo_y.clear()
            self.combo_x.addItems(self.data.columns)
            self.combo_y.addItems(self.data.columns)

        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))

    def show_stats(self):
        if self.data is None:
            return

        stats = self.data.describe()
        self.stats_view.setModel(PandasModel(stats))
        self.stack.setCurrentWidget(self.stats_page)

    def generate_plot(self):
        if self.data is None:
            return

        x_col = self.combo_x.currentText()
        y_col = self.combo_y.currentText()

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.scatter(self.data[x_col], self.data[y_col])
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        self.canvas.draw()

    def export_pdf(self):
        if self.data is None:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Zapisz PDF",
            "",
            "PDF Files (*.pdf)"
        )

        if not file_path:
            return

        doc = SimpleDocTemplate(file_path)
        elements = []

        styles = getSampleStyleSheet()
        elements.append(Paragraph("Eksport danych", styles['Heading1']))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph(str(self.data.head()), styles['Normal']))

        doc.build(elements)


# ================= START =================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DataApp()
    window.show()
    sys.exit(app.exec())