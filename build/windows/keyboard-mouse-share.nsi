; Keyboard Mouse Share - Windows Installer Script (NSIS)
; This script creates a professional Windows installer for the application
; Build requirements: NSIS 3.0+

!include "LogicLib.nsh"
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "x64.nsh"

; Define version and product info
!define PRODUCT_NAME "Keyboard Mouse Share"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "Cross-Device Input Team"
!define PRODUCT_WEB_SITE "https://github.com/yourusername/keyboard-mouse-share"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\KeyboardMouseShare.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"

; Installer settings
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "dist\KeyboardMouseShare-${PRODUCT_VERSION}-setup.exe"
InstallDir "$PROGRAMFILES\${PRODUCT_NAME}"

; Request admin privileges for installation
RequestExecutionLevel admin

; Set compression method
SetCompressor /SOLID lzma

; MUI Settings
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Language
!insertmacro MUI_LANGUAGE "English"

; MUI end ------

; Installer sections
Section "Install Application Files"
  SetOutPath "$INSTDIR"
  
  ; Copy PyInstaller-generated application files
  File /r "build\windows\KeyboardMouseShare\*.*"
  
  ; Copy documentation
  SetOutPath "$INSTDIR\docs"
  File /r "docs\*.*"
  
  ; Copy README and license
  SetOutPath "$INSTDIR"
  File "README.md"
  File "LICENSE"
  
  ; Create Start Menu shortcuts
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\KeyboardMouseShare.exe"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  
  ; Create Desktop shortcut
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\KeyboardMouseShare.exe"
  
  ; Write registry entries for uninstall
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\KeyboardMouseShare.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\KeyboardMouseShare.exe"
  
  ; Write uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  ; Verify installation
  ${If} ${FileExists} "$INSTDIR\KeyboardMouseShare.exe"
    DetailPrint "Installation completed successfully"
  ${Else}
    MessageBox MB_ICONEXCLAMATION "Installation may have failed. Please check the application files."
  ${EndIf}
SectionEnd

; Uninstaller section
Section "Uninstall"
  ; Remove application files
  RMDir /r "$INSTDIR"
  
  ; Remove Start Menu shortcuts
  RMDir /r "$SMPROGRAMS\${PRODUCT_NAME}"
  
  ; Remove Desktop shortcut
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
  
  ; Remove registry entries
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  DeleteRegKey HKLM "${PRODUCT_UNINST_KEY}"
  
  DetailPrint "Uninstall completed successfully"
SectionEnd

; Function to check system requirements
Function .onInit
  SetShellVarContext all
  
  ; Check for admin privileges
  UserInfo::GetAccountType
  Pop $0
  ${If} $0 != "admin"
    MessageBox MB_ICONSTOP "Administrator rights required to install ${PRODUCT_NAME}."
    SetErrorLevel 740
    Quit
  ${EndIf}
  
  ; Check Windows version (Windows 10+)
  ${If} ${IsWinVista}
  ${AndIf} ${IsWin7}
  ${AndIf} ${IsWin8}
  ${AndIf} ${IsWin8.1}
    MessageBox MB_ICONSTOP "This application requires Windows 10 or later."
    Quit
  ${EndIf}
  
  DetailPrint "System requirements check passed..."
FunctionEnd

; Function for uninstaller initialization
Function un.onInit
  SetShellVarContext all
  
  ; Ask for confirmation
  MessageBox MB_ICONQUESTION|MB_YESNO \
    "Are you sure you want to uninstall ${PRODUCT_NAME}?" \
    IDYES +2
  Abort
FunctionEnd
