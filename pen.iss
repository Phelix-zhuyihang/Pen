[Setup]
AppName=Pen - NetCut Paste Tool
AppVersion=1.4.0
AppPublisher=Pen Tool
AppPublisherURL=https://github.com/
AppSupportURL=https://github.com/
AppUpdatesURL=https://github.com/
DefaultDirName={pf}\Pen
DefaultGroupName=Pen
OutputDir=installer
OutputBaseFilename=pen-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimp.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\pen.exe"; DestDir: "{app}"; Flags: ignoreversion
; Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion  ; 取消注释添加图标

[Dirs]

[Icons]
Name: "{group}\Pen"; Filename: "{app}\pen.exe"
Name: "{group}\帮助"; Filename: "{app}\README.chm"
Name: "{desktop}\Pen"; Filename: "{app}\pen.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\pen.exe"; Description: "打开 Pen 命令行工具"; Flags: nowait postinstall skipifsilent
Filename: "{cmd}"; Parameters: "/k ""cd ""{app}"" && pen help"""; Description: "在命令行中运行 Pen"; Flags: postinstall unchecked

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\pen"
