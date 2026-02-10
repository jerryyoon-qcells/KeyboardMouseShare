; Inno Setup installer script for Keyboard Mouse Share
; Download Inno Setup from: https://jrsoftware.org/isdl.php
; Build command: iscc keyboard_mouse_share.iss

#define MyAppName "Keyboard Mouse Share"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Cross-Device Input Team"
#define MyAppURL "https://github.com/yourusername/keyboard-mouse-share"
#define MyAppExeName "KeyboardMouseShare.exe"
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".kms"
#define MyAppAssocProgId "KeyboardMouseShare.1"

[Setup]
AppId={{5F3C7C2E-9B4D-4F1E-8A6C-3D2E1C0F5B7A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
ChangesAssociations=yes
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
LicenseFile=LICENSE.txt
InfoBeforeFile=build\windows\BEFORE_INSTALL.txt
OutputDir=dist\windows
OutputBaseFilename=KeyboardMouseShare-Setup-{#MyAppVersion}
SetupIconFile=build\windows\kms.ico
Compression=lz4
SolidCompression=yes
WizardStyle=modern
WizardResizable=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCopyright=2024 {#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
MinVersion=10.0.19041

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1,10.0
Name: "autostart"; Description: "&Run at Windows startup"; GroupDescription: "Startup options:"; Flags: unchecked

[Files]
Source: "dist\KeyboardMouseShare\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\KeyboardMouseShare\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion disentanglepath
Source: "build\windows\kms.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "build\windows\SYSTEM_REQUIREMENTS.txt"; DestDir: "{app}"; Flags: ignoreversion

[Registry]
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocExt}\OpenWithProgids"; ValueType: string; ValueName: "{#MyAppAssocProgId}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocProgId}"; ValueType: string; ValueData: "{#MyAppAssocName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocProgId}\DefaultIcon"; ValueType: string; ValueData: "{app}\{#MyAppExeName},0"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocProgId}\shell\open\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppAssocProgId}_is1"; ValueType: string; ValueName: "Inno Setup: App Path"; ValueData: "{app}"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\{#MyAppName}"; Flags: uninsdeletekey

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\kms.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\kms.ico"; Tasks: desktopicon
Name: "{autostartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\kms.ico"; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: dirifempty; Name: "{app}"
Type: dirifempty; Name: "{group}"
Type: files; Name: "{userappdata}\KeyboardMouseShare\*"

[CustomMessages]
english.NameAndVersion=%1 version %2
english.AdditionalIcons=Additional icons:
english.CreateDesktopIcon=Create a &desktop icon
english.CreateQuickLaunchIcon=Create a &Quick Launch icon
english.ProgramOnTheWeb=%1 on the Web
english.UninstallProgram=Uninstall %1
english.LaunchProgram=Launch %1
english.AssocFileExtension=Associate %1 with the %2 file extension
english.AssocingFileExtension=Associating %1 with the %2 file extension...
english.AutoStartProgramGroupDescription=Startup:
english.AutoStartProgram=Automatically run %1 at startup

[Code]
function InitializeSetup(): Boolean;
begin
  // Check Windows 11 (build 22000+) or Windows 10 (build 19041+)
  if not (IsWindows10OrLater and (GetWindowsVersion >= $0A0F2328)) then
  begin
    MsgBox('This application requires Windows 10 (build 19041) or later, or Windows 11. You have an older version of Windows.', mbCriticalError, MB_OK);
    Result := False;
  end
  else
    Result := True;
end;

procedure InitializeUninstall();
begin
  if MsgBox('Are you sure you want to uninstall ' + ExpandConstant('{#MyAppName}') + '?', mbConfirmation, MB_YESNO) = IDNO then
    Abort();
end;
