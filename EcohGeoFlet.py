import flet as ft
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import simplekml
import random
import tempfile
import webbrowser
import os

class CoordPlotter:
    def __init__(self, page: ft.Page):
        self.page = page
        self.df = None
        self.lat_col = None
        self.lon_col = None
        self.map = None
        self.marker_color = "#3388ff"
        self.date_column = None

        self.page.title = "ECOH TOOLS, Geoposicionador de Coordenadas Ver 1.0 By Rafo"
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        self.upload_btn = ft.ElevatedButton("Subir archivo", on_click=self.upload_file)
        self.status_text = ft.Text("Esperando archivo...")
        
        self.min_lat = ft.TextField(label="Lat min", value="-90", width=100)
        self.max_lat = ft.TextField(label="Lat max", value="90", width=100)
        self.min_lon = ft.TextField(label="Lon min", value="-180", width=100)
        self.max_lon = ft.TextField(label="Lon max", value="180", width=100)

        self.date_column_dropdown = ft.Dropdown(
            label="Columna de fecha",
            options=[ft.dropdown.Option("Ninguna")],
            width=200,
        )
        self.min_date = ft.TextField(label="Fecha min", width=150)
        self.max_date = ft.TextField(label="Fecha max", width=150)

        self.label_column_dropdown = ft.Dropdown(
            label="Columna para etiquetas",
            options=[],
            width=200,
        )

        self.filter_btn = ft.ElevatedButton("Aplicar filtro", on_click=self.apply_filter)
        self.use_clustering_cb = ft.Checkbox(label="Usar agrupación de marcadores", value=True)
        self.random_color_cb = ft.Checkbox(label="Usar colores aleatorios")

        self.download_kmz_btn = ft.ElevatedButton("Descargar KMZ", on_click=self.download_kmz)

        self.page.add(
            self.upload_btn,
            ft.Row([self.min_lat, self.max_lat, self.min_lon, self.max_lon]),
            ft.Row([self.date_column_dropdown, self.min_date, self.max_date]),
            self.label_column_dropdown,
            self.filter_btn,
            ft.Row([self.use_clustering_cb, self.random_color_cb]),
            self.download_kmz_btn,
            self.status_text,
        )

    def upload_file(self, e):
        def file_picker_result(e: ft.FilePickerResultEvent):
            if e.files:
                file_path = e.files[0].path
                self.process_file(file_path)

        file_picker = ft.FilePicker(on_result=file_picker_result)
        self.page.overlay.append(file_picker)
        self.page.update()
        file_picker.pick_files(allowed_extensions=["xlsx", "csv"])

    def process_file(self, file_path):
        try:
            if file_path.endswith('.xlsx'):
                self.df = pd.read_excel(file_path)
            else:
                self.df = pd.read_csv(file_path)

            self.lat_col = self.find_column(self.df, ['latitud', 'lat', 'latitude'])
            self.lon_col = self.find_column(self.df, ['longitud', 'lon', 'long', 'longitude'])

            if self.lat_col is None or self.lon_col is None:
                self.status_text.value = 'No se encontraron columnas de latitud y longitud.'
                self.page.update()
                return

            self.df[self.lat_col] = self.df[self.lat_col].apply(self.clean_coordinate)
            self.df[self.lon_col] = self.df[self.lon_col].apply(self.clean_coordinate)

            self.label_column_dropdown.options = [ft.dropdown.Option(col) for col in self.df.columns]
            
            date_columns = self.find_date_columns(self.df)
            self.date_column_dropdown.options = [ft.dropdown.Option("Ninguna")] + [ft.dropdown.Option(col) for col in date_columns]

            self.status_text.value = 'Archivo procesado con éxito.'
            self.page.update()

        except Exception as e:
            self.status_text.value = f'Error al procesar el archivo: {str(e)}'
            self.page.update()

    def find_date_columns(self, df):
        date_columns = []
        for col in df.columns:
            try:
                pd.to_datetime(df[col])
                date_columns.append(col)
            except:
                pass
        return date_columns

    def apply_filter(self, e):
        if self.df is None:
            return

        filtered_df = self.df[
            (self.df[self.lat_col] >= float(self.min_lat.value)) &
            (self.df[self.lat_col] <= float(self.max_lat.value)) &
            (self.df[self.lon_col] >= float(self.min_lon.value)) &
            (self.df[self.lon_col] <= float(self.max_lon.value))
        ]

        if self.date_column_dropdown.value != "Ninguna":
            min_date = pd.to_datetime(self.min_date.value)
            max_date = pd.to_datetime(self.max_date.value)
            filtered_df = filtered_df[
                (pd.to_datetime(filtered_df[self.date_column_dropdown.value]) >= min_date) &
                (pd.to_datetime(filtered_df[self.date_column_dropdown.value]) <= max_date)
            ]

        self.create_map(filtered_df)

    def create_map(self, df):
        m = folium.Map(location=[df[self.lat_col].mean(), df[self.lon_col].mean()], zoom_start=10)
        
        if self.use_clustering_cb.value:
            marker_cluster = MarkerCluster().add_to(m)
        else:
            marker_cluster = m

        label_col = self.label_column_dropdown.value

        for idx, row in df.iterrows():
            popup_content = f"{label_col}: {row[label_col]}<br>"
            for col in df.columns:
                if col != label_col:
                    popup_content += f"{col}: {row[col]}<br>"
            
            if self.random_color_cb.value:
                color = f"#{random.randint(0, 0xFFFFFF):06x}"
            else:
                color = self.marker_color

            folium.Marker(
                [row[self.lat_col], row[self.lon_col]],
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.Icon(color=color, icon="info-sign")
            ).add_to(marker_cluster)

        temp_map_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
        m.save(temp_map_file.name)
        webbrowser.open('file://' + temp_map_file.name, new=2)

        self.status_text.value = 'Mapa generado con éxito.'
        self.page.update()
        self.map = m

    def download_kmz(self, e):
        if self.df is None or self.map is None:
            self.status_text.value = 'No hay datos para exportar.'
            self.page.update()
            return

        def save_file_result(e: ft.FilePickerResultEvent):
            if e.path:
                try:
                    kml = simplekml.Kml()
                    label_col = self.label_column_dropdown.value

                    for idx, row in self.df.iterrows():
                        point = kml.newpoint(name=str(row[label_col]))
                        point.coords = [(row[self.lon_col], row[self.lat_col])]
                        description = ""
                        for col in self.df.columns:
                            if col != label_col:
                                description += f"{col}: {row[col]}\n"
                        point.description = description

                    kml.save(e.path)
                    self.status_text.value = 'Archivo KMZ guardado con éxito.'
                except Exception as ex:
                    self.status_text.value = f'Error al guardar el archivo KMZ: {str(ex)}'
                self.page.update()

        save_file_dialog = ft.FilePicker(on_result=save_file_result)
        self.page.overlay.append(save_file_dialog)
        self.page.update()
        save_file_dialog.save_file(file_name="mapa.kmz", allowed_extensions=["kmz"])

    def find_column(self, df, possible_names):
        lower_columns = {col.lower(): col for col in df.columns}
        for name in possible_names:
            if name.lower() in lower_columns:
                return lower_columns[name.lower()]
        return None

    def clean_coordinate(self, coord):
        if isinstance(coord, str):
            coord = coord.replace("'", "").replace(",", ".")
        return -abs(float(coord))

def main(page: ft.Page):
    CoordPlotter(page)

ft.app(target=main)