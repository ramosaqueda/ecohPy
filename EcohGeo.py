import sys
import os
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import simplekml
import random
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, 
                             QLabel, QComboBox, QDoubleSpinBox, QCheckBox, QDialog, QColorDialog,
                             QDateTimeEdit)
from PyQt5.QtCore import Qt, QUrl, QDateTime
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QColor

class MapWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Mapa')
        layout = QVBoxLayout()
        self.map_view = QWebEngineView()
        layout.addWidget(self.map_view)
        self.setLayout(layout)
        self.resize(800, 600)

class CoordPlotter(QWidget):
    def __init__(self):
        super().__init__()
        self.df = None
        self.map = None
        self.marker_color = "#3388ff"  # Default marker color
        self.date_column = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('ECOH TOOLS, Geoposicionador de Coordenada Ver 1.0 By Rafo')
        layout = QVBoxLayout()

        self.upload_btn = QPushButton('Subir archivo')
        self.upload_btn.clicked.connect(self.upload_file)
        layout.addWidget(self.upload_btn)

        filter_layout = QHBoxLayout()
        self.min_lat = QDoubleSpinBox(minimum=-90, maximum=90, value=-90)
        self.max_lat = QDoubleSpinBox(minimum=-90, maximum=90, value=90)
        self.min_lon = QDoubleSpinBox(minimum=-180, maximum=180, value=-180)
        self.max_lon = QDoubleSpinBox(minimum=-180, maximum=180, value=180)
        filter_layout.addWidget(QLabel('Lat min:'))
        filter_layout.addWidget(self.min_lat)
        filter_layout.addWidget(QLabel('Lat max:'))
        filter_layout.addWidget(self.max_lat)
        filter_layout.addWidget(QLabel('Lon min:'))
        filter_layout.addWidget(self.min_lon)
        filter_layout.addWidget(QLabel('Lon max:'))
        filter_layout.addWidget(self.max_lon)
        layout.addLayout(filter_layout)

        date_filter_layout = QHBoxLayout()
        self.date_column_combo = QComboBox()
        self.date_column_combo.currentTextChanged.connect(self.update_date_filter)
        date_filter_layout.addWidget(QLabel('Columna de fecha:'))
        date_filter_layout.addWidget(self.date_column_combo)
        self.min_date = QDateTimeEdit(calendarPopup=True)
        self.max_date = QDateTimeEdit(calendarPopup=True)
        self.min_date.setDateTime(QDateTime.currentDateTime().addYears(-1))
        self.max_date.setDateTime(QDateTime.currentDateTime())
        date_filter_layout.addWidget(QLabel('Fecha min:'))
        date_filter_layout.addWidget(self.min_date)
        date_filter_layout.addWidget(QLabel('Fecha max:'))
        date_filter_layout.addWidget(self.max_date)
        layout.addLayout(date_filter_layout)

        self.label_column = QComboBox()
        layout.addWidget(QLabel('Columna para etiquetas:'))
        layout.addWidget(self.label_column)

        self.filter_btn = QPushButton('Aplicar filtro')
        self.filter_btn.clicked.connect(self.apply_filter)
        layout.addWidget(self.filter_btn)

        self.new_window_cb = QCheckBox('Abrir mapa en nueva ventana')
        layout.addWidget(self.new_window_cb)

        self.use_clustering_cb = QCheckBox('Usar agrupación de marcadores')
        self.use_clustering_cb.setChecked(True)
        layout.addWidget(self.use_clustering_cb)

        color_layout = QHBoxLayout()
        self.color_btn = QPushButton('Seleccionar color de marcadores')
        self.color_btn.clicked.connect(self.select_color)
        color_layout.addWidget(self.color_btn)
        self.random_color_cb = QCheckBox('Usar colores aleatorios')
        color_layout.addWidget(self.random_color_cb)
        layout.addLayout(color_layout)

        self.download_kmz_btn = QPushButton('Descargar KMZ')
        self.download_kmz_btn.clicked.connect(self.download_kmz)
        layout.addWidget(self.download_kmz_btn)

        self.status_label = QLabel('Esperando archivo...')
        layout.addWidget(self.status_label)

        self.map_view = QWebEngineView()
        layout.addWidget(self.map_view)

        self.setLayout(layout)
        self.setGeometry(300, 300, 800, 600)

        self.map_window = None

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo", "", "Excel Files (*.xlsx);;CSV Files (*.csv)")
        if file_path:
            self.process_file(file_path)

    def process_file(self, file_path):
        try:
            if file_path.endswith('.xlsx'):
                self.df = pd.read_excel(file_path)
            else:
                self.df = pd.read_csv(file_path)

            

            self.lat_col = self.find_column(self.df, ['latitud', 'lat', 'latitude'])
            self.lon_col = self.find_column(self.df, ['longitud', 'lon', 'long', 'longitude'])

            if self.lat_col is None or self.lon_col is None:
                self.status_label.setText('No se encontraron columnas de latitud y longitud.')
                return

            self.df[self.lat_col] = self.df[self.lat_col].apply(self.clean_coordinate)
            self.df[self.lon_col] = self.df[self.lon_col].apply(self.clean_coordinate)

            self.label_column.clear()
            self.label_column.addItems(self.df.columns)

            self.date_column_combo.clear()
            self.date_column_combo.addItem('Ninguna')
            date_columns = self.find_date_columns(self.df)
            self.date_column_combo.addItems(date_columns)

            self.apply_filter()

        except Exception as e:
            self.status_label.setText(f'Error al procesar el archivo: {str(e)}')

    def find_date_columns(self, df):
        date_columns = []
        for col in df.columns:
            try:
                pd.to_datetime(df[col])
                date_columns.append(col)
            except:
                pass
        return date_columns

    def update_date_filter(self, column):
        if column != 'Ninguna':
            self.date_column = column
            min_date = pd.to_datetime(self.df[column].min())
            max_date = pd.to_datetime(self.df[column].max())
            self.min_date.setDateTime(min_date.to_pydatetime())
            self.max_date.setDateTime(max_date.to_pydatetime())
        else:
            self.date_column = None

    def apply_filter(self):
        if self.df is None:
            return

        filtered_df = self.df[
            (self.df[self.lat_col] >= self.min_lat.value()) &
            (self.df[self.lat_col] <= self.max_lat.value()) &
            (self.df[self.lon_col] >= self.min_lon.value()) &
            (self.df[self.lon_col] <= self.max_lon.value())
        ]

        if self.date_column:
            min_date = self.min_date.dateTime().toPyDateTime()
            max_date = self.max_date.dateTime().toPyDateTime()
            filtered_df = filtered_df[
                (pd.to_datetime(filtered_df[self.date_column]) >= min_date) &
                (pd.to_datetime(filtered_df[self.date_column]) <= max_date)
            ]

        self.create_map(filtered_df)

    def create_map(self, df):
        m = folium.Map(location=[df[self.lat_col].mean(), df[self.lon_col].mean()], zoom_start=10)
        
        if self.use_clustering_cb.isChecked():
            marker_cluster = MarkerCluster().add_to(m)
        else:
            marker_cluster = m

        label_col = self.label_column.currentText()

        for idx, row in df.iterrows():
            popup_content = f"{label_col}: {row[label_col]}<br>"
            for col in df.columns:
                if col != label_col:
                    popup_content += f"{col}: {row[col]}<br>"
            
            if self.random_color_cb.isChecked():
                color = f"#{random.randint(0, 0xFFFFFF):06x}"
            else:
                color = self.marker_color

            folium.Marker(
                [row[self.lat_col], row[self.lon_col]],
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.Icon(color=color, icon="info-sign")
            ).add_to(marker_cluster)

        temp_map_path = os.path.join(os.path.dirname(__file__), "temp_map.html")
        m.save(temp_map_path)

        if self.new_window_cb.isChecked():
            if self.map_window is None or not self.map_window.isVisible():
                self.map_window = MapWindow(self)
            self.map_window.map_view.setUrl(QUrl.fromLocalFile(temp_map_path))
            self.map_window.show()
        else:
            self.map_view.setUrl(QUrl.fromLocalFile(temp_map_path))

        self.status_label.setText('Mapa generado con éxito.')
        self.map = m

    def select_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.marker_color = color.name()
            self.color_btn.setStyleSheet(f"background-color: {self.marker_color};")

    def download_kmz(self):
        if self.df is None or self.map is None:
            self.status_label.setText('No hay datos para exportar.')
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar archivo KMZ", "", "KMZ Files (*.kmz)")
        if file_path:
            try:
                kml = simplekml.Kml()
                label_col = self.label_column.currentText()

                for idx, row in self.df.iterrows():
                    point = kml.newpoint(name=str(row[label_col]))
                    point.coords = [(row[self.lon_col], row[self.lat_col])]
                    description = ""
                    for col in self.df.columns:
                        if col != label_col:
                            description += f"{col}: {row[col]}\n"
                    point.description = description

                kml.save(file_path)
                self.status_label.setText('Archivo KMZ guardado con éxito.')
            except Exception as e:
                self.status_label.setText(f'Error al guardar el archivo KMZ: {str(e)}')

    def find_column(self, df, possible_names):
        # Convertimos todas las columnas a minúsculas para hacer la búsqueda insensible a mayúsculas/minúsculas
        lower_columns = {col.lower(): col for col in df.columns}
        for name in possible_names:
            if name.lower() in lower_columns:
                return lower_columns[name.lower()]
        raise ValueError(f'No se encontró ninguna columna que coincida con: {possible_names}')

    def clean_coordinate(self, coord):
        if isinstance(coord, str):
            coord = coord.replace("'", "").replace(",", ".")
        return -abs(float(coord))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CoordPlotter()
    ex.show()
    sys.exit(app.exec_())