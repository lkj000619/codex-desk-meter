#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "cJSON.h"
#include "meter_model.h"
#include "meter_parser.h"

int main(void) {
    /* Read complete JSON object from stdin until EOF */
    size_t cap = 16384;
    size_t len = 0;
    char *buf = (char *)malloc(cap);
    if (!buf) {
        fprintf(stderr, "adapter: OOM allocating stdin buffer\n");
        return 1;
    }

    int c;
    while ((c = getchar()) != EOF) {
        if (len + 2 >= cap) {
            cap *= 2;
            char *nb = (char *)realloc(buf, cap);
            if (!nb) {
                fprintf(stderr, "adapter: OOM reallocating stdin buffer\n");
                free(buf);
                return 1;
            }
            buf = nb;
        }
        buf[len++] = (char)c;
    }
    buf[len] = '\0';

    if (len == 0) {
        fprintf(stderr, "adapter: empty stdin\n");
        free(buf);
        return 1;
    }

    cJSON *req = cJSON_Parse(buf);
    free(buf);
    if (!req) {
        fprintf(stderr, "adapter: invalid JSON on stdin\n");
        return 1;
    }

    cJSON *jsource = cJSON_GetObjectItem(req, "source");
    cJSON *jevents = cJSON_GetObjectItem(req, "events");
    if (!jsource || !cJSON_IsString(jsource) || !jevents || !cJSON_IsArray(jevents)) {
        fprintf(stderr, "adapter: missing source or events array\n");
        cJSON_Delete(req);
        return 1;
    }

    const char *source = jsource->valuestring;
    int num_events = cJSON_GetArraySize(jevents);

    cJSON *out_array = cJSON_CreateArray();

    if (strcmp(source, "fixture") == 0) {
        usage_snapshot_t snap;
        memset(&snap, 0, sizeof(snap));

        for (int i = 0; i < num_events; i++) {
            cJSON *evt = cJSON_GetArrayItem(jevents, i);
            cJSON *jnow = cJSON_GetObjectItem(evt, "now");
            cJSON *jbody = cJSON_GetObjectItem(evt, "body");
            cJSON *jerr = cJSON_GetObjectItem(evt, "error");

            const char *now_str = (jnow && cJSON_IsString(jnow)) ? jnow->valuestring : NULL;
            const char *err_str = (jerr && cJSON_IsString(jerr)) ? jerr->valuestring : NULL;

            char *body_str = NULL;
            if (jbody) {
                if (cJSON_IsObject(jbody)) {
                    body_str = cJSON_PrintUnformatted(jbody);
                } else if (cJSON_IsString(jbody)) {
                    body_str = strdup(jbody->valuestring);
                }
            }

            meter_parse_usage_json(body_str, now_str, err_str, &snap);

            if (body_str) free(body_str);

            cJSON *snap_json = meter_serialize_usage_to_cjson(&snap);
            cJSON_AddItemToArray(out_array, snap_json);
        }
    } else {
        global_reset_snapshot_t snap;
        memset(&snap, 0, sizeof(snap));

        for (int i = 0; i < num_events; i++) {
            cJSON *evt = cJSON_GetArrayItem(jevents, i);
            cJSON *jnow = cJSON_GetObjectItem(evt, "now");
            cJSON *jbody = cJSON_GetObjectItem(evt, "body");
            cJSON *jerr = cJSON_GetObjectItem(evt, "error");

            const char *now_str = (jnow && cJSON_IsString(jnow)) ? jnow->valuestring : NULL;
            const char *err_str = (jerr && cJSON_IsString(jerr)) ? jerr->valuestring : NULL;

            char *body_str = NULL;
            if (jbody) {
                if (cJSON_IsObject(jbody)) {
                    body_str = cJSON_PrintUnformatted(jbody);
                } else if (cJSON_IsString(jbody)) {
                    body_str = strdup(jbody->valuestring);
                }
            }

            meter_parse_global_reset_json(body_str, source, now_str, err_str, &snap);

            if (body_str) free(body_str);

            cJSON *snap_json = meter_serialize_global_reset_to_cjson(&snap);
            cJSON_AddItemToArray(out_array, snap_json);
        }
    }

    cJSON_Delete(req);

    char *out_str = cJSON_PrintUnformatted(out_array);
    cJSON_Delete(out_array);

    if (out_str) {
        printf("%s\n", out_str);
        free(out_str);
    }
    return 0;
}
