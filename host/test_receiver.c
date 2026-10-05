#include "receiver.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static char line[1000];
static const char *payload="{\"global_resets\":[],\"usage\":[]}";
static void make_line(uint32_t seq) {
    char body[800];
    snprintf(body,sizeof(body),"{\"payload\":%s,\"protocol\":\"cdm/1\",\"sent_at\":\"2026-09-10T00:00:00Z\",\"sequence\":%u}",payload,seq);
    char crc[9]; snprintf(crc,sizeof(crc),"%08X",cdm_crc32((unsigned char *)body,strlen(body)));
    snprintf(line,sizeof(line),"{\"integrity\":{\"algorithm\":\"crc32\",\"value\":\"%s\"},\"payload\":%s,\"protocol\":\"cdm/1\",\"sent_at\":\"2026-09-10T00:00:00Z\",\"sequence\":%u}\n",crc,payload,seq);
}
int main(void) {
    cdm_state s; cdm_init(&s);
    make_line(7); assert(cdm_accept(&s,line,strlen(line),0)); assert(!cdm_stale(&s,299999)); assert(cdm_stale(&s,300000));
    make_line(1); assert(!cdm_accept(&s,line,strlen(line),500)); assert(s.sequence==7);
    make_line(8); assert(cdm_accept(&s,line,strlen(line),600));
    make_line(9); char *crc=strstr(line,"\"value\":\""); assert(crc); crc+=9; *crc=(*crc=='A'?'B':'A');
    assert(!cdm_accept(&s,line,strlen(line),650)); assert(!strcmp(s.error,"CRC_MISMATCH")); assert(s.sequence==8);
    line[12]='X'; assert(!cdm_accept(&s,line,strlen(line),700)); assert(s.sequence==8);
    make_line(9); line[strlen(line)-1]='\r'; assert(!cdm_accept(&s,line,strlen(line),800));
    make_line(9); line[30]=(char)0xff; assert(!cdm_accept(&s,line,strlen(line),900));
    cdm_state wrap; cdm_init(&wrap);
    make_line(4294967295u); assert(cdm_accept(&wrap,line,strlen(line),0));
    make_line(0); assert(cdm_accept(&wrap,line,strlen(line),1));
    make_line(0x80000000u); assert(!cdm_accept(&wrap,line,strlen(line),2));
    cdm_free(&wrap);
    cdm_free(&s); puts("receiver state, CRC, canonical, stale: PASS"); return 0;
}
