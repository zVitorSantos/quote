; QuotesInstaller.iss

[Setup]
AppName=Quotes
AppVersion=1.0.0
DefaultDirName={pf}\Quotes
DefaultGroupName=Quotes
OutputDir=dist
OutputBaseFilename=QuotesInstaller
Compression=lzma/max
SolidCompression=yes
DisableDirPage=yes
DisableReadyPage=yes
DisableFinishedPage=yes

[Files]
Source: "dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "path\to\additional\files\*"; DestDir: "{app}"; Flags: ignoreversion

[Run]
Filename: "{app}\main.exe"; Description: "{cm:LaunchProgram,Quotes}"; Flags: nowait postinstall skipifsilent
