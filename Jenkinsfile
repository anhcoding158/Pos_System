pipeline {
    agent any
    environment {
        APP_NAME = "POS_Enterprise"
        APP_VERSION = "2.0.${env.BUILD_NUMBER}"
    }
    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }
        stage('Cài đặt Môi trường') {
            steps {
                bat '''
                echo =========================================
                echo CÀI ĐẶT THƯ VIỆN PYTHON
                echo =========================================
                python -m pip install --upgrade pip
                pip install -r requirements.txt
                pip install pyinstaller
                '''
            }
        }
        stage('Đóng gói (Build 1 FILE EXE)') {
            steps {
                bat '''
                echo =========================================
                echo TIẾN HÀNH BUILD 1 FILE EXE DUY NHẤT
                echo =========================================
                if exist build rmdir /S /Q build
                if exist dist rmdir /S /Q dist

                :: --onefile: Chỉ sinh ra 1 file exe duy nhất
                :: --add-data "icon.ico;.": Ép file icon chui vào bên trong file exe
                pyinstaller --noconsole --onefile --windowed --icon=icon.ico --add-data "icon.ico;." --name %APP_NAME% main.py
                '''
            }
        }
        stage('Xuất bản (Zip Release)') {
            steps {
                bat '''
                echo =========================================
                echo ĐÓNG GÓI SẢN PHẨM SẠCH GIAO KHÁCH HÀNG
                echo =========================================
                :: 1. Tạo một thư mục Release gọn gàng
                if exist Release_Build rmdir /S /Q Release_Build
                mkdir Release_Build

                :: 2. Copy 1 file EXE duy nhất vào thư mục Release
                copy dist\\%APP_NAME%.exe Release_Build\\

                :: 3. ĐỔI TÊN file config_default thành config.json (BẢN SẠCH CỦA KHÁCH)
                copy config_default.json Release_Build\\config.json

                :: 4. Nén 2 file đó lại thành file ZIP mang đi bán
                powershell Compress-Archive -Path Release_Build\\* -DestinationPath %APP_NAME%_v%APP_VERSION%.zip -Force
                '''
            }
        }
    }
    post {
        success {
            echo "🎉 CHÚC MỪNG: BUILD THÀNH CÔNG PHIÊN BẢN ${env.APP_VERSION}!"
            archiveArtifacts artifacts: '*.zip', fingerprint: true
        }
        cleanup {
            cleanWs()
        }
    }
}