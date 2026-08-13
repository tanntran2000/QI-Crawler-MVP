; Per-user Windows installer for the complete PyInstaller onedir bundle.
; Mutable Bid data is deliberately never installed under {app}.

#define AppName "QI-Crawler"
#define AppVersion "0.7.0"
#define AppPublisher "QI Technologies"
#define AppExeName "QI-Crawler.exe"

[Setup]
AppId={{E5FA0E8F-90C7-46F8-93E8-0E1FD3AC1740}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\QI-Crawler
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist\installer
OutputBaseFilename=QI-Crawler-Setup-v{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
; Include only the immutable PyInstaller release bundle. No local DB, session,
; reports, HSMT, configuration or developer cache is sourced by this installer.
Source: "..\dist\QI-Crawler\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\QI-Crawler"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\QI-Crawler"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a Desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Open QI-Crawler"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeUninstall(): Boolean;
begin
  // User data remains in %LOCALAPPDATA%\QI-Crawler. The uninstaller removes
  // only the application folder and never deletes database, documents, sessions or config.
  Result := True;
end;
