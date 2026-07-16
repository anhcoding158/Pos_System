pipeline {
    agent any
    environment {
        APP_NAME = "POS_Enterprise"
        // Version tự động tăng theo lượt build của Jenkins
        APP_VERSION = "2.0.${env.BUILD_NUMBER}"
    }
    stages {
        stage('Checkout Code') {
            steps {
                // Jenkins tự động tải code mới nhất từ Github về
                checkout scm
            }
        }
        stage('Cài đặt Môi trường') {
            steps {
                bat '''
                echo =========================================
                echo CÀI ĐẶT THƯ VIỆN PYTHON (DEPENDENCIES)
                echo =========================================
                python -m pip install --upgrade pip
                pip install -r requirements.txt
                pip install pyinstaller
                '''
            }
        }
        stage('Đóng gói (Build EXE)') {
            steps {
                bat '''
                echo =========================================
                echo TIẾN HÀNH BUILD FILE EXE
                echo =========================================
                if exist build rmdir /S /Q build
                if exist dist rmdir /S /Q dist

                :: Build ra thư mục (onedir) để phần mềm chạy ổn định nhất, ẩn cửa sổ đen (noconsole)
                pyinstaller --noconsole --onedir --windowed --icon=icon.ico --name %APP_NAME% main.py
                '''
            }
        }
        stage('Xuất bản (Zip Release)') {
            steps {
                bat '''
                echo =========================================
                echo NÉN THÀNH PHẨM ĐỂ GIAO CHO KHÁCH HÀNG
                echo =========================================
                :: Dùng Powershell của Windows để nén thư mục dist/POS_Enterprise thành file ZIP
                powershell Compress-Archive -Path dist\\%APP_NAME% -DestinationPath %APP_NAME%_v%APP_VERSION%.zip -Force
                '''
            }
        }
    }
    post {
        success {
            echo "🎉 CHÚC MỪNG: BUILD THÀNH CÔNG PHIÊN BẢN ${env.APP_VERSION}!"
            // Đẩy file ZIP lên giao diện Jenkins để sếp tải về
            archiveArtifacts artifacts: '*.zip', fingerprint: true
        }
        cleanup {
            // FIX LỖI: Dùng 'cleanup' thay vì 'always' để dọn rác sau khi đã lưu file ZIP xong
            cleanWs()
        }
    }
}