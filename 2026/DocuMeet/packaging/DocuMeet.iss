[Setup]
AppId={{86A5121F-EAAE-4D5D-AABC-2A7068E1B4D9}
AppName=DocuMeet
AppVersion=0.1.0
AppPublisher=DocuMeet Meetings
DefaultDirName={localappdata}\Programs\DocuMeet
DefaultGroupName=DocuMeet
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=DocuMeet-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\DocuMeet.exe

[Files]
Source: "..\dist\DocuMeet\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\DocuMeet"; Filename: "{app}\DocuMeet.exe"
Name: "{autodesktop}\DocuMeet"; Filename: "{app}\DocuMeet.exe"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked

[Run]
Filename: "{app}\DocuMeet.exe"; Description: "Open DocuMeet and set up offline models"; Flags: nowait postinstall skipifsilent
