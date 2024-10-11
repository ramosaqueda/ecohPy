import sys
import boto3
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class AWSRekognitionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.aws_access_key_id = ""
        self.aws_secret_access_key = ""
        self.aws_region = ""
        self.image1_path = ""
        self.image2_path = ""

    def initUI(self):
        print("Initializing UI...")  # Mensaje de depuración
        self.setWindowTitle('AWS Rekognition Photo Comparison')
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        # AWS Credentials
        cred_layout = QHBoxLayout()
        cred_layout.addWidget(QLabel('AWS Access Key ID:'))
        self.access_key_input = QLineEdit()
        cred_layout.addWidget(self.access_key_input)
        cred_layout.addWidget(QLabel('AWS Secret Access Key:'))
        self.secret_key_input = QLineEdit()
        self.secret_key_input.setEchoMode(QLineEdit.Password)
        cred_layout.addWidget(self.secret_key_input)
        cred_layout.addWidget(QLabel('AWS Region:'))
        self.region_input = QLineEdit()
        cred_layout.addWidget(self.region_input)
        layout.addLayout(cred_layout)

        # Image selection
        img_layout = QHBoxLayout()
        self.img1_label = QLabel('Image 1')
        self.img1_label.setAlignment(Qt.AlignCenter)
        img_layout.addWidget(self.img1_label)
        self.img2_label = QLabel('Image 2')
        self.img2_label.setAlignment(Qt.AlignCenter)
        img_layout.addWidget(self.img2_label)
        layout.addLayout(img_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_img1 = QPushButton('Select Image 1')
        self.btn_img1.clicked.connect(lambda: self.select_image(1))
        btn_layout.addWidget(self.btn_img1)
        self.btn_img2 = QPushButton('Select Image 2')
        self.btn_img2.clicked.connect(lambda: self.select_image(2))
        btn_layout.addWidget(self.btn_img2)
        self.btn_compare = QPushButton('Compare Images')
        self.btn_compare.clicked.connect(self.compare_images)
        btn_layout.addWidget(self.btn_compare)
        layout.addLayout(btn_layout)

        # Results
        self.result_label = QLabel('Results will be displayed here')
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)

        self.setLayout(layout)
        print("UI initialization complete.")  # Mensaje de depuración

    def select_image(self, img_num):
        print(f"Selecting image {img_num}...")  # Mensaje de depuración
        file_name, _ = QFileDialog.getOpenFileName(self, f"Select Image {img_num}", "", "Image Files (*.png *.jpg *.bmp)")
        if file_name:
            pixmap = QPixmap(file_name).scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            if img_num == 1:
                self.img1_label.setPixmap(pixmap)
                self.image1_path = file_name
            else:
                self.img2_label.setPixmap(pixmap)
                self.image2_path = file_name
            print(f"Image {img_num} selected: {file_name}")  # Mensaje de depuración
        else:
            print(f"No image selected for image {img_num}")  # Mensaje de depuración

    def compare_images(self):
        print("Comparing images...")  # Mensaje de depuración
        self.aws_access_key_id = self.access_key_input.text()
        self.aws_secret_access_key = self.secret_key_input.text()
        self.aws_region = self.region_input.text()

        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.aws_region, self.image1_path, self.image2_path]):
            QMessageBox.warning(self, "Missing Information", "Please fill in all AWS credentials and select both images.")
            print("Missing information. Cannot proceed with comparison.")  # Mensaje de depuración
            return

        try:
            client = boto3.client('rekognition',
                                  aws_access_key_id=self.aws_access_key_id,
                                  aws_secret_access_key=self.aws_secret_access_key,
                                  region_name=self.aws_region)

            with open(self.image1_path, 'rb') as image_file1:
                source_bytes = image_file1.read()

            with open(self.image2_path, 'rb') as image_file2:
                target_bytes = image_file2.read()

            response = client.compare_faces(
                SourceImage={'Bytes': source_bytes},
                TargetImage={'Bytes': target_bytes}
            )

            if response['FaceMatches']:
                similarity = response['FaceMatches'][0]['Similarity']
                self.result_label.setText(f"Similarity: {similarity:.2f}%")
                print(f"Comparison complete. Similarity: {similarity:.2f}%")  # Mensaje de depuración
            else:
                self.result_label.setText("No matching faces found.")
                print("Comparison complete. No matching faces found.")  # Mensaje de depuración

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            QMessageBox.critical(self, "Error", error_message)
            print(f"Error during comparison: {error_message}")  # Mensaje de depuración

def main():
    print("Starting application...")  # Mensaje de depuración
    app = QApplication(sys.argv)
    ex = AWSRekognitionApp()
    ex.show()
    print("Application window should be visible now.")  # Mensaje de depuración
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()