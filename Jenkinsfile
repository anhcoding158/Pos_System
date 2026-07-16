pipeline {
    agent any
    environment {
        APP_NAME = "POS_Enterprise"
        // Phiên bản tự động ăn theo số Build của Jenkins (Ví dụ: 2.0.15)
        APP_VERSION = "2.0.${env.BUILD_NUMBER}"
        // Lấy thời gian thực để đóng dấu vào bản Build
        BUILD_DATE = new Date().format("dd/MM/yyyy HH:mm:ss")
    }

    stages {
        stage('1. Checkout Code') {
            steps {
                echo '🚀 Đang tải mã nguồn mới nhất từ GitHub...'
                checkout scm
            }
        }

        stage('2. Phục hồi Môi trường (Setup Env)') {
            steps {
                bat '''
                echo =========================================
                echo [DEV-OPS] CÀI ĐẶT THƯ VIỆN & CÔNG CỤ TEST
                echo =========================================
                python -m pip install --upgrade pip
                pip install -r requirements.txt
                :: Cài thêm công cụ kiểm thử (pytest) và dò lỗi code (flake8)
                pip install pyinstaller pytest flake8
                '''
            }
        }

        stage('3. Kiểm tra Mã nguồn (Linting)') {
            steps {
                bat '''
                echo =========================================
                echo [DEV-OPS] QUÉT LỖI CÚ PHÁP BẰNG FLAKE8
                echo =========================================
                :: Quét các lỗi cú pháp nghiêm trọng (Syntax errors) trước khi Build
                :: Nếu code có lỗi ngớ ngẩn (thiếu dấu, thụt lề sai), nó sẽ cảnh báo ngay!
                flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
                '''
            }
        }

        stage('4. Kiểm thử Tự động (Unit Testing)') {
            steps {
                bat '''
                echo =========================================
                echo [DEV-OPS] CHẠY KIỂM THỬ TỰ ĐỘNG (PYTEST)
                echo =========================================
                :: Kiểm tra xem Dev đã viết Test chưa. Nếu có thư mục 'tests' thì chạy, chưa có thì bỏ qua.
                if exist tests\\ (
                    echo 🔍 Đang chạy các bài Test...
                    pytest tests/ -v
                ) else (
                    echo ⚠️ [CẢNH BÁO] Chưa tìm thấy thư mục 'tests'. Bỏ qua quá trình kiểm thử...
                )
                '''
            }
        }

        stage('5. Đóng dấu Phiên bản (Versioning)') {
            steps {
                bat '''
                echo =========================================
                echo [DEV-OPS] TẠO FILE PHIÊN BẢN TỰ ĐỘNG
                echo =========================================
                :: Tự động tạo file version.txt để nhúng vào phần mềm
                echo Phiên bản: %APP_VERSION% > version.txt
                echo Ngày đóng gói: %BUILD_DATE% >> version.txt
                '''
            }
        }

        stage('6. Biên dịch (Build EXE)') {
            steps {
                bat '''
                echo =========================================
                echo [DEV-OPS] BIÊN DỊCH CODE BẰNG PYINSTALLER
                echo =========================================
                if exist build rmdir /S /Q build
                if exist dist rmdir /S /Q dist

                :: Bổ sung thêm file version.txt vào bên trong EXE (--add-data "version.txt;.")
                pyinstaller --noconsole --onefile --windowed --icon=icon.ico --add-data "icon.ico;." --add-data "version.txt;." --name %APP_NAME% main.py
                '''
            }
        }

        stage('7. Tạo Trình Cài Đặt (Inno Setup)') {
            steps {
                bat '''
                echo =========================================
                echo [DEV-OPS] ĐÓNG GÓI BỘ CÀI CHUYÊN NGHIỆP
                echo =========================================
                "C:\\Program Files (x86)\\Inno Setup 6\\iscc.exe" setup.iss
                '''
            }
        }

        stage('8. Xuất Bản Cập Nhật (Release Notes)') {
            steps {
                bat '''
                echo =========================================
                echo [DEV-OPS] TẠO CHANGELOG TỪ GITHUB
                echo =========================================
                :: Tự động trích xuất 5 lần thay đổi code gần nhất (Commit) để làm Lịch sử cập nhật giao cho khách!
                echo CHI TIET BAN CAP NHAT %APP_VERSION% > Release_Installer\\Changelog.txt
                echo Ngay phat hanh: %BUILD_DATE% >> Release_Installer\\Changelog.txt
                echo ---------------------------------- >> Release_Installer\\Changelog.txt
                git log -5 --pretty=format:"- %%s (%%h)" >> Release_Installer\\Changelog.txt
                '''
            }
        }
    }

    post {
        success {
            echo "✅ [THÀNH CÔNG] SẢN PHẨM PHIÊN BẢN ${env.APP_VERSION} ĐÃ SẴN SÀNG!"
            // Lưu trữ toàn bộ file EXE cài đặt và file Lịch sử cập nhật (Changelog.txt)
            archiveArtifacts artifacts: 'Release_Installer/*.*', fingerprint: true
        }
        failure {
            echo "❌ [THẤT BẠI] QUÁ TRÌNH BUILD BỊ LỖI!"
            echo "🔥 Gửi cảnh báo: Hãy kiểm tra lại Log của Stage bị đỏ để Fix Bug ngay!"
        }
        cleanup {
            echo "🧹 [DỌN DẸP] Xóa không gian làm việc để giải phóng RAM/Ổ cứng..."
            cleanWs()
        }
    }
}