[Setup]
; --- THÔNG TIN PHẦN MỀM ---
AppName=POS Enterprise
AppVersion=2.0
AppPublisher=Anh Linh Store

; ĐÃ FIX LỖI: Cài thẳng ra ổ C:\ thay vì Program Files để có quyền tạo folder Assets và lưu Database
DefaultDirName={sd}\POS Enterprise
DefaultGroupName=POS Enterprise

; --- CẤU HÌNH FILE SETUP ĐẦU RA ---
OutputDir=Release_Installer
OutputBaseFilename=POS_Enterprise_Setup_v2
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin

; --- ICON CHO FILE SETUP VÀ PHẦN MỀM ---
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\POS_Enterprise.exe

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng ngoài màn hình (Desktop Shortcut)"; GroupDescription: "Tùy chọn bổ sung:"

[Files]
Source: "dist\POS_Enterprise.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config_default.json"; DestName: "config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\POS Enterprise"; Filename: "{app}\POS_Enterprise.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon
Name: "{group}\POS Enterprise"; Filename: "{app}\POS_Enterprise.exe"; IconFilename: "{app}\icon.ico"