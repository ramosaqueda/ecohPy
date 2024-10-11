import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QMainWindow, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer, QDateTime

# Importa tus scripts (asegúrate de que estén en el mismo directorio o en el PYTHONPATH)
import EcohAntenas
import EcohGeo
import aws_rekognition_app

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Main Application')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Cabecera con logo
        header_layout = QHBoxLayout()
        logo_label = QLabel()
        logo_pixmap = QPixmap('logo.png')  # Asegúrate de tener un archivo logo.png en el mismo directorio
        logo_label.setPixmap(logo_pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(logo_label)
        header_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        main_layout.addLayout(header_layout)

        # Título
        title_label = QLabel('Bienvenido a la Aplicación Principal')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont('Arial', 16, QFont.Bold))
        main_layout.addWidget(title_label)

        # Botones del menú
        menu_layout = QVBoxLayout()
        
        ecoh_antenas_button = QPushButton('EcohAntenas')
        ecoh_antenas_button.clicked.connect(self.run_ecoh_antenas)
        menu_layout.addWidget(ecoh_antenas_button)

        ecoh_geo_button = QPushButton('EcohGeo')
        ecoh_geo_button.clicked.connect(self.run_ecoh_geo)
        menu_layout.addWidget(ecoh_geo_button)

        aws_rekognition_button = QPushButton('AWS Rekognition')
        aws_rekognition_button.clicked.connect(self.run_aws_rekognition)
        menu_layout.addWidget(aws_rekognition_button)

        main_layout.addLayout(menu_layout)

        # Footer con fecha y hora
        self.footer_label = QLabel()
        self.footer_label.setAlignment(Qt.AlignRight)
        main_layout.addWidget(self.footer_label)

        # Timer para actualizar la fecha y hora
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)  # Actualiza cada segundo

        self.update_datetime()  # Actualiza inmediatamente al iniciar

    def update_datetime(self):
        current_datetime = QDateTime.currentDateTime()
        formatted_datetime = current_datetime.toString('dd/MM/yyyy hh:mm:ss')
        self.footer_label.setText(formatted_datetime)

    def run_ecoh_antenas(self):
        EcohAntenas.main()

    def run_ecoh_geo(self):
        EcohGeo.main()

    def run_aws_rekognition(self):
        aws_rekognition_app.main()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())