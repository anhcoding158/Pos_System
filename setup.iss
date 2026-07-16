[Setup]
; --- THÔNG TIN PHẦN MỀM ---
AppName=POS Enterprise
AppVersion=2.0
AppPublisher=Anh Linh Store
DefaultDirName={autopf}\POS Enterprise
DefaultGroupName=POS Enterprise

; --- CẤU HÌNH FILE SETUP ĐẦU RA ---
OutputDir=Release_Installer
OutputBaseFilename=POS_Enterprise_Setup_v2
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin

; --- ICON CHO FILE SETUP VÀ PHẦN MỀM ---
; LƯU Ý: Phải đảm bảo bạn có file icon.ico ở thư mục gốc!
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\POS_Enterprise.exe

[Tasks]
; Lệnh tạo dấu tích "Create a desktop shortcut" khi cài đặt
Name: "desktopicon"; Description: "Tạo biểu tượng ngoài màn hình (Desktop Shortcut)"; GroupDescription: "Tùy chọn bổ sung:"

[Files]
; --- NHỮNG FILE NÀO SẼ ĐƯỢC NHÉT VÀO TRONG BỘ CÀI SETUP ---
; 1. File chạy chính
Source: "dist\POS_Enterprise.exe"; DestDir: "{app}"; Flags: ignoreversion
; 2. File cấu hình TRẮNG (đổi tên thành config.json khi cài)
Source: "config_default.json"; DestName: "config.json"; DestDir: "{app}"; Flags: ignoreversion
; 3. File Icon để làm shortcut
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; --- LỆNH TẠO SHORTCUT RA DESKTOP (KÈM ICON XỊN) ---
Name: "{autodesktop}\POS Enterprise"; Filename: "{app}\POS_Enterprise.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon
Name: "{group}\POS Enterprise"; Filename: "{app}\POS_Enterprise.exe"; IconFilename: "{app}\icon.ico"