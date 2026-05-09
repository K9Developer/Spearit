import Box from "@/components/Box";
import Button from "@/components/Button";
import Input from "@/components/Input";
import Modal from "@/components/Modal";
import { useUser } from "@/context/useUser";
import APIManager, { type UserManagementMetadata } from "@/utils/api_manager";
import { hasPermission } from "@/utils/permissions";
import type { Rule, RuleCondition, RuleConditionKey, RuleConditionOperator, RuleEventType } from "@/utils/types";
import { GripVertical, Plus, RefreshCw, Shield, Trash2 } from "lucide-react";
import React from "react";
import toast from "react-hot-toast";
import SectionCard from "./overview/SectionCard";
import IdMultiSelect from "./users/IdMultiSelect";

const CONDITION_KEYS: RuleConditionKey[] = [
    "packet.length",
    "packet.src_ip",
    "packet.dst_ip",
    "packet.src_port",
    "packet.dst_port",
    "packet.protocol",
    "packet.is_connection_establishing",
];

const CONDITION_KEY_LABEL: Record<RuleConditionKey, string> = {
    "packet.length": "Packet length",
    "packet.src_ip": "Source IP address",
    "packet.dst_ip": "Destination IP address",
    "packet.src_port": "Source port",
    "packet.dst_port": "Destination port",
    "packet.protocol": "Protocol",
    "packet.is_connection_establishing": "Is connection establishing",
};

const OPERATORS: RuleConditionOperator[] = [
    "equals",
    "not_equals",
    "lower_than",
    "greater_than",
    "lower_than_or_equal",
    "greater_than_or_equal",
    "contains",
];

const EVENT_TYPES: RuleEventType[] = ["network.send_packet", "network.receive_packet", "network.receive_connection", "network.create_connection"];

const EVENT_TYPE_LABEL: Record<RuleEventType, string> = {
    "network.send_packet": "Send packet",
    "network.receive_packet": "Receive packet",
    "network.receive_connection": "Receive connection",
    "network.create_connection": "Create connection",
};

type ResponseMode = "alert" | "block_alert";

const responseModeFromResponses = (responses: string[] | null | undefined): ResponseMode => {
    const r = responses ?? [];
    return r.includes("kill") ? "block_alert" : "alert";
};

const responsesFromMode = (mode: ResponseMode): string[] => {
    if (mode === "block_alert") return ["kill", "alert"];
    return ["alert"];
};

const moveItem = <T,>(arr: T[], from: number, to: number): T[] => {
    if (from === to) return arr;
    const next = [...arr];
    const [item] = next.splice(from, 1);
    next.splice(to, 0, item);
    return next;
};

const bytesFromBase64 = (value: string): Uint8Array | null => {
    try {
        const bin = atob(value);
        const bytes = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
        return bytes;
    } catch {
        return null;
    }
};

const base64FromBytes = (bytes: Uint8Array) => {
    let binary = "";
    for (const b of bytes) binary += String.fromCharCode(b);
    return btoa(binary);
};

const isMostlyPrintable = (s: string) => {
    if (!s) return true;
    let ok = 0;
    for (const ch of s) {
        const code = ch.charCodeAt(0);
        if (code === 9 || code === 10 || code === 13) ok++;
        else if (code >= 32 && code <= 126) ok++;
    }
    return ok / s.length > 0.9;
};

const decodeLittleEndianUnsignedInt = (bytes: Uint8Array): number | null => {
    if (bytes.length === 0 || bytes.length > 8) return null;
    let v = 0n;
    for (let i = 0; i < bytes.length; i++) {
        v |= BigInt(bytes[i]!) << BigInt(8 * i);
    }
    if (v > BigInt(Number.MAX_SAFE_INTEGER)) return null;
    return Number(v);
};

const encodeLittleEndianUnsignedInt = (n: number): Uint8Array => {
    const value = Math.trunc(n);
    if (value < 0) return new Uint8Array([0]);
    if (value <= 0xff) return new Uint8Array([value]);
    if (value <= 0xffff) return new Uint8Array([value & 0xff, (value >> 8) & 0xff]);
    return new Uint8Array([value & 0xff, (value >> 8) & 0xff, (value >> 16) & 0xff, (value >> 24) & 0xff]);
};

type LiteralValueKind = "bool" | "int" | "text";

const literalKindForKey = (key: RuleConditionKey): LiteralValueKind => {
    if (key === "packet.is_connection_establishing") return "bool";
    if (key === "packet.length" || key === "packet.src_port" || key === "packet.dst_port") return "int";
    return "text";
};

const decodeLiteralForKey = (key: RuleConditionKey, base64Value: string): string => {
    const bytes = bytesFromBase64(base64Value);
    if (!bytes) return base64Value;

    const kind = literalKindForKey(key);
    if (kind === "bool") {
        if (bytes.length === 1 && (bytes[0] === 0 || bytes[0] === 1)) return bytes[0] === 1 ? "true" : "false";
        const utf = new TextDecoder().decode(bytes).trim().toLowerCase();
        if (utf === "1" || utf === "true") return "true";
        if (utf === "0" || utf === "false") return "false";
        return "false";
    }

    if (kind === "int") {
        const v = decodeLittleEndianUnsignedInt(bytes);
        if (v !== null) return String(v);
        const utf = new TextDecoder().decode(bytes).trim();
        if (/^\d+$/.test(utf)) return utf;
        return "0";
    }

    const utf = new TextDecoder().decode(bytes);
    if (isMostlyPrintable(utf)) return utf;
    return base64Value;
};

const encodeLiteralForKey = (key: RuleConditionKey, uiValue: string): string => {
    const kind = literalKindForKey(key);
    if (kind === "bool") {
        const normalized = uiValue.trim().toLowerCase();
        const b = normalized === "true" || normalized === "1";
        return base64FromBytes(new Uint8Array([b ? 1 : 0]));
    }
    if (kind === "int") {
        const n = Number(uiValue);
        const safe = Number.isFinite(n) ? Math.max(0, Math.trunc(n)) : 0;
        return base64FromBytes(encodeLittleEndianUnsignedInt(safe));
    }
    return base64FromBytes(new TextEncoder().encode(uiValue ?? ""));
};

const normalizeRuleForEdit = (rule: Rule) => {
    const conditions: RuleCondition[] = (rule.conditions ?? []).map((c) => {
        const valIsKey = Boolean((c as any)?.value?.is_key);
        const raw = String((c as any)?.value?.value ?? "");
        const key = (c as any)?.key?.value as RuleConditionKey;
        const decoded = !valIsKey ? decodeLiteralForKey(key, raw) : null;
        return {
            key: { is_key: true, value: key },
            operator: (c as any)?.operator as RuleConditionOperator,
            value: {
                is_key: valIsKey,
                value: valIsKey ? raw : (decoded ?? raw),
            },
        };
    });

    return {
        ...rule,
        active_for_groups: rule.active_for_groups ?? [],
        handlers: rule.handlers ?? [],
        description: rule.description ?? "",
        conditions,
    };
};

export default function Rules() {
    const { user } = useUser();
    const canControlRules = user ? hasPermission(user.permissions, "control_rules") : false;

    const [rules, setRules] = React.useState<Rule[]>([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState<string | null>(null);

    const [metadata, setMetadata] = React.useState<UserManagementMetadata | null>(null);

    const [editOpen, setEditOpen] = React.useState(false);
    const [editing, setEditing] = React.useState<Rule | null>(null);
    const [isCreate, setIsCreate] = React.useState(false);

    const [formName, setFormName] = React.useState("");
    const [formDescription, setFormDescription] = React.useState("");
    const [formIsActive, setFormIsActive] = React.useState(true);
    const [formEventTypes, setFormEventTypes] = React.useState<RuleEventType[]>([]);
    const [formResponseMode, setFormResponseMode] = React.useState<ResponseMode>("alert");
    const [formActiveForGroups, setFormActiveForGroups] = React.useState<number[]>([]);
    const [formConditions, setFormConditions] = React.useState<RuleCondition[]>([]);

    const [dragIndex, setDragIndex] = React.useState<number | null>(null);
    const [savingOrder, setSavingOrder] = React.useState(false);

    const load = React.useCallback(async () => {
        setLoading(true);
        setError(null);

        const [rulesRes, metaRes] = await Promise.all([APIManager.listRules(), APIManager.getUserManagementMetadata()]);

        if (metaRes.success && metaRes.data) setMetadata(metaRes.data);
        else setMetadata({ permission_types: {}, group_ids: {}, device_ids: {} });

        if (rulesRes.success && rulesRes.data) {
            const sorted = [...(rulesRes.data.rules ?? [])].sort((a, b) => (a.rule_order ?? 0) - (b.rule_order ?? 0));
            setRules(sorted);
        } else {
            setRules([]);
            setError(rulesRes.message || "Failed to load rules");
        }

        setLoading(false);
    }, []);

    React.useEffect(() => {
        load();
    }, [load]);

    const resetFormForCreate = () => {
        setFormName("");
        setFormDescription("");
        setFormIsActive(true);
        setFormEventTypes([]);
        setFormResponseMode("alert");
        setFormActiveForGroups([]);
        setFormConditions([
            {
                key: { is_key: true, value: "packet.src_ip" },
                operator: "equals",
                value: { is_key: false, value: "" },
            },
        ]);
    };

    const openCreate = () => {
        resetFormForCreate();
        setIsCreate(true);
        setEditing(null);
        setEditOpen(true);
    };

    const openEdit = (rule: Rule) => {
        const normalized = normalizeRuleForEdit(rule);
        setEditing(normalized);
        setIsCreate(false);

        setFormName(normalized.rule_name ?? "");
        setFormDescription(String(normalized.description ?? ""));
        setFormIsActive(Boolean(normalized.is_active));
        setFormEventTypes((normalized.event_types ?? []) as RuleEventType[]);
        setFormResponseMode(responseModeFromResponses(normalized.responses));
        setFormActiveForGroups((normalized.active_for_groups ?? []) as number[]);
        setFormConditions(normalized.conditions ?? []);

        setEditOpen(true);
    };

    const toApiConditions = (conds: RuleCondition[]) => {
        return conds.map((c) => {
            const value = c.value.is_key
                ? { is_key: true, value: c.value.value }
                : { is_key: false, value: encodeLiteralForKey(c.key.value, c.value.value ?? "") };
            return {
                key: { is_key: true, value: c.key.value },
                operator: c.operator,
                value,
            };
        });
    };

    const onSave = async () => {
        if (!canControlRules) {
            toast.error("You do not have permission to edit rules");
            return;
        }

        const name = formName.trim();
        if (!name) {
            toast.error("Rule name is required");
            return;
        }

        if (formEventTypes.length === 0) {
            toast.error("Select at least one event type");
            return;
        }

        if (formConditions.length === 0) {
            toast.error("Add at least one condition");
            return;
        }

        const payload = {
            rule_name: name,
            event_types: formEventTypes,
            conditions: toApiConditions(formConditions),
            responses: responsesFromMode(formResponseMode),
            active_for_groups: formActiveForGroups,
            is_active: formIsActive,
            priority: 0,
            handlers: [],
            description: formDescription,
        };

        const res = isCreate
            ? await APIManager.createRule({
                  ...payload,
                  rule_order: rules.length,
              })
            : editing
              ? await APIManager.updateRule(editing.rule_id, payload)
              : null;

        if (!res) return;

        if (res.success) {
            toast.success(isCreate ? "Rule created" : "Rule updated");
            setEditOpen(false);
            await load();
        } else {
            toast.error(res.message || "Failed to save rule");
        }
    };

    const onDelete = async () => {
        if (!canControlRules || !editing) return;
        const ok = window.confirm(`Delete rule '${editing.rule_name}'? This cannot be undone.`);
        if (!ok) return;
        const res = await APIManager.deleteRule(editing.rule_id);
        if (res.success) {
            toast.success("Rule deleted");
            setEditOpen(false);
            await load();
        } else {
            toast.error(res.message || "Failed to delete rule");
        }
    };

    const onDropReorder = async () => {
        if (!canControlRules) return;
        setDragIndex(null);

        setSavingOrder(true);
        const ids = rules.map((r) => r.rule_id);
        const res = await APIManager.reorderRules(ids);
        setSavingOrder(false);

        if (res.success) {
            toast.success("Rule order updated");
            // update local order numbers immediately
            setRules((prev) => prev.map((r, idx) => ({ ...r, rule_order: idx })));
        } else {
            toast.error(res.message || "Failed to update order");
            await load();
        }
    };

    const toggleEventType = (t: RuleEventType) => {
        setFormEventTypes((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]));
    };

    const summarizeEventTypes = (types: RuleEventType[]) => {
        const labels = types.map((t) => EVENT_TYPE_LABEL[t]);
        if (labels.length <= 2) return labels.join(", ") || "—";
        return `${labels.slice(0, 2).join(", ")} +${labels.length - 2}`;
    };

    const updateCondition = (idx: number, next: RuleCondition) => {
        setFormConditions((prev) => prev.map((c, i) => (i === idx ? next : c)));
    };

    const addCondition = () => {
        setFormConditions((prev) => [
            ...prev,
            {
                key: { is_key: true, value: "packet.src_ip" },
                operator: "equals",
                value: { is_key: false, value: "" },
            },
        ]);
    };

    const removeCondition = (idx: number) => {
        setFormConditions((prev) => prev.filter((_, i) => i !== idx));
    };

    return (
        <div className="h-full min-h-0 overflow-y-auto">
            <div className="px-6 py-6">
                <div className="flex items-start justify-between gap-6">
                    <div className="min-w-0">
                        <p className="text-xs uppercase tracking-wide text-text-gray">Security</p>
                        <h1 className="mt-1 text-2xl font-semibold text-text-primary">Rules</h1>
                        <p className="mt-2 text-sm text-text-secondary">
                            Manage packet rules. Conditions are evaluated with AND (every condition must pass).
                        </p>
                    </div>

                    <div className="shrink-0 flex items-center gap-3">
                        <Button
                            title={loading ? "Refreshing" : "Refresh"}
                            onClick={load}
                            loading={loading}
                            icon={!loading ? <RefreshCw size={18} /> : undefined}
                            className="rounded-xl"
                        />
                        <Button
                            title="Create Rule"
                            onClick={openCreate}
                            icon={<Plus size={18} />}
                            className="rounded-xl"
                            disabled={!canControlRules}
                            hint={!canControlRules ? "Requires control_rules" : undefined}
                        />
                    </div>
                </div>

                <div className="mt-6">
                    {!user && (
                        <Box.Secondary className="p-6!">
                            <p className="text-sm text-text-secondary">You are not logged in.</p>
                        </Box.Secondary>
                    )}

                    {user && !canControlRules && (
                        <Box.Secondary className="p-6!">
                            <div className="flex items-center gap-3">
                                <span className="text-highlight">
                                    <Shield size={20} />
                                </span>
                                <p className="text-sm text-text-secondary">You can view rules, but you don’t have permission to edit them.</p>
                            </div>
                        </Box.Secondary>
                    )}

                    {loading && (
                        <Box.Secondary className="p-6!">
                            <p className="text-sm text-text-secondary">Loading rules…</p>
                        </Box.Secondary>
                    )}

                    {!loading && error && (
                        <Box.Secondary className="p-6!">
                            <p className="text-sm text-text-secondary">{error}</p>
                        </Box.Secondary>
                    )}
                </div>

                {!loading && !error && (
                    <div className="mt-6 grid grid-cols-1 gap-6">
                        <SectionCard title="All Rules">
                            {rules.length === 0 ? (
                                <p className="text-sm text-text-gray">No rules</p>
                            ) : (
                                <div className="w-full overflow-x-auto">
                                    <table className="w-full text-left border-separate border-spacing-0">
                                        <thead>
                                            <tr>
                                                <th className="text-xs uppercase tracking-wide text-text-gray pb-3 w-10" />
                                                <th className="text-xs uppercase tracking-wide text-text-gray pb-3 w-16">Order</th>
                                                <th className="text-xs uppercase tracking-wide text-text-gray pb-3">Rule</th>
                                                <th className="text-xs uppercase tracking-wide text-text-gray pb-3 w-28">Status</th>
                                                <th className="text-xs uppercase tracking-wide text-text-gray pb-3 w-52">Events</th>
                                                <th className="text-xs uppercase tracking-wide text-text-gray pb-3 w-28">Conditions</th>
                                                <th className="text-xs uppercase tracking-wide text-text-gray pb-3 w-32">Response</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {rules.map((r, idx) => {
                                                const respMode = responseModeFromResponses(r.responses);
                                                return (
                                                    <tr
                                                        key={r.rule_id}
                                                        className={`border-t border-secondary/60 ${canControlRules ? "cursor-grab" : "cursor-pointer"} hover:bg-background/20`.trim()}
                                                        draggable={canControlRules}
                                                        onDragStart={() => setDragIndex(idx)}
                                                        onDragOver={(e) => {
                                                            if (!canControlRules) return;
                                                            e.preventDefault();
                                                            if (dragIndex === null) return;
                                                            if (dragIndex === idx) return;
                                                            setRules((prev) => moveItem(prev, dragIndex, idx));
                                                            setDragIndex(idx);
                                                        }}
                                                        onDragEnd={() => {
                                                            if (!canControlRules) return;
                                                            void onDropReorder();
                                                        }}
                                                        onClick={() => openEdit(r)}
                                                    >
                                                        <td className="py-3 text-sm text-text-primary align-middle w-10">
                                                            <span className="text-text-gray">
                                                                <GripVertical size={16} />
                                                            </span>
                                                        </td>
                                                        <td className="py-3 text-sm text-text-secondary align-middle w-16">{r.rule_order}</td>
                                                        <td className="py-3 text-sm text-text-primary align-middle">
                                                            <div className="min-w-0">
                                                                <p className="text-text-primary truncate">{r.rule_name}</p>
                                                                <p className="mt-1 text-xs text-text-gray truncate">ID {r.rule_id}</p>
                                                            </div>
                                                        </td>
                                                        <td className="py-3 text-sm text-text-primary align-middle w-28">
                                                            <span
                                                                className={`inline-flex items-center rounded-md px-2 py-1 text-xs uppercase tracking-wide ${
                                                                    r.is_active
                                                                        ? "bg-highlight/15 text-highlight"
                                                                        : "bg-background/40 text-text-secondary"
                                                                }`}
                                                            >
                                                                {r.is_active ? "Active" : "Inactive"}
                                                            </span>
                                                        </td>
                                                        <td className="py-3 text-sm text-text-secondary align-middle w-52">
                                                            {summarizeEventTypes((r.event_types ?? []) as RuleEventType[])}
                                                        </td>
                                                        <td className="py-3 text-sm text-text-secondary align-middle w-28">
                                                            {(r.conditions ?? []).length}
                                                        </td>
                                                        <td className="py-3 text-sm text-text-secondary align-middle w-32">
                                                            {respMode === "block_alert" ? "Block + alert" : "Alert"}
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>

                                    {savingOrder && <p className="mt-3 text-xs text-text-gray">Saving rule order…</p>}
                                    {!canControlRules && (
                                        <p className="mt-3 text-xs text-text-gray">Drag-reordering is available with control_rules.</p>
                                    )}
                                </div>
                            )}
                        </SectionCard>
                    </div>
                )}
            </div>

            <Modal
                isOpen={editOpen}
                onClose={() => {
                    setEditOpen(false);
                    setEditing(null);
                    setIsCreate(false);
                }}
                title={isCreate ? "Create Rule" : editing ? `Rule: ${editing.rule_name}` : "Rule"}
                maxWidthClass="max-w-3xl"
            >
                <div className="grid grid-cols-1 gap-4">
                    {!canControlRules && (
                        <Box.Secondary className="p-4!">
                            <p className="text-sm text-text-secondary">Read-only: editing requires the control_rules permission.</p>
                        </Box.Secondary>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
                        <Input title="Rule Name" value={formName} onChange={setFormName} disabled={!canControlRules} />
                        <div>
                            <p className="text-xs uppercase tracking-wide text-text-gray">Response</p>
                            <select
                                className={`mt-2 w-full bg-foreground outline outline-secondary rounded-md px-3 py-2 text-sm text-text-primary transition ${
                                    !canControlRules ? "opacity-70 cursor-not-allowed" : "hover:brightness-90"
                                }`}
                                disabled={!canControlRules}
                                value={formResponseMode}
                                onChange={(e) => setFormResponseMode(e.target.value as ResponseMode)}
                            >
                                <option value="alert">Alert</option>
                                <option value="block_alert">Block + alert</option>
                            </select>
                        </div>
                    </div>

                    <Input
                        title="Description"
                        value={formDescription}
                        onChange={setFormDescription}
                        disabled={!canControlRules}
                        placeholder="Optional"
                    />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
                        <div className="w-full">
                            <p className="text-xs uppercase tracking-wide text-text-gray">Enabled</p>
                            <button
                                type="button"
                                disabled={!canControlRules}
                                onClick={() => setFormIsActive((v) => !v)}
                                className={`mt-2 w-full bg-foreground outline outline-secondary rounded-md px-3 py-2 text-sm flex items-center justify-between gap-3 transition ${
                                    !canControlRules ? "opacity-70 cursor-not-allowed" : "hover:brightness-90"
                                }`}
                            >
                                <span className="text-text-primary">{formIsActive ? "Active" : "Inactive"}</span>
                                <span className="text-xs text-text-gray">Toggle</span>
                            </button>
                        </div>

                        <IdMultiSelect
                            title="Active For Groups"
                            items={metadata?.group_ids ?? {}}
                            selected={formActiveForGroups}
                            onChange={setFormActiveForGroups}
                            emptyText="No groups available"
                            disabled={!canControlRules}
                        />
                    </div>

                    <div>
                        <p className="text-xs uppercase tracking-wide text-text-gray">Event Types</p>
                        <p className="mt-1 text-xs text-text-gray">Rules are evaluated when these events occur.</p>
                        <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {EVENT_TYPES.map((t) => {
                                const selected = formEventTypes.includes(t);
                                return (
                                    <button
                                        key={t}
                                        type="button"
                                        disabled={!canControlRules}
                                        onClick={() => toggleEventType(t)}
                                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-md transition text-left outline outline-secondary bg-foreground ${
                                            selected ? "outline-highlight bg-background/40" : ""
                                        } ${!canControlRules ? "opacity-70 cursor-not-allowed" : "hover:brightness-90"}`}
                                    >
                                        <span
                                            className={`h-4 w-4 rounded-sm outline outline-secondary flex items-center justify-center shrink-0 ${
                                                selected ? "bg-highlight/20 outline-highlight" : "bg-background/40"
                                            }`}
                                        >
                                            {selected && <span className="text-highlight text-xs">✓</span>}
                                        </span>
                                        <span className="text-sm text-text-secondary truncate">{EVENT_TYPE_LABEL[t]}</span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    <div>
                        <p className="text-xs uppercase tracking-wide text-text-gray">Conditions</p>
                        <p className="mt-1 text-xs text-text-gray">All conditions are combined with AND (every condition must pass).</p>

                        <div className="mt-3 grid grid-cols-1 gap-3">
                            {formConditions.map((c, idx) => (
                                <Box.Secondary key={idx} className="p-4!">
                                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
                                        <div>
                                            <p className="text-xs uppercase tracking-wide text-text-gray">Field</p>
                                            <select
                                                className="mt-2 w-full bg-foreground outline outline-secondary rounded-md px-3 py-2 text-sm text-text-primary"
                                                disabled={!canControlRules}
                                                value={c.key.value}
                                                onChange={(e) =>
                                                    updateCondition(idx, {
                                                        ...c,
                                                        key: { is_key: true, value: e.target.value as RuleConditionKey },
                                                        value: c.value.is_key
                                                            ? c.value
                                                            : {
                                                                  is_key: false,
                                                                  value:
                                                                      literalKindForKey(e.target.value as RuleConditionKey) === "bool" ? "false" : "",
                                                              },
                                                    })
                                                }
                                            >
                                                {CONDITION_KEYS.map((k) => (
                                                    <option key={k} value={k}>
                                                        {CONDITION_KEY_LABEL[k]}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>

                                        <div>
                                            <p className="text-xs uppercase tracking-wide text-text-gray">Operator</p>
                                            <select
                                                className="mt-2 w-full bg-foreground outline outline-secondary rounded-md px-3 py-2 text-sm text-text-primary"
                                                disabled={!canControlRules}
                                                value={c.operator}
                                                onChange={(e) => updateCondition(idx, { ...c, operator: e.target.value as RuleConditionOperator })}
                                            >
                                                {OPERATORS.map((op) => (
                                                    <option key={op} value={op}>
                                                        {op}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>

                                        <div>
                                            <p className="text-xs uppercase tracking-wide text-text-gray">Value Type</p>
                                            <select
                                                className="mt-2 w-full bg-foreground outline outline-secondary rounded-md px-3 py-2 text-sm text-text-primary"
                                                disabled={!canControlRules}
                                                value={c.value.is_key ? "key" : "literal"}
                                                onChange={(e) => {
                                                    const nextIsKey = e.target.value === "key";
                                                    updateCondition(idx, {
                                                        ...c,
                                                        value: {
                                                            is_key: nextIsKey,
                                                            value: nextIsKey
                                                                ? "packet.src_ip"
                                                                : literalKindForKey(c.key.value) === "bool"
                                                                  ? "false"
                                                                  : "",
                                                        },
                                                    });
                                                }}
                                            >
                                                <option value="literal">Custom value</option>
                                                <option value="key">Another field</option>
                                            </select>
                                        </div>

                                        <div>
                                            {c.value.is_key ? (
                                                <>
                                                    <p className="text-xs uppercase tracking-wide text-text-gray">Compare With Field</p>
                                                    <select
                                                        className="mt-2 w-full bg-foreground outline outline-secondary rounded-md px-3 py-2 text-sm text-text-primary"
                                                        disabled={!canControlRules}
                                                        value={c.value.value}
                                                        onChange={(e) =>
                                                            updateCondition(idx, { ...c, value: { is_key: true, value: e.target.value as string } })
                                                        }
                                                    >
                                                        {CONDITION_KEYS.map((k) => (
                                                            <option key={k} value={k}>
                                                                {CONDITION_KEY_LABEL[k]}
                                                            </option>
                                                        ))}
                                                    </select>
                                                </>
                                            ) : (
                                                <>
                                                    {literalKindForKey(c.key.value) === "bool" ? (
                                                        <div>
                                                            <p className="text-xs uppercase tracking-wide text-text-gray">Value</p>
                                                            <select
                                                                className={`mt-2 w-full bg-foreground outline outline-secondary rounded-md px-3 py-2 text-sm text-text-primary transition ${
                                                                    !canControlRules ? "opacity-70 cursor-not-allowed" : "hover:brightness-90"
                                                                }`}
                                                                disabled={!canControlRules}
                                                                value={c.value.value === "true" ? "true" : "false"}
                                                                onChange={(e) =>
                                                                    updateCondition(idx, { ...c, value: { is_key: false, value: e.target.value } })
                                                                }
                                                            >
                                                                <option value="false">false</option>
                                                                <option value="true">true</option>
                                                            </select>
                                                        </div>
                                                    ) : (
                                                        <Input
                                                            title="Value"
                                                            type={literalKindForKey(c.key.value) === "int" ? "number" : "text"}
                                                            value={c.value.value}
                                                            onChange={(v) => updateCondition(idx, { ...c, value: { is_key: false, value: v } })}
                                                            disabled={!canControlRules}
                                                            placeholder={
                                                                literalKindForKey(c.key.value) === "int"
                                                                    ? "Number (stored as base64)"
                                                                    : "Text (stored as base64)"
                                                            }
                                                        />
                                                    )}
                                                </>
                                            )}
                                        </div>
                                    </div>

                                    {canControlRules && (
                                        <div className="mt-3 flex items-center justify-end">
                                            <Button
                                                title="Remove"
                                                onClick={() => removeCondition(idx)}
                                                icon={<Trash2 size={18} />}
                                                className="rounded-xl"
                                            />
                                        </div>
                                    )}
                                </Box.Secondary>
                            ))}

                            {canControlRules && (
                                <div className="flex items-center justify-between">
                                    <Button title="Add Condition" onClick={addCondition} icon={<Plus size={18} />} className="rounded-xl" />
                                    <p className="text-xs text-text-gray">Every condition must pass to trigger the rule.</p>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="pt-2 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                            {canControlRules && !isCreate && editing && (
                                <Button title="Delete" onClick={onDelete} icon={<Trash2 size={18} />} className="rounded-xl" />
                            )}
                        </div>

                        <div className="flex items-center gap-3">
                            <Button title="Close" onClick={() => setEditOpen(false)} className="rounded-xl" />
                            {canControlRules && <Button title="Save" onClick={onSave} className="rounded-xl" />}
                        </div>
                    </div>
                </div>
            </Modal>
        </div>
    );
}
