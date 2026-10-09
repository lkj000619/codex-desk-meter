#include "legacy.h"
#include "cdm.h"
#include <stdio.h>
#include <string.h>

static const cJSON *field(const cJSON *obj,const char *name)
{ return cJSON_GetObjectItemCaseSensitive(obj,name); }
static bool text(const cJSON *v) { return cJSON_IsString(v) && v->valuestring[0]; }
static bool percent(const cJSON *v)
{ return !v || cJSON_IsNull(v) || cJSON_IsNumber(v) && v->valuedouble>=0 && v->valuedouble<=100; }
static bool date(const cJSON *v,int64_t *out)
{ return text(v) && cdm_parse_time(v->valuestring,out); }
static bool valid_body(const cJSON *body,const char *source,int64_t now)
{
    if (!cJSON_IsObject(body) || !text(field(body,"source")) || strcmp(field(body,"source")->valuestring,source) ||
        !cJSON_IsNumber(field(body,"schema_version")) || field(body,"schema_version")->valuedouble!=1) return false;
    int64_t captured;
    if (!date(field(body,"captured_at"),&captured) || captured>now) return false;
    if (!strcmp(source,"fixture")) {
        const cJSON *windows=field(body,"windows"); if (!cJSON_IsArray(windows)) return false;
        for(const cJSON *w=windows->child;w;w=w->next) {
            if (!cJSON_IsObject(w) || !text(field(w,"id")) || !text(field(w,"label")) ||
                !percent(field(w,"percent_used")) || !percent(field(w,"percent_remaining"))) return false;
            const cJSON *reset=field(w,"resets_at"); int64_t ignored;
            if (reset && !cJSON_IsNull(reset) && !date(reset,&ignored)) return false;
        }
    } else {
        if (!percent(field(body,"forecast_24h_percent")) || !percent(field(body,"forecast_48h_percent"))) return false;
        const cJSON *reset=field(body,"last_reset_at"); if (!reset) reset=field(body,"latest_reset_at");
        int64_t ignored; if (reset && !cJSON_IsNull(reset) && !date(reset,&ignored)) return false;
    }
    return true;
}
static void copy(cJSON *target,const char *dst,const cJSON *source,const char *src)
{
    const cJSON *value=field(source,src);
    cJSON_AddItemToObject(target,dst,value?cJSON_Duplicate(value,1):cJSON_CreateNull());
}
cJSON *cdm_legacy_run(const cJSON *request)
{
    const cJSON *src=field(request,"source"), *events=field(request,"events");
    if (!text(src) || !cJSON_IsArray(events)) return NULL;
    const char *source=src->valuestring;
    cJSON *result=cJSON_CreateArray(), *good=NULL;
    if (!result) return NULL;
    for(const cJSON *event=events->child;event;event=event->next) {
        const cJSON *now_value=field(event,"now"), *error=field(event,"error"), *body=field(event,"body");
        int64_t now=0; bool clock_valid=date(now_value,&now);
        cJSON *parsed=NULL;
        if (cJSON_IsString(body)) parsed=cJSON_Parse(body->valuestring);
        else if (cJSON_IsObject(body)) parsed=cJSON_Duplicate(body,1);
        const cJSON *candidate=parsed;
        bool ok=clock_valid && cJSON_IsNull(error) && valid_body(candidate,source,now);
        if (ok) { cJSON_Delete(good); good=cJSON_Duplicate(candidate,1); }
        cJSON *out=cJSON_CreateObject();
        if (!out) { cJSON_Delete(parsed); cJSON_Delete(good); cJSON_Delete(result); return NULL; }
        int64_t observed=0; bool has_observed=good && date(field(good,"captured_at"),&observed);
        bool stale=clock_valid && has_observed && now-observed>=300000000;
        if (!strcmp(source,"fixture")) {
            cJSON_AddStringToObject(out,"source",source);
            copy(out,"windows",good,"windows");
            copy(out,"observed_at",good,"captured_at");
        } else {
            cJSON_AddStringToObject(out,"provider",source);
            copy(out,"fetched_at",good,"captured_at");
            if (good && field(good,"last_reset_at")) copy(out,"latest_reset_at",good,"last_reset_at");
            else copy(out,"latest_reset_at",good,"latest_reset_at");
            copy(out,"forecast_24h_percent",good,"forecast_24h_percent");
            copy(out,"forecast_48h_percent",good,"forecast_48h_percent");
            cJSON_AddFalseToObject(out,"forecast_is_schedule");
        }
        cJSON_AddBoolToObject(out,"stale",stale);
        if (ok) cJSON_AddNullToObject(out,"error_code");
        else if (text(error)) {
            char code[64]; size_t n=strlen(error->valuestring); if (n>=sizeof code) n=sizeof code-1;
            for(size_t i=0;i<n;i++) { char c=error->valuestring[i]; code[i]=c>='a'&&c<='z'?c-32:c; }
            code[n]=0; cJSON_AddStringToObject(out,"error_code",code);
        } else cJSON_AddStringToObject(out,"error_code","SOURCE_INVALID");
        cJSON_AddItemToArray(result,out);
        cJSON_Delete(parsed);
    }
    cJSON_Delete(good);
    return result;
}
