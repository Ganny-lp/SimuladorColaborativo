; Inno Setup — gera installer\SimuladorLumina-Setup-<versão>.exe
; Compilar:  iscc /DAppVersion=1.0.0 packaging\installer.iss   (rode a partir da raiz do projeto)

#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#define AppName "Simulador LUMINA"
#define AppExe  "SimuladorLumina.exe"

[Setup]
AppId={{B7C1D2E4-5A63-4F0B-9C3D-6E1A2F4B8D90}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=LUMINA
DefaultDirName={autopf}\SimuladorLumina
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\installer
OutputBaseFilename=SimuladorLumina-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName={#AppName}
#ifexist "icon.ico"
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#AppExe}
#endif

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "..\dist\SimuladorLumina\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir o {#AppName} agora"; Flags: nowait postinstall skipifsilent
