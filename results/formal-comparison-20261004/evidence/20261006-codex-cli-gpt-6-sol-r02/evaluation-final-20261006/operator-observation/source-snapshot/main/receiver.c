#include "receiver.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

uint32_t cdm_crc32(const unsigned char *p, size_t n) {
    uint32_t c = 0xffffffffu;
    for (size_t i = 0; i < n; ++i) {
        c ^= p[i];
        for (int b = 0; b < 8; ++b) c = (c >> 1) ^ (0xedb88320u & -(int)(c & 1));
    }
    return ~c;
}
static bool valid_utf8(const unsigned char *s,size_t n) {
    for(size_t i=0;i<n;) {
        unsigned char c=s[i++];
        if(c<0x80) continue;
        int extra; uint32_t value, minimum;
        if(c>=0xC2&&c<=0xDF) { extra=1; value=c&31; minimum=0x80; }
        else if(c>=0xE0&&c<=0xEF) { extra=2; value=c&15; minimum=0x800; }
        else if(c>=0xF0&&c<=0xF4) { extra=3; value=c&7; minimum=0x10000; }
        else return false;
        if(i+extra>n) return false;
        for(int j=0;j<extra;j++) { if((s[i]&0xC0)!=0x80) return false; value=(value<<6)|(s[i++]&0x3f); }
        if(value<minimum || (value>=0xD800&&value<=0xDFFF) || value>0x10FFFF) return false;
    }
    return true;
}
static int cmp_key(const void *a, const void *b) {
    const cJSON *x = *(const cJSON *const *)a, *y = *(const cJSON *const *)b;
    return strcmp(x->string, y->string);
}
static cJSON *sorted_copy(const cJSON *src) {
    if (cJSON_IsArray(src)) {
        cJSON *dst = cJSON_CreateArray();
        if (!dst) return NULL;
        for (const cJSON *p = src->child; p; p = p->next) {
            cJSON *v = sorted_copy(p);
            if (!v) { cJSON_Delete(dst); return NULL; }
            cJSON_AddItemToArray(dst, v);
        }
        return dst;
    }
    if (cJSON_IsObject(src)) {
        int n = cJSON_GetArraySize(src);
        cJSON **keys = calloc(n ? n : 1, sizeof(*keys));
        cJSON *dst = cJSON_CreateObject();
        if (!keys || !dst) { free(keys); cJSON_Delete(dst); return NULL; }
        int i = 0;
        for (cJSON *p = src->child; p; p = p->next) keys[i++] = p;
        qsort(keys, n, sizeof(*keys), cmp_key);
        for (i = 0; i < n; ++i) {
            if (i && !strcmp(keys[i-1]->string, keys[i]->string)) { free(keys); cJSON_Delete(dst); return NULL; }
            cJSON *v = sorted_copy(keys[i]);
            if (!v) { free(keys); cJSON_Delete(dst); return NULL; }
            cJSON_AddItemToObject(dst, keys[i]->string, v);
        }
        free(keys);
        return dst;
    }
    return cJSON_Duplicate(src, false);
}
static bool field(const cJSON *o, const char *key, int kind) {
    const cJSON *v = cJSON_GetObjectItemCaseSensitive(o, key);
    return v && (v->type & 0xff) == kind;
}
static int64_t civil_days(int year,unsigned month,unsigned day) {
    year-=month<=2;
    const int era=(year>=0?year:year-399)/400;
    const unsigned yoe=(unsigned)(year-era*400);
    const unsigned doy=(153*(month+(month>2?-3:9))+2)/5+day-1;
    const unsigned doe=yoe*365+yoe/4-yoe/100+doy;
    return era*146097+(int)doe-719468;
}
bool cdm_timestamp(const char *s,int64_t *epoch) {
    if(!s || strlen(s)<20 || s[4]!='-' || s[7]!='-' || (s[10]!='T'&&s[10]!='t') || s[13]!=':' || s[16]!=':') return false;
    int y=0,m=0,d=0,h=0,mi=0,sec=0;
    if(sscanf(s,"%4d-%2d-%2dT%2d:%2d:%2d",&y,&m,&d,&h,&mi,&sec)!=6 || y<1970 || m<1 || m>12 || d<1 || h>23 || mi>59 || sec>59) return false;
    static const int days[]={31,28,31,30,31,30,31,31,30,31,30,31};
    int max=days[m-1]+(m==2 && y%4==0 && (y%100!=0 || y%400==0));
    if(d>max) return false;
    const char *tz=s+19;
    while(*tz>='0'&&*tz<='9') tz++; // fractional seconds
    if(*tz=='.') { tz++; if(*tz<'0'||*tz>'9') return false; while(*tz>='0'&&*tz<='9') tz++; }
    int offset=0;
    if(*tz=='+'||*tz=='-') { int oh=0,om=0; if(strlen(tz)!=6 || tz[3]!=':' || sscanf(tz+1,"%2d:%2d",&oh,&om)!=2 || oh>23 || om>59) return false; offset=(oh*60+om)*60*(*tz=='+'?1:-1); }
    else if(strcmp(tz,"Z")) return false;
    if(epoch) *epoch=civil_days(y,m,d)*86400+h*3600+mi*60+sec-offset;
    return true;
}
static bool time_or_null(const cJSON *o, const char *key) {
    const cJSON *v = cJSON_GetObjectItemCaseSensitive(o, key);
    if (cJSON_IsNull(v)) return true;
    if (!cJSON_IsString(v) || !v->valuestring) return false;
    return cdm_timestamp(v->valuestring,NULL);
}
static bool nullable_number(const cJSON *o, const char *key, double max) {
    const cJSON *v = cJSON_GetObjectItemCaseSensitive(o, key);
    return cJSON_IsNull(v) || (cJSON_IsNumber(v) && isfinite(v->valuedouble) && v->valuedouble >= 0 && v->valuedouble <= max);
}
static bool one_of(const char *v,const char *const *items,size_t n) {
    if(!v) return false;
    for(size_t i=0;i<n;i++) if(!strcmp(v,items[i])) return true;
    return false;
}
static bool only_keys(const cJSON *object,const char *const *keys,size_t count) {
    for(const cJSON *item=object->child;item;item=item->next) {
        if(!one_of(item->string,keys,count)) return false;
    }
    return true;
}
static bool identifier(const char *s,bool lower,bool colon) {
    if(!s || !*s) return false;
    for(size_t i=0;s[i];i++) {
        unsigned char c=(unsigned char)s[i];
        bool good=(c>='0'&&c<='9') || (c>='a'&&c<='z') || (!lower&&c>='A'&&c<='Z') || (i>0&&(c=='.'||c=='_'||c=='-'||(colon&&c==':')));
        if(!good) return false;
    }
    return true;
}
static bool optional_identity(const cJSON *o,const char *key) {
    cJSON *v=cJSON_GetObjectItemCaseSensitive(o,key);
    return cJSON_IsNull(v) || (cJSON_IsString(v)&&identifier(v->valuestring,true,false));
}
static bool optional_string(const cJSON *o,const char *key) {
    cJSON *v=cJSON_GetObjectItemCaseSensitive(o,key);
    return cJSON_IsNull(v) || (cJSON_IsString(v)&&v->valuestring[0]);
}
static bool validate_window(const cJSON *w) {
    static const char *const units[]={"percent","token","credit","unknown"};
    static const char *const keys[]={"window_id","label","used_units","remaining_units","limit_units","unit","percent_used","percent_remaining","resets_at","reset_status"};
    if (!cJSON_IsObject(w) || cJSON_GetArraySize(w)<9 || cJSON_GetArraySize(w)>10 || !field(w,"window_id",cJSON_String) || !field(w,"label",cJSON_String) || !field(w,"unit",cJSON_String) || !time_or_null(w,"resets_at")) return false;
    if(!only_keys(w,keys,10) || !identifier(cJSON_GetObjectItemCaseSensitive(w,"window_id")->valuestring,true,true) || !cJSON_GetObjectItemCaseSensitive(w,"label")->valuestring[0]) return false;
    cJSON *reset_status=cJSON_GetObjectItemCaseSensitive(w,"reset_status");
    static const char *const reset_values[]={"unknown","scheduled","expired"};
    if(reset_status && (!cJSON_IsString(reset_status) || !one_of(reset_status->valuestring,reset_values,3))) return false;
    if(!one_of(cJSON_GetObjectItemCaseSensitive(w,"unit")->valuestring,units,4)) return false;
    const char *number_keys[] = {"used_units","remaining_units","limit_units","percent_used","percent_remaining"};
    for (int i=0;i<5;i++) if (!nullable_number(w,number_keys[i], i<3 ? 1e18 : 100)) return false;
    cJSON *a=cJSON_GetObjectItemCaseSensitive(w,"used_units"), *b=cJSON_GetObjectItemCaseSensitive(w,"remaining_units"), *c=cJSON_GetObjectItemCaseSensitive(w,"limit_units");
    if (cJSON_IsNumber(a)&&cJSON_IsNumber(b)&&cJSON_IsNumber(c)&&fabs(a->valuedouble+b->valuedouble-c->valuedouble)>0.01) return false;
    a=cJSON_GetObjectItemCaseSensitive(w,"percent_used"); b=cJSON_GetObjectItemCaseSensitive(w,"percent_remaining");
    if(cJSON_IsNumber(a)&&cJSON_IsNumber(b)&&fabs(a->valuedouble+b->valuedouble-100.0)>0.01) return false;
    return true;
}
static bool validate_payload(const cJSON *p,int64_t sent_epoch) {
    static const char *const statuses[]={"available","unavailable","unsupported","unauthorized","error","stale"};
    static const char *const units[]={"percent","token","credit","unknown"};
    static const char *const metrics[]={"quota_window","token_balance","credits","session_telemetry"};
    static const char *const sources[]={"fixture","local_runtime","provider_api","ide_telemetry","unknown"};
    static const char *const usage_keys[]={"schema_version","snapshot_id","provider_id","agent_id","host_id","model_id","account_profile_id","source_kind","metric_kind","unit","status","observed_at","windows","stale","last_good_at","error_code","error_reason"};
    static const char *const global_keys[]={"schema_version","source","captured_at","latest_reset_at","forecast_24h_percent","forecast_48h_percent","forecast_is_schedule","stale","error_code"};
    cJSON *usage=cJSON_GetObjectItemCaseSensitive(p,"usage"), *global=cJSON_GetObjectItemCaseSensitive(p,"global_resets");
    if (!cJSON_IsObject(p) || !cJSON_IsArray(usage) || !cJSON_IsArray(global) || cJSON_GetArraySize(p)!=2) return false;
    for (cJSON *s=usage->child;s;s=s->next) {
        if (!cJSON_IsObject(s) || cJSON_GetArraySize(s)!=17 || !field(s,"provider_id",cJSON_String) || !field(s,"snapshot_id",cJSON_String) || !field(s,"status",cJSON_String) || !field(s,"source_kind",cJSON_String) || !field(s,"metric_kind",cJSON_String) || !field(s,"unit",cJSON_String) || !field(s,"schema_version",cJSON_Number) || cJSON_GetObjectItemCaseSensitive(s,"schema_version")->valuedouble!=1 || !time_or_null(s,"observed_at") || !time_or_null(s,"last_good_at") || (!field(s,"stale",cJSON_True) && !field(s,"stale",cJSON_False))) return false;
        if(!only_keys(s,usage_keys,17) || !identifier(cJSON_GetObjectItemCaseSensitive(s,"snapshot_id")->valuestring,false,true) || !identifier(cJSON_GetObjectItemCaseSensitive(s,"provider_id")->valuestring,true,false)) return false;
        if(!optional_identity(s,"agent_id") || !optional_identity(s,"host_id") || !optional_identity(s,"account_profile_id") || !optional_string(s,"model_id") || !optional_string(s,"error_code") || !optional_string(s,"error_reason")) return false;
        if(!one_of(cJSON_GetObjectItemCaseSensitive(s,"status")->valuestring,statuses,6) || !one_of(cJSON_GetObjectItemCaseSensitive(s,"unit")->valuestring,units,4) || !one_of(cJSON_GetObjectItemCaseSensitive(s,"metric_kind")->valuestring,metrics,4) || !one_of(cJSON_GetObjectItemCaseSensitive(s,"source_kind")->valuestring,sources,5)) return false;
        if(!cJSON_GetObjectItemCaseSensitive(s,"agent_id") || !cJSON_GetObjectItemCaseSensitive(s,"host_id") || !cJSON_GetObjectItemCaseSensitive(s,"model_id") || !cJSON_GetObjectItemCaseSensitive(s,"account_profile_id") || !cJSON_GetObjectItemCaseSensitive(s,"error_code") || !cJSON_GetObjectItemCaseSensitive(s,"error_reason")) return false;
        if(!strcmp(cJSON_GetObjectItemCaseSensitive(s,"status")->valuestring,"available") && (!cJSON_IsString(cJSON_GetObjectItemCaseSensitive(s,"agent_id")) || !cJSON_IsString(cJSON_GetObjectItemCaseSensitive(s,"host_id")))) return false;
        const char *times[]={"observed_at","last_good_at"};
        for(int i=0;i<2;i++) { cJSON *v=cJSON_GetObjectItemCaseSensitive(s,times[i]); int64_t when; if(cJSON_IsString(v) && (!cdm_timestamp(v->valuestring,&when) || when>sent_epoch)) return false; }
        cJSON *windows=cJSON_GetObjectItemCaseSensitive(s,"windows");
        if (!cJSON_IsArray(windows)) return false;
        for (cJSON *w=windows->child;w;w=w->next) if (!validate_window(w)) return false;
    }
    for (cJSON *g=global->child;g;g=g->next) {
        const cJSON *source_item=cJSON_GetObjectItemCaseSensitive(g,"source");
        const char *source=cJSON_IsString(source_item)?source_item->valuestring:NULL;
        if (!cJSON_IsObject(g) || cJSON_GetArraySize(g)!=9 || !field(g,"source",cJSON_String) ||
            (!source || (strcmp(source,"codex-resets.com") && strcmp(source,"codex-reset.com"))) ||
            !field(g,"captured_at",cJSON_String) || !cdm_timestamp(cJSON_GetObjectItemCaseSensitive(g,"captured_at")->valuestring,NULL) || !time_or_null(g,"latest_reset_at") || !nullable_number(g,"forecast_24h_percent",100) || !nullable_number(g,"forecast_48h_percent",100) || !field(g,"forecast_is_schedule",cJSON_False)) return false;
        if(!only_keys(g,global_keys,9) || !field(g,"schema_version",cJSON_Number) || cJSON_GetObjectItemCaseSensitive(g,"schema_version")->valuedouble!=1 || !optional_string(g,"error_code") || (!field(g,"stale",cJSON_True) && !field(g,"stale",cJSON_False))) return false;
    }
    return true;
}
void cdm_init(cdm_state *s) { memset(s,0,sizeof(*s)); }
void cdm_free(cdm_state *s) { cJSON_Delete(s->payload); s->payload=NULL; }
bool cdm_accept(cdm_state *s, const char *line, size_t len, uint64_t now_ms) {
    const char *reason="FRAME_INVALID";
    cJSON *root=NULL,*canon=NULL,*envelope=NULL; char *printed=NULL,*body=NULL;
    if (!line || len<2 || len>CDM_MAX_FRAME || line[len-1]!='\n' || memchr(line,'\r',len) || memchr(line,'\0',len) || !valid_utf8((const unsigned char *)line,len-1)) goto fail;
    root=cJSON_ParseWithLength(line,len-1);
    if (!root || !cJSON_IsObject(root) || cJSON_GetArraySize(root)!=5) goto fail;
    canon=sorted_copy(root);
    if (!canon) goto fail;
    printed=cJSON_PrintUnformatted(canon);
    if (!printed || strlen(printed)!=len-1 || memcmp(printed,line,len-1)) { reason="NONCANONICAL"; goto fail; }
    cJSON *protocol=cJSON_GetObjectItemCaseSensitive(root,"protocol"), *seq=cJSON_GetObjectItemCaseSensitive(root,"sequence"), *integrity=cJSON_GetObjectItemCaseSensitive(root,"integrity");
    int64_t sent_epoch=0;
    if (!cJSON_IsString(protocol) || strcmp(protocol->valuestring,"cdm/1") || !cJSON_IsNumber(seq) || seq->valuedouble<0 || seq->valuedouble>4294967295.0 || floor(seq->valuedouble)!=seq->valuedouble || !field(root,"sent_at",cJSON_String) || !cdm_timestamp(cJSON_GetObjectItemCaseSensitive(root,"sent_at")->valuestring,&sent_epoch) || !cJSON_IsObject(integrity) || cJSON_GetArraySize(integrity)!=2) goto fail;
    if (!field(integrity,"algorithm",cJSON_String) || strcmp(cJSON_GetObjectItemCaseSensitive(integrity,"algorithm")->valuestring,"crc32") || !field(integrity,"value",cJSON_String)) goto fail;
    const char *hex=cJSON_GetObjectItemCaseSensitive(integrity,"value")->valuestring;
    if (strlen(hex)!=8) goto fail;
    for (int i=0;i<8;i++) if (!((hex[i]>='0'&&hex[i]<='9')||(hex[i]>='A'&&hex[i]<='F'))) goto fail;
    envelope=cJSON_Duplicate(root,true);
    cJSON_DeleteItemFromObjectCaseSensitive(envelope,"integrity");
    cJSON *sorted=sorted_copy(envelope);
    cJSON_Delete(envelope); envelope=sorted;
    if (!envelope || !(body=cJSON_PrintUnformatted(envelope))) goto fail;
    char expected[9]; snprintf(expected,sizeof(expected),"%08lX",(unsigned long)cdm_crc32((unsigned char *)body,strlen(body)));
    if (strcmp(hex,expected)) { reason="CRC_MISMATCH"; goto fail; }
    if (!validate_payload(cJSON_GetObjectItemCaseSensitive(root,"payload"),sent_epoch)) { reason="SCHEMA_INVALID"; goto fail; }
    uint32_t candidate=(uint32_t)seq->valuedouble;
    if (s->has_sequence) {
        uint32_t delta=candidate-s->sequence;
        if (!delta || delta>=0x80000000u) { reason="SEQUENCE_OLD"; goto fail; }
    }
    cJSON *payload=cJSON_DetachItemFromObjectCaseSensitive(root,"payload");
    cJSON_Delete(s->payload); s->payload=payload; s->sequence=candidate; s->has_sequence=true; s->received_ms=now_ms; s->sent_epoch=sent_epoch; s->error[0]=0;
    free(printed); free(body); cJSON_Delete(canon); cJSON_Delete(envelope); cJSON_Delete(root); return true;
fail:
    snprintf(s->error,sizeof(s->error),"%s",reason);
    free(printed); free(body); cJSON_Delete(canon); cJSON_Delete(envelope); cJSON_Delete(root); return false;
}
bool cdm_stale(const cdm_state *s,uint64_t now_ms) { return !s->has_sequence || now_ms-s->received_ms>=300000; }
