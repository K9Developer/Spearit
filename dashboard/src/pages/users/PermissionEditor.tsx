import React from "react";
import Button from "@/components/Button";
import type { Permission } from "@/utils/types";
import { Plus, Trash2 } from "lucide-react";
import IdMultiSelect from "./IdMultiSelect";

interface Props {
    permissionTypes: Record<string, string>;
    groupIds: Record<string, string>;
    deviceIds: Record<string, string>;
    canAssignType: (type: string) => boolean;
    lockedTypes: Set<string>;
    value: Permission[];
    onChange: (next: Permission[]) => void;
}

const emptyPermission = (permissionTypes: Record<string, string>, canAssignType: (type: string) => boolean, usedTypes: Set<string>): Permission => {
    const keys = Object.keys(permissionTypes);
    const firstAssignable = keys.find((k) => canAssignType(k) && !usedTypes.has(k));
    const type = firstAssignable ?? keys[0] ?? "control_users";
    return {
        type,
        affected_groups: [],
        affected_devices: [],
    };
};

export default function PermissionEditor({ permissionTypes, groupIds, deviceIds, canAssignType, lockedTypes, value, onChange }: Props) {
    const permissionTypeKeys = React.useMemo(() => Object.keys(permissionTypes), [permissionTypes]);

    const isTypeLocked = React.useCallback((perm: Permission) => lockedTypes.has(perm.type), [lockedTypes]);

    const usedTypes = React.useMemo(() => new Set(value.map((p) => p.type)), [value]);
    const hasDuplicates = React.useMemo(() => usedTypes.size !== value.length, [usedTypes, value.length]);

    const availableToAdd = React.useMemo(
        () => permissionTypeKeys.filter((t) => canAssignType(t) && !usedTypes.has(t)),
        [permissionTypeKeys, canAssignType, usedTypes],
    );

    const updateAt = (idx: number, next: Permission) => {
        if (!canAssignType(next.type)) return;
        if (isTypeLocked(value[idx])) return;
        if (value.some((p, i) => i !== idx && p.type === next.type)) return;
        onChange(value.map((p, i) => (i === idx ? next : p)));
    };

    const removeAt = (idx: number) => {
        if (isTypeLocked(value[idx])) return;
        onChange(value.filter((_, i) => i !== idx));
    };

    const add = () => {
        if (availableToAdd.length === 0) return;
        onChange([...value, emptyPermission(permissionTypes, canAssignType, usedTypes)]);
    };

    return (
        <div className="flex flex-col gap-4">
            {permissionTypeKeys.length > 0 && permissionTypeKeys.some((k) => !canAssignType(k)) && (
                <p className="text-xs text-text-secondary">
                    You can only grant permission types that you already have (unless you are <span className="text-text-primary">root</span>).
                </p>
            )}
            {hasDuplicates && <p className="text-xs text-text-secondary">Duplicate permission types are not allowed.</p>}
            {value.length === 0 && <p className="text-sm text-text-gray">No permissions assigned</p>}

            {value.map((perm, idx) => (
                <div key={idx} className="rounded-md outline outline-secondary bg-background/30 p-4">
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex flex-col gap-2">
                            <p className="text-xs uppercase tracking-wide text-text-gray">Permission Type</p>
                            <select
                                value={perm.type}
                                onChange={(e) => updateAt(idx, { ...perm, type: e.target.value })}
                                disabled={isTypeLocked(perm)}
                                className={`bg-foreground outline outline-secondary rounded-md px-3 py-2 text-sm text-text-primary ${
                                    isTypeLocked(perm) ? "opacity-70 cursor-not-allowed" : ""
                                }`}
                            >
                                {permissionTypeKeys.length === 0 ? (
                                    <option value={perm.type}>{perm.type}</option>
                                ) : (
                                    permissionTypeKeys.map((t) => (
                                        <option key={t} value={t} disabled={!canAssignType(t) || (t !== perm.type && usedTypes.has(t))}>
                                            {t}
                                        </option>
                                    ))
                                )}
                            </select>

                            {permissionTypes[perm.type] && <p className="text-xs text-text-secondary">{permissionTypes[perm.type]}</p>}
                        </div>

                        <Button
                            title="Remove"
                            onClick={() => removeAt(idx)}
                            icon={<Trash2 size={18} />}
                            className="rounded-xl"
                            disabled={isTypeLocked(perm)}
                        />
                    </div>

                    <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <IdMultiSelect
                            title="Affected Groups"
                            items={groupIds}
                            selected={perm.affected_groups}
                            onChange={(next) => updateAt(idx, { ...perm, affected_groups: next })}
                            emptyText="No groups available"
                        />
                        <IdMultiSelect
                            title="Affected Devices"
                            items={deviceIds}
                            selected={perm.affected_devices}
                            onChange={(next) => updateAt(idx, { ...perm, affected_devices: next })}
                            emptyText="No devices available"
                        />
                    </div>
                </div>
            ))}

            <div className="flex justify-start">
                <Button
                    title="Add Permission"
                    onClick={add}
                    icon={<Plus size={18} />}
                    className="rounded-xl"
                    disabled={availableToAdd.length === 0}
                />
            </div>
        </div>
    );
}
