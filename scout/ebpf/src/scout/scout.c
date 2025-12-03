
#include "rule.h"
#include "comms.h"
#include "report.h"
#include "scout.h"
#include <string.h>

static CompiledRule RULES[MAX_RULES];
static size_t rule_count = 0;

void _remove_rule(unsigned int id) {
    if (rule_count == 0) return;
    int rule_index = -1;
    for (int i = 0; i < rule_count; i++) {
        if (RULES[i].id == id) {
            rule_index = i;
            break;
        }
    }
    if (rule_index == -1) return;
    memcpy(&RULES[rule_index], &RULES[rule_count - 1], sizeof(CompiledRule));
    rule_count--;
}

void _create_rule(unsigned int id) {
    if (rule_count >= MAX_RULES) return;
    RawCommsResponse response = shm_request(REQ_RULE_DATA, &id, sizeof(id));
    if (response.size == 0) return; // failed to get response
    memcpy(&RULES[rule_count], response.data, response.size);
    rule_count++;
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
    unsigned int* ids = (unsigned int*)response.data;
    for (int ci = 0; ci < rule_count; ci++) {
        bool exists = false;
        for (int ai = 0; ai < response.size / sizeof(unsigned int); ai++) {
            unsigned int active_rule_id = ids[ai];
            if (active_rule_id == RULES[ci].id) {
                exists = true;
                ids[ai] = 0; // Mark this ID as matched
                break;
            }
        }
        if (!exists) _remove_rule(RULES[ci].id);
    }

    for (int ai = 0; ai < response.size / sizeof(unsigned int); ai++) {
        if (ids[ai] == 0) continue;
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


void wait_for_wrapper(void) {
    _wait_for_wrapper();
}

void destruct_scout(void) {
    destruct_comms();
}