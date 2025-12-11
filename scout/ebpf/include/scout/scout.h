#pragma once

#include "rule.h"
#include "comms.h"
#include "report.h"

void _remove_rule(unsigned long long id);

void _create_rule(unsigned long long id);

/**
 * option 1 - ID already exists for us - mark as matched (0)
 * option 2 - ID does not exist for us - create new rule
 * option 3 - ID exists for us but not in active list - remove rule
 * 
 * returns true if rules were updated
 */
bool update_rules(void);
void destruct_scout(void);
void send_report(Report report);
CompiledRule* get_rules(void);
bool has_wrapper_initialized(void);
void show_ready_to_wrapper(void);