#include "cdm.h"
#include <ctype.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { const unsigned char *p, *end; unsigned depth; } scan;

static bool utf8(const unsigned char *p, size_t n)
{
    for (size_t i = 0; i < n;) {
        unsigned char c = p[i++];
        if (c < 0x80) continue;
        unsigned count = c >= 0xF0 && c <= 0xF4 ? 3 : c >= 0xE0 && c <= 0xEF ? 2 : c >= 0xC2 && c <= 0xDF ? 1 : 0;
        if (!count || i + count > n) return false;
        unsigned char first = p[i];
        if ((c == 0xE0 && first < 0xA0) || (c == 0xED && first >= 0xA0) ||
            (c == 0xF0 && first < 0x90) || (c == 0xF4 && first >= 0x90)) return false;
        while (count--) if ((p[i++] & 0xC0) != 0x80) return false;
    }
    return true;
}

static bool scan_string(scan *s, const unsigned char **start, size_t *length)
{
    if (s->p == s->end || *s->p++ != '"') return false;
    *start = s->p;
    while (s->p < s->end && *s->p != '"') {
        unsigned char c = *s->p++;
        if (c < 0x20) return false;
        if (c != '\\') continue;
        if (s->p == s->end) return false;
        c = *s->p++;
        if (c == 'u') {
            if (s->end - s->p < 4) return false;
            unsigned v = 0;
            for (int i = 0; i < 4; i++) {
                unsigned char h = *s->p++;
                if (!isxdigit(h) || (h >= 'A' && h <= 'F')) return false;
                v = v * 16 + (h <= '9' ? h - '0' : h - 'a' + 10);
            }
            if (v >= 0x20 || v == 8 || v == 9 || v == 10 || v == 12 || v == 13) return false;
        } else if (!strchr("\"\\bfnrt", c)) return false;
    }
    if (s->p == s->end) return false;
    *length = (size_t)(s->p - *start);
    s->p++;
    return true;
}

static bool canonical_number(const unsigned char *begin,size_t length)
{
    if (!length || length>=64) return false;
    char original[64]; memcpy(original,begin,length); original[length]=0;
    if (!strpbrk(original,".eE")) return strcmp(original,"-0")!=0;
    char *end; double value=strtod(original,&end);
    if (*end || !isfinite(value)) return false;
    char scientific[64],digits[32],expected[128];
    int precision;
    for(precision=1;precision<=17;precision++) {
        snprintf(scientific,sizeof scientific,"%.*e",precision-1,value);
        double check=strtod(scientific,NULL);
        if (!memcmp(&check,&value,sizeof value)) break;
    }
    if (precision>17) return false;
    char *e=strchr(scientific,'e'); if (!e) return false;
    int exponent=atoi(e+1), n=0;
    for(char *p=scientific; p<e; p++) if (isdigit((unsigned char)*p)) digits[n++]=*p;
    digits[n]=0;
    char *p=expected;
    if (signbit(value)) *p++='-';
    if (exponent>=-4 && exponent<16) {
        int point=exponent+1;
        if (point<=0) { *p++='0'; *p++='.'; while(point++<0) *p++='0'; memcpy(p,digits,n); p+=n; }
        else if (point>=n) { memcpy(p,digits,n); p+=n; while(point-->n) *p++='0'; *p++='.'; *p++='0'; }
        else { memcpy(p,digits,point); p+=point; *p++='.'; memcpy(p,digits+point,n-point); p+=n-point; }
    } else {
        *p++=digits[0]; if (n>1) { *p++='.'; memcpy(p,digits+1,n-1); p+=n-1; }
        *p++='e'; *p++=exponent<0?'-':'+';
        unsigned x=(unsigned)(exponent<0?-exponent:exponent);
        if (x<10) *p++='0';
        p+=sprintf(p,"%u",x);
    }
    *p=0;
    return strlen(expected)==length && !memcmp(expected,original,length);
}

static bool scan_value(scan *s)
{
    if (s->p == s->end || ++s->depth > 64) return false;
    unsigned char c = *s->p;
    if (c == '{') {
        s->p++;
        const unsigned char *previous = NULL;
        size_t previous_len = 0;
        while (s->p < s->end && *s->p != '}') {
            const unsigned char *key;
            size_t key_len;
            if (!scan_string(s, &key, &key_len) || s->p == s->end || *s->p++ != ':') return false;
            if (previous) {
                size_t common=key_len<previous_len?key_len:previous_len;
                int cmp=memcmp(previous,key,common);
                if (cmp>0 || (cmp==0 && previous_len>=key_len)) return false;
            }
            previous = key; previous_len = key_len;
            if (!scan_value(s)) return false;
            if (s->p == s->end || *s->p == '}') break;
            if (*s->p++ != ',' || s->p == s->end || *s->p == '}') return false;
        }
        if (s->p == s->end || *s->p++ != '}') return false;
    } else if (c == '[') {
        s->p++;
        while (s->p < s->end && *s->p != ']') {
            if (!scan_value(s)) return false;
            if (s->p == s->end || *s->p == ']') break;
            if (*s->p++ != ',' || s->p == s->end || *s->p == ']') return false;
        }
        if (s->p == s->end || *s->p++ != ']') return false;
    } else if (c == '"') {
        const unsigned char *start; size_t len;
        if (!scan_string(s, &start, &len)) return false;
    } else if (c == 't' || c == 'f' || c == 'n') {
        const char *word = c == 't' ? "true" : c == 'f' ? "false" : "null";
        size_t len = strlen(word);
        if ((size_t)(s->end - s->p) < len || memcmp(s->p, word, len)) return false;
        s->p += len;
    } else {
        const unsigned char *number_start=s->p;
        if (*s->p == '-') s->p++;
        if (s->p == s->end) return false;
        if (*s->p == '0') s->p++;
        else {
            if (*s->p < '1' || *s->p > '9') return false;
            while (s->p < s->end && isdigit(*s->p)) s->p++;
        }
        if (s->p < s->end && *s->p == '.') {
            s->p++;
            if (s->p == s->end || !isdigit(*s->p)) return false;
            while (s->p < s->end && isdigit(*s->p)) s->p++;
        }
        if (s->p < s->end && (*s->p == 'e' || *s->p == 'E')) {
            s->p++;
            if (s->p < s->end && (*s->p == '+' || *s->p == '-')) s->p++;
            if (s->p == s->end || !isdigit(*s->p)) return false;
            while (s->p < s->end && isdigit(*s->p)) s->p++;
        }
        if (!canonical_number(number_start,(size_t)(s->p-number_start))) return false;
    }
    s->depth--;
    return true;
}

uint32_t cdm_crc32(const unsigned char *bytes, size_t length)
{
    uint32_t crc = 0xFFFFFFFFu;
    for (size_t i = 0; i < length; i++) {
        crc ^= bytes[i];
        for (int b = 0; b < 8; b++) crc = (crc >> 1) ^ (0xEDB88320u & -(crc & 1u));
    }
    return ~crc;
}

static bool number(const cJSON *v, double lo, double hi, bool nullable)
{ return v && (nullable && cJSON_IsNull(v) || cJSON_IsNumber(v) && isfinite(v->valuedouble) && v->valuedouble >= lo && v->valuedouble <= hi); }
static bool string(const cJSON *v, bool nullable)
{ return v && (nullable && cJSON_IsNull(v) || cJSON_IsString(v) && v->valuestring[0]); }
static bool literal(const cJSON *v, const char *words)
{
    if (!cJSON_IsString(v)) return false;
    size_t len = strlen(v->valuestring);
    const char *p = words;
    while (*p) { const char *end = strchr(p, '|'); if (!end) end = p + strlen(p);
        if ((size_t)(end-p) == len && !memcmp(p, v->valuestring, len)) return true;
        p = *end ? end+1 : end;
    }
    return false;
}
static bool error_code(const cJSON *v)
{
    if (cJSON_IsNull(v)) return true;
    if (!cJSON_IsString(v) || v->valuestring[0]<'A' || v->valuestring[0]>'Z') return false;
    for(const char *p=v->valuestring+1;*p;p++)
        if (!(*p>='A'&&*p<='Z') && !isdigit((unsigned char)*p) && *p!='_' && *p!='.' && *p!='-') return false;
    return true;
}
static bool keys(const cJSON *obj, const char *required, const char *optional)
{
    if (!cJSON_IsObject(obj)) return false;
    for (const cJSON *p = obj->child; p; p = p->next) {
        char term[80]; int n = snprintf(term, sizeof term, "|%s|", p->string);
        if (n < 0 || n >= sizeof term || (!strstr(required, term) && !strstr(optional, term))) return false;
    }
    const char *p = required;
    while (*p) {
        if (*p == '|') { p++; continue; }
        const char *end = strchr(p, '|'); if (!end) return false;
        char name[80]; size_t n = (size_t)(end-p); if (n >= sizeof name) return false;
        memcpy(name,p,n); name[n]=0;
        if (!cJSON_GetObjectItemCaseSensitive(obj,name)) return false;
        p=end;
    }
    return true;
}
static bool ident(const cJSON *v, bool lower, bool nullable)
{
    if (nullable && cJSON_IsNull(v)) return true;
    if (!cJSON_IsString(v) || !v->valuestring[0]) return false;
    const char *p=v->valuestring;
    if (!isalnum((unsigned char)*p) || lower && !(*p >= 'a' && *p <= 'z' || isdigit((unsigned char)*p))) return false;
    for (; *p; p++) if (!(lower ? (*p >= 'a' && *p <= 'z') : isalnum((unsigned char)*p)) &&
        !isdigit((unsigned char)*p) && *p!='.' && *p!='_' && *p!='-' && (!lower && *p!=':')) return false;
    return true;
}

static int64_t days_from_civil(int y, unsigned m, unsigned d)
{
    y -= m <= 2; const int era = (y >= 0 ? y : y-399)/400;
    const unsigned yoe = (unsigned)(y-era*400); const unsigned doy=(153*(m+(m>2?-3:9))+2)/5+d-1;
    const unsigned doe=yoe*365+yoe/4-yoe/100+doy;
    return (int64_t)era*146097+(int)doe-719468;
}
static bool digits(const char **p, int count, int *v)
{ *v=0; while(count--) { if (!isdigit((unsigned char)**p)) return false; *v=*v*10+(*(*p)++-'0'); } return true; }
bool cdm_parse_time(const char *value, int64_t *utc_us)
{
    if (!value || !utc_us) return false;
    const char *p=value; int y,m,d,h,mi,s,oh=0,om=0;
    if (!digits(&p,4,&y) || *p++!='-' || !digits(&p,2,&m) || *p++!='-' || !digits(&p,2,&d) ||
        (*p++!='T' && p[-1]!='t') || !digits(&p,2,&h) || *p++!=':' || !digits(&p,2,&mi) ||
        *p++!=':' || !digits(&p,2,&s)) return false;
    int64_t frac=0; int scale=100000;
    if (*p=='.') { p++; if (!isdigit((unsigned char)*p)) return false;
        while (isdigit((unsigned char)*p)) { if (scale) { frac+=(*p-'0')*scale; scale/=10; } p++; }
    }
    int sign=0;
    if (*p=='Z' || *p=='z') p++;
    else if (*p=='+' || *p=='-') { sign=*p++=='+'?1:-1;
        if (!digits(&p,2,&oh) || *p++!=':' || !digits(&p,2,&om)) return false;
    } else return false;
    if (*p || y<1 || m<1 || m>12 || h>23 || mi>59 || s>59 || oh>23 || om>59) return false;
    int leap=(y%4==0 && (y%100!=0 || y%400==0));
    const int mdays[]={0,31,28+leap,31,30,31,30,31,31,30,31,30,31};
    if (d<1 || d>mdays[m]) return false;
    *utc_us=(((days_from_civil(y,m,d)*24+h)*60+mi)*60+s-(sign*(oh*60+om)*60))*1000000+frac;
    return true;
}
static bool timestamp(const cJSON *v, bool nullable, int64_t *out)
{ if (nullable && cJSON_IsNull(v)) return true; return cJSON_IsString(v) && cdm_parse_time(v->valuestring,out); }
static bool window(const cJSON *w, bool session, int64_t anchor)
{
    const char *req="|window_id|label|used_units|remaining_units|limit_units|unit|percent_used|percent_remaining|resets_at|";
    if (!keys(w,req,"|reset_status|") || !ident(cJSON_GetObjectItemCaseSensitive(w,"window_id"),false,false) ||
        !string(cJSON_GetObjectItemCaseSensitive(w,"label"),false) ||
        !literal(cJSON_GetObjectItemCaseSensitive(w,"unit"),"percent|token|credit|unknown")) return false;
    const char *nums[]={"used_units","remaining_units","limit_units","percent_used","percent_remaining"};
    for (int i=0;i<5;i++) if (!number(cJSON_GetObjectItemCaseSensitive(w,nums[i]),0,i>=3?100:9007199254740991.0,true)) return false;
    int64_t t; if (!timestamp(cJSON_GetObjectItemCaseSensitive(w,"resets_at"),true,&t)) return false;
    const cJSON *rs=cJSON_GetObjectItemCaseSensitive(w,"reset_status");
    if (rs && !literal(rs,"unknown|scheduled|expired")) return false;
    if (cJSON_IsString(cJSON_GetObjectItemCaseSensitive(w,"resets_at")) && rs &&
        (literal(rs,"scheduled") && t<=anchor || literal(rs,"expired") && t>anchor)) return false;
    if (session) {
        if (!literal(cJSON_GetObjectItemCaseSensitive(w,"unit"),"token")) return false;
        const char *nulls[]={"remaining_units","limit_units","percent_used","percent_remaining","resets_at"};
        for(int i=0;i<5;i++) if (!cJSON_IsNull(cJSON_GetObjectItemCaseSensitive(w,nulls[i]))) return false;
        if (rs && !literal(rs,"unknown")) return false;
    } else {
        const cJSON *used=cJSON_GetObjectItemCaseSensitive(w,"used_units"), *rem=cJSON_GetObjectItemCaseSensitive(w,"remaining_units"),
            *lim=cJSON_GetObjectItemCaseSensitive(w,"limit_units"), *pu=cJSON_GetObjectItemCaseSensitive(w,"percent_used"),
            *pr=cJSON_GetObjectItemCaseSensitive(w,"percent_remaining");
        if (cJSON_IsNumber(used)&&cJSON_IsNumber(rem)&&cJSON_IsNumber(lim)&&fabs(used->valuedouble+rem->valuedouble-lim->valuedouble)>0.01) return false;
        if (cJSON_IsNumber(pu)&&cJSON_IsNumber(pr)&&fabs(pu->valuedouble+pr->valuedouble-100)>0.05) return false;
    }
    return true;
}
static bool snapshot(const cJSON *v, int64_t anchor)
{
    const char *req="|schema_version|snapshot_id|provider_id|agent_id|host_id|model_id|account_profile_id|source_kind|metric_kind|unit|status|observed_at|windows|stale|last_good_at|error_code|error_reason|";
    if (!keys(v,req,"") || !cJSON_IsNumber(cJSON_GetObjectItemCaseSensitive(v,"schema_version")) ||
        cJSON_GetObjectItemCaseSensitive(v,"schema_version")->valuedouble!=1 ||
        !ident(cJSON_GetObjectItemCaseSensitive(v,"snapshot_id"),false,false) ||
        !ident(cJSON_GetObjectItemCaseSensitive(v,"provider_id"),true,false) ||
        !ident(cJSON_GetObjectItemCaseSensitive(v,"agent_id"),true,true) ||
        !ident(cJSON_GetObjectItemCaseSensitive(v,"host_id"),true,true) ||
        !string(cJSON_GetObjectItemCaseSensitive(v,"model_id"),true) ||
        !ident(cJSON_GetObjectItemCaseSensitive(v,"account_profile_id"),true,true) ||
        !literal(cJSON_GetObjectItemCaseSensitive(v,"source_kind"),"fixture|local_runtime|provider_api|ide_telemetry|unknown") ||
        !literal(cJSON_GetObjectItemCaseSensitive(v,"metric_kind"),"quota_window|token_balance|credits|session_telemetry") ||
        !literal(cJSON_GetObjectItemCaseSensitive(v,"unit"),"percent|token|credit|unknown") ||
        !literal(cJSON_GetObjectItemCaseSensitive(v,"status"),"available|unavailable|unsupported|unauthorized|error|stale") ||
        !cJSON_IsBool(cJSON_GetObjectItemCaseSensitive(v,"stale")) ||
        !error_code(cJSON_GetObjectItemCaseSensitive(v,"error_code")) ||
        !string(cJSON_GetObjectItemCaseSensitive(v,"error_reason"),true)) return false;
    const cJSON *status=cJSON_GetObjectItemCaseSensitive(v,"status"), *metric=cJSON_GetObjectItemCaseSensitive(v,"metric_kind");
    bool available=literal(status,"available"), session=literal(metric,"session_telemetry");
    if (available && (cJSON_IsNull(cJSON_GetObjectItemCaseSensitive(v,"agent_id")) || cJSON_IsNull(cJSON_GetObjectItemCaseSensitive(v,"host_id")) ||
        !cJSON_IsNull(cJSON_GetObjectItemCaseSensitive(v,"error_code")) || !cJSON_IsNull(cJSON_GetObjectItemCaseSensitive(v,"error_reason")))) return false;
    if (!available && !literal(status,"unavailable|unsupported|unauthorized") &&
        (cJSON_IsNull(cJSON_GetObjectItemCaseSensitive(v,"error_code")) || cJSON_IsNull(cJSON_GetObjectItemCaseSensitive(v,"error_reason")))) return false;
    if (session && !cJSON_IsNull(cJSON_GetObjectItemCaseSensitive(v,"account_profile_id"))) return false;
    if (session && !literal(cJSON_GetObjectItemCaseSensitive(v,"unit"),"token")) return false;
    if (literal(status,"stale") && !cJSON_IsTrue(cJSON_GetObjectItemCaseSensitive(v,"stale"))) return false;
    int64_t t;
    const char *times[]={"observed_at","last_good_at"};
    for(int i=0;i<2;i++) { const cJSON *tv=cJSON_GetObjectItemCaseSensitive(v,times[i]);
        if (!timestamp(tv,true,&t) || (cJSON_IsString(tv) && t>anchor)) return false; }
    cJSON *wins=cJSON_GetObjectItemCaseSensitive(v,"windows"); if (!cJSON_IsArray(wins)) return false;
    bool seen[6]={0};
    const char *channels[]={"input","output","cached_input","reasoning_output","source_total","normalized_total"};
    for(cJSON *w=wins->child;w;w=w->next) {
        if (!window(w,session,anchor)) return false;
        const char *id=cJSON_GetObjectItemCaseSensitive(w,"window_id")->valuestring;
        for(cJSON *other=wins->child;other!=w;other=other->next)
            if (!strcmp(id,cJSON_GetObjectItemCaseSensitive(other,"window_id")->valuestring)) return false;
        if (session) {
            int j=0; while(j<6 && strcmp(id,channels[j])) j++;
            if (j==6) return false;
            seen[j]=true;
            const cJSON *n=cJSON_GetObjectItemCaseSensitive(w,"used_units");
            if (available && !cJSON_IsNumber(n)) return false;
        }
    }
    if (session && (available || wins->child)) {
        for(int i=0;i<6;i++) if (!seen[i]) return false;
        const cJSON *input=NULL,*output=NULL,*cached=NULL,*reason=NULL,*norm=NULL;
        for(cJSON *w=wins->child;w;w=w->next) {
            const char *id=cJSON_GetObjectItemCaseSensitive(w,"window_id")->valuestring;
            const cJSON *n=cJSON_GetObjectItemCaseSensitive(w,"used_units");
            if (!strcmp(id,"input")) input=n; else if (!strcmp(id,"output")) output=n;
            else if (!strcmp(id,"cached_input")) cached=n; else if (!strcmp(id,"reasoning_output")) reason=n;
            else if (!strcmp(id,"normalized_total")) norm=n;
        }
        if (cJSON_IsNumber(cached)&&cJSON_IsNumber(input)&&cached->valuedouble>input->valuedouble ||
            cJSON_IsNumber(reason)&&cJSON_IsNumber(output)&&reason->valuedouble>output->valuedouble ||
            cJSON_IsNumber(norm)&&cJSON_IsNumber(input)&&cJSON_IsNumber(output)&&norm->valuedouble!=input->valuedouble+output->valuedouble) return false;
    }
    return true;
}
static bool global_reset(const cJSON *v, int64_t anchor)
{
    const char *req="|schema_version|source|captured_at|latest_reset_at|forecast_24h_percent|forecast_48h_percent|forecast_is_schedule|stale|error_code|";
    int64_t t;
    const cJSON *captured=cJSON_GetObjectItemCaseSensitive(v,"captured_at");
    return keys(v,req,"") && cJSON_IsNumber(cJSON_GetObjectItemCaseSensitive(v,"schema_version")) &&
        cJSON_GetObjectItemCaseSensitive(v,"schema_version")->valuedouble==1 &&
        string(cJSON_GetObjectItemCaseSensitive(v,"source"),false) &&
        timestamp(captured,false,&t) && t<=anchor &&
        timestamp(cJSON_GetObjectItemCaseSensitive(v,"latest_reset_at"),true,&t) &&
        number(cJSON_GetObjectItemCaseSensitive(v,"forecast_24h_percent"),0,100,true) &&
        number(cJSON_GetObjectItemCaseSensitive(v,"forecast_48h_percent"),0,100,true) &&
        cJSON_IsFalse(cJSON_GetObjectItemCaseSensitive(v,"forecast_is_schedule")) &&
        cJSON_IsBool(cJSON_GetObjectItemCaseSensitive(v,"stale")) &&
        error_code(cJSON_GetObjectItemCaseSensitive(v,"error_code"));
}

void cdm_init(cdm_state *s) { memset(s,0,sizeof *s); }
static void free_entries(cdm_entry *entries,size_t count)
{
    if (!entries) return;
    for(size_t i=0;i<count;i++) { free(entries[i].key); cJSON_Delete(entries[i].current); cJSON_Delete(entries[i].good); }
    free(entries);
}
void cdm_free(cdm_state *s)
{
    free_entries(s->usage,s->usage_count); free_entries(s->global,s->global_count); cdm_init(s);
}
bool cdm_newer(uint32_t current,uint32_t candidate)
{ uint32_t delta=candidate-current; return delta>0 && delta<0x80000000u; }
static bool merge(cdm_entry **list,size_t *count,const cJSON *record,const char *key,bool good,uint64_t now)
{
    cdm_entry *entry=NULL;
    for(size_t i=0;i<*count;i++) if (!strcmp((*list)[i].key,key)) { entry=&(*list)[i]; break; }
    if (!entry) {
        cdm_entry *more=realloc(*list,(*count+1)*sizeof **list); if (!more) return false;
        *list=more; entry=&more[(*count)++]; memset(entry,0,sizeof *entry);
        entry->key=malloc(strlen(key)+1); if (!entry->key) return false; strcpy(entry->key,key);
    }
    cJSON *copy=cJSON_Duplicate(record,1); if (!copy) return false;
    cJSON_Delete(entry->current); entry->current=copy; entry->received_ms=now;
    if (good) { copy=cJSON_Duplicate(record,1); if (!copy) return false; cJSON_Delete(entry->good); entry->good=copy; }
    return true;
}
static cdm_entry *clone_entries(const cdm_entry *source,size_t count)
{
    if (!count) return NULL;
    cdm_entry *copy=calloc(count,sizeof *copy); if (!copy) return NULL;
    for(size_t i=0;i<count;i++) {
        copy[i].key=malloc(strlen(source[i].key)+1);
        if (copy[i].key) strcpy(copy[i].key,source[i].key);
        copy[i].current=cJSON_Duplicate(source[i].current,1);
        if (source[i].good) copy[i].good=cJSON_Duplicate(source[i].good,1);
        copy[i].received_ms=source[i].received_ms;
        if (!copy[i].key || !copy[i].current || source[i].good && !copy[i].good) {
            free_entries(copy,count); return NULL;
        }
    }
    return copy;
}
bool cdm_accept(cdm_state *s,const unsigned char *line,size_t length,uint64_t mono_ms)
{
    const char *why="FRAME_BYTES"; cJSON *frame=NULL;
    cdm_entry *next_usage=NULL,*next_global=NULL;
    size_t next_usage_count=s->usage_count,next_global_count=s->global_count;
    if (!line || !length || length>CDM_MAX_FRAME || line[length-1]!='\n' ||
        memchr(line,'\n',length-1) || memchr(line,'\r',length) || memchr(line,0,length) ||
        !utf8(line,length-1)) goto bad;
    why="FRAME_CANONICAL";
    scan sc={line,line+length-1,0}; if (!scan_value(&sc) || sc.p!=sc.end) goto bad;
    why="FRAME_SHAPE";
    frame=cJSON_ParseWithLengthOpts((const char *)line,length-1,NULL,0);
    if (!frame || !keys(frame,"|protocol|sequence|sent_at|payload|integrity|","")) goto bad;
    cJSON *integrity=cJSON_GetObjectItemCaseSensitive(frame,"integrity"), *payload=cJSON_GetObjectItemCaseSensitive(frame,"payload");
    cJSON *seq=cJSON_GetObjectItemCaseSensitive(frame,"sequence"), *stamp=cJSON_GetObjectItemCaseSensitive(frame,"sent_at");
    if (!literal(cJSON_GetObjectItemCaseSensitive(frame,"protocol"),"cdm/1") ||
        !number(seq,0,4294967295.0,false) || floor(seq->valuedouble)!=seq->valuedouble ||
        !keys(integrity,"|algorithm|value|","") || !literal(cJSON_GetObjectItemCaseSensitive(integrity,"algorithm"),"crc32") ||
        !string(cJSON_GetObjectItemCaseSensitive(integrity,"value"),false) || !keys(payload,"|usage|global_resets|","")) goto bad;
    const char *hex=cJSON_GetObjectItemCaseSensitive(integrity,"value")->valuestring;
    if (strlen(hex)!=8) goto bad; for(int i=0;i<8;i++) if (!isxdigit((unsigned char)hex[i]) || hex[i]>='a' && hex[i]<='f') goto bad;
    why="FRAME_INTEGRITY";
    if (line[0]!='{' || memcmp(line+1,"\"integrity\":",12)) goto bad;
    scan start={line+13,line+length-1,0}; if (!scan_value(&start) || *start.p++!=',') goto bad;
    uint32_t crc;
    size_t unsigned_len=(size_t)(sc.end-start.p)+1;
    unsigned char *unsigned_bytes=malloc(unsigned_len); if (!unsigned_bytes) { why="NO_MEMORY"; goto bad; }
    unsigned_bytes[0]='{'; memcpy(unsigned_bytes+1,start.p,unsigned_len-1);
    crc=cdm_crc32(unsigned_bytes,unsigned_len); free(unsigned_bytes);
    char expected[9]; snprintf(expected,sizeof expected,"%08X",crc);
    if (strcmp(hex,expected)) { why="CRC_MISMATCH"; goto bad; }
    why="FRAME_TIME";
    int64_t anchor; if (!timestamp(stamp,false,&anchor)) goto bad;
    if (!cJSON_IsArray(cJSON_GetObjectItemCaseSensitive(payload,"usage")) ||
        !cJSON_IsArray(cJSON_GetObjectItemCaseSensitive(payload,"global_resets"))) goto bad;
    cJSON *usage=cJSON_GetObjectItemCaseSensitive(payload,"usage"), *global=cJSON_GetObjectItemCaseSensitive(payload,"global_resets");
    why="SNAPSHOT_INVALID";
    for(cJSON *v=usage->child;v;v=v->next) {
        if (!snapshot(v,anchor)) goto bad;
        const char *id=cJSON_GetObjectItemCaseSensitive(v,"snapshot_id")->valuestring;
        for(cJSON *p=usage->child;p!=v;p=p->next) if (!strcmp(id,cJSON_GetObjectItemCaseSensitive(p,"snapshot_id")->valuestring)) goto bad;
    }
    why="GLOBAL_INVALID";
    for(cJSON *v=global->child;v;v=v->next) {
        if (!global_reset(v,anchor)) goto bad;
        const char *id=cJSON_GetObjectItemCaseSensitive(v,"source")->valuestring;
        for(cJSON *p=global->child;p!=v;p=p->next) if (!strcmp(id,cJSON_GetObjectItemCaseSensitive(p,"source")->valuestring)) goto bad;
    }
    uint32_t candidate=(uint32_t)seq->valuedouble;
    if (s->has_sequence && !cdm_newer(s->sequence,candidate)) { why="SEQUENCE_OLD"; goto bad; }
    why="NO_MEMORY";
    next_usage=clone_entries(s->usage,s->usage_count);
    if (s->usage_count && !next_usage) goto bad;
    next_global=clone_entries(s->global,s->global_count);
    if (s->global_count && !next_global) goto bad;
    for(cJSON *v=usage->child;v;v=v->next) {
        const char *key=cJSON_GetObjectItemCaseSensitive(v,"snapshot_id")->valuestring;
        bool good=literal(cJSON_GetObjectItemCaseSensitive(v,"status"),"available") && !cJSON_IsTrue(cJSON_GetObjectItemCaseSensitive(v,"stale"));
        if (!merge(&next_usage,&next_usage_count,v,key,good,mono_ms)) goto bad;
    }
    for(cJSON *v=global->child;v;v=v->next) {
        const char *key=cJSON_GetObjectItemCaseSensitive(v,"source")->valuestring;
        bool good=!cJSON_IsTrue(cJSON_GetObjectItemCaseSensitive(v,"stale")) &&
            cJSON_IsNull(cJSON_GetObjectItemCaseSensitive(v,"error_code")) &&
            cJSON_IsString(cJSON_GetObjectItemCaseSensitive(v,"latest_reset_at"));
        if (!merge(&next_global,&next_global_count,v,key,good,mono_ms)) goto bad;
    }
    free_entries(s->usage,s->usage_count); free_entries(s->global,s->global_count);
    s->usage=next_usage; s->usage_count=next_usage_count;
    s->global=next_global; s->global_count=next_global_count;
    s->sequence=candidate; s->has_sequence=true; s->has_frame=true; s->received_ms=mono_ms;
    s->anchor_utc_us=anchor; s->anchor_mono_ms=mono_ms; s->has_anchor=true; s->wire_error[0]=0;
    cJSON_Delete(frame); return true;
bad:
    snprintf(s->wire_error,sizeof s->wire_error,"%s",why);
    free_entries(next_usage,next_usage_count); free_entries(next_global,next_global_count);
    cJSON_Delete(frame); return false;
}
bool cdm_source_age(const cdm_state *s,const cJSON *record,uint64_t now,uint64_t *age_s)
{
    if (!s->has_anchor || now<s->anchor_mono_ms || !record || !age_s) return false;
    const cJSON *v=cJSON_GetObjectItemCaseSensitive(record,"observed_at");
    if (!v) v=cJSON_GetObjectItemCaseSensitive(record,"captured_at");
    int64_t source; if (!timestamp(v,false,&source)) return false;
    int64_t current=s->anchor_utc_us+(int64_t)(now-s->anchor_mono_ms)*1000;
    if (current<source) return false;
    *age_s=(uint64_t)((current-source)/1000000); return true;
}
bool cdm_receive_age(const cdm_state *s,uint64_t now,uint64_t *age_s)
{ if (!s->has_frame || now<s->received_ms || !age_s) return false; *age_s=(now-s->received_ms)/1000; return true; }
bool cdm_stale(const cdm_state *s,const cJSON *record,uint64_t now)
{ uint64_t age; return record && (cJSON_IsTrue(cJSON_GetObjectItemCaseSensitive(record,"stale")) ||
    cdm_source_age(s,record,now,&age) && age>=300); }
