
Detection options:
1. Rulesets - a set of rules for a program or network
2. Baseline - over a time window the server will record a baseline (since status message with info is sent every x time), once an agent surpasses that baseline do something
3. Signatures

Response options (Network):
1. Alert
2. Prevent
3. Air-gap (tell all agents to block connections from it as well as make the agent disconnect interface)

Response options (Software):
1. Alert
2. Quarantine
3. Kill
3. Air-gap (tell all agents to block connections from it as well as make the agent disconnect interface)

Data sources:
1. Network traffic - DPI (get packets, if HTTPS, try to decrypt using cert on pc, grab attached files (in the packet (MZ for example)), etc.)
2. System logs (event viewer, etc.) - for example how many login attempts made
3. Signatures of every running process, or modified file

The server will communicate with the agent, and every change in the ruleset will be sent to the agent. If a connection with an agent terminates, DO SOMETHING (kill input until reconnect?)

Dashboard features:
1. Alert list - sort by severity, id, time, etc.
2. Ruleset management - add/remove/edit rulesets
3. Agent management - see all agents, their status, etc.
4. Reports - generate reports based on alerts, agents, etc.
5. Baseline management - set time window, view baselines, etc.
6. Signature management - add/remove/edit signatures
7. Network map - visualize network topology and agent locations
8. Graphs showing attack types over time, number of alerts, etc.

The server will also detect certain events (maybe in succession) as a certain event type (info, brute_force, malware, etc.)

Important to detect a succession of events as campaigns

figure out way to make it not bypassable

Server - SpearHead
Client - Scout