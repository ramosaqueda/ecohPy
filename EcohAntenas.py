import sys
import os
os.environ['QT_MAC_WANTS_LAYER'] = '1'
import pandas as pd
from packaging import version

import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QProgressBar
from PyQt5.QtCore import QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import chardet

class Worker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def detect_encoding(self, file_path):
        with open(file_path, 'rb') as file:
            raw = file.read(10000)
        return chardet.detect(raw)['encoding']

    def count_lines(self, file_path, encoding):
        with open(file_path, 'r', encoding=encoding, errors='replace') as file:
            return sum(1 for _ in file)

    def run(self):
        try:
            encoding = self.detect_encoding(self.file_path)
            total_rows = self.count_lines(self.file_path, encoding) - 1  # -1 para excluir la cabecera
        except Exception as e:
            print(f"Error al detectar codificación o contar líneas: {e}")
            encoding = 'ISO-8859-1'  # Usar como fallback
            total_rows = 0  # Manejaremos esto de manera diferente

        chunksize = 100000
        processed_rows = 0

        movil_counts = {}
        coord_counts = {}
        compania_counts = {}
        trafico_por_tecnologia = {}

        try:
            # Comprobamos la versión de pandas para usar el parámetro correcto
            if version.parse(pd.__version__) >= version.parse('1.3.0'):
                csv_reader = pd.read_csv(self.file_path, chunksize=chunksize, encoding=encoding, on_bad_lines='skip')
            else:
                csv_reader = pd.read_csv(self.file_path, chunksize=chunksize, encoding=encoding, error_bad_lines=False)

            for chunk in csv_reader:
                for _, row in chunk.iterrows():
                    movil = row.get('movil', 'N/A')
                    coord = (row.get('latitud', 'N/A'), row.get('longitud', 'N/A'))
                    compania = row.get('compania_origen', 'N/A')
                    tecnologia = row.get('tecnologia', 'N/A')
                    trafico = row.get('cantidad_trafico', 0)

                    movil_counts[movil] = movil_counts.get(movil, 0) + 1
                    coord_counts[coord] = coord_counts.get(coord, 0) + 1
                    compania_counts[compania] = compania_counts.get(compania, 0) + 1
                    
                    trafico_por_tecnologia[tecnologia] = trafico_por_tecnologia.get(tecnologia, 0) + trafico

                processed_rows += len(chunk)
                if total_rows > 0:
                    self.progress.emit(int(processed_rows / total_rows * 100))
                else:
                    self.progress.emit(int(processed_rows / chunksize * 100) % 100)

        except Exception as e:
            print(f"Error al procesar el archivo: {e}")

        results = {
            'movil_counts': movil_counts,
            'coord_counts': coord_counts,
            'compania_counts': compania_counts,
            'trafico_por_tecnologia': trafico_por_tecnologia
        }
        self.finished.emit(results)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ECOH TOOLS, Análisis de Tráfico Telefónico basado en traficos de antenas")
        self.setGeometry(100, 100, 1000, 800)

        layout = QVBoxLayout()

        self.upload_button = QPushButton("Cargar archivo")
        self.upload_button.clicked.connect(self.load_file)
        layout.addWidget(self.upload_button)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.figure, self.ax = plt.subplots(2, 2, figsize=(12, 10))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo", "", "CSV Files (*.csv)")
        if file_path:
            self.worker = Worker(file_path)
            self.worker.progress.connect(self.update_progress)
            self.worker.finished.connect(self.show_results)
            self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def show_results(self, results):
        self.ax[0, 0].clear()
        self.ax[0, 1].clear()
        self.ax[1, 0].clear()
        self.ax[1, 1].clear()

        # Gráfico de números móviles más frecuentes
        top_moviles = sorted(results['movil_counts'].items(), key=lambda x: x[1], reverse=True)[:10]
        self.ax[0, 0].bar([str(x[0]) for x in top_moviles], [x[1] for x in top_moviles])
        self.ax[0, 0].set_title("Top 10 números móviles")
        self.ax[0, 0].set_xlabel("Número móvil")
        self.ax[0, 0].set_ylabel("Frecuencia")
        self.ax[0, 0].tick_params(axis='x', rotation=45)

        # Gráfico de coordenadas más frecuentes
        top_coords = sorted(results['coord_counts'].items(), key=lambda x: x[1], reverse=True)[:10]
        self.ax[0, 1].bar([f"{x[0][0]}, {x[0][1]}" for x in top_coords], [x[1] for x in top_coords])
        self.ax[0, 1].set_title("Top 10 coordenadas")
        self.ax[0, 1].set_xlabel("Coordenadas")
        self.ax[0, 1].set_ylabel("Frecuencia")
        self.ax[0, 1].tick_params(axis='x', rotation=45)

        # Gráfico de compañías más frecuentes
        companias = list(results['compania_counts'].items())
        self.ax[1, 0].pie([x[1] for x in companias], labels=[x[0] for x in companias], autopct='%1.1f%%')
        self.ax[1, 0].set_title("Distribución de compañías")

        # Gráfico de tráfico por tecnología
        tecnologias = list(results['trafico_por_tecnologia'].items())
        self.ax[1, 1].bar([x[0] for x in tecnologias], [x[1] for x in tecnologias])
        self.ax[1, 1].set_title("Tráfico por tecnología")
        self.ax[1, 1].set_xlabel("Tecnología")
        self.ax[1, 1].set_ylabel("Cantidad de tráfico")

        self.figure.tight_layout()
        self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())