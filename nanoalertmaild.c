#include <stdio.h>
#include <stdlib.h>

int main(){
    const char *filePath = "/opt/alertmaild/alertmaild.conf";

    char command[100];
    snprintf(command, sizeof(command), "nano %s", filePath);

    system(command);

    return 0;
}