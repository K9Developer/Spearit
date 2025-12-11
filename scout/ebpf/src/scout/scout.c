
#include "rule.h"
#include "comms.h"
#include "report.h"
#include "scout.h"
#include <string.h>

static CompiledRule RULES[MAX_RULES];

void _remove_rule(unsigned long long id) {
    int rule_index = -1;
    for (int i = 0; i < MAX_RULES; i++) {
        if (RULES[i].id == id) {
            rule_index = i;
            break;
        }
    }
    if (rule_index == -1) return;
    memset(&RULES[rule_index], 0, sizeof(CompiledRule));
}


void _create_rule(unsigned long long id) {
    RawCommsResponse response = shm_request(REQ_RULE_DATA, &id, sizeof(id));
    if (response.size == 0) {
        log_warn("Failed to create rule with ID %llu - no response data", id);
        return;
    }
    
    // failed to get response
    if (response.size != sizeof(CompiledRule)) {
        log_warn("Failed to create rule with ID %llu - response size %zu != expected %zu", 
                 id, response.size, sizeof(CompiledRule));
        return;
    }
    CompiledRule* cr = (CompiledRule*) response.data;
    if (cr->order >= MAX_RULES) return;
    memcpy(&RULES[cr->order], response.data, response.size);
}

/**
 * option 1 - ID already exists for us - mark as matched (0)
 * option 2 - ID does not exist for us - create new rule
 * option 3 - ID exists for us but not in active list - remove rule
 * 
 * returns true if rules were updated
 */
bool update_rules() {
    RawCommsResponse response = shm_request(REQ_ACTIVE_RULE_IDS, NULL, 0);
    if (!response.size) return false;
    unsigned long long* ids = (unsigned long long*)response.data;
    for (int ci = 0; ci < MAX_RULES; ci++) {
        if (RULES[ci].id == 0) continue;
        bool exists = false;
        for (int ai = 0; ai < response.size / sizeof(unsigned long long); ai++) {
            unsigned long long active_rule_id = ids[ai];
            if (active_rule_id == RULES[ci].id) {
                exists = true;
                ids[ai] = 0; // Mark this ID as matched
                log_debug("Rule with ID %llu already exists, marking as matched", RULES[ci].id);
                break;
            }
        }
        if (!exists) {
            _remove_rule(RULES[ci].id);
            log_debug("Removing rule with ID %llu", RULES[ci].id);
        }
    }

    for (int ai = 0; ai < response.size / sizeof(unsigned long long); ai++) {
        if (ids[ai] == 0) continue;
        log_debug("Creating new rule with ID %llu", ids[ai]);
        _create_rule(ids[ai]);
        
    }

    return true;
}

void send_report(Report report) {
    shm_send(RES_RULE_VIOLATION, &report, sizeof(report));
}

CompiledRule* get_rules()
{
    return RULES;
}

bool has_wrapper_initialized(void) {
    return _has_wrapper_initialized();
}

void show_ready_to_wrapper(void) {
    _show_ready_to_wrapper();
}

void destruct_scout(void) {
    destruct_comms();
}