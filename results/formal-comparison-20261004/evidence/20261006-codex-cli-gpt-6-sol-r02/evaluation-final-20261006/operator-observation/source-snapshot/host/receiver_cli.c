#include "receiver.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(void) {
    char *line=malloc(CDM_MAX_FRAME+2);
    if(!line) return 2;
    cdm_state state; cdm_init(&state);
    while(fgets(line,CDM_MAX_FRAME+2,stdin)) {
        size_t n=strlen(line);
        bool accepted=cdm_accept(&state,line,n,1000);
        printf("%s %lu %s\n",accepted?"accepted":"rejected",(unsigned long)state.sequence,accepted?"ok":state.error);
        fflush(stdout);
    }
    cdm_free(&state); free(line); return 0;
}
