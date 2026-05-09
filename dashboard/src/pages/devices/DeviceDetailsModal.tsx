import Button from "@/components/Button";
import Input from "@/components/Input";
import Modal from "@/components/Modal";
import APIManager from "@/utils/api_manager";
import { parseIdList, sameIds } from "@/utils/idLists";
import type { Campaign, Device, Event } from "@/utils/types";
import React from "react";
import { OrbitProgress } from "react-loading-indicators";
import toast from "react-hot-toast";
import IdMultiSelect from "../users/IdMultiSelect";
import SimpleTable from "../users/SimpleTable";

const formatTimestampNs = (timestampNs: number) => {
    const ms = Math.round(timestampNs / 1_000_000);
    const d = new Date(ms);
    if (Number.isNaN(d.getTime())) return String(timestampNs);
    return new Intl.DateTimeFormat(undefined, {
        year: "numeric",
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    }).format(d);
};

const formatIso = (iso: string) => {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return new Intl.DateTimeFormat(undefined, {
        year: "numeric",
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    }).format(d);
};

interface Props {
    isOpen: boolean;
    deviceId: number | null;
    onClose: () => void;

    canControlDevices: boolean;
    groupIds: Record<string, string>;
    handlerIdMap: Record<string, string>;

    onDeviceUpdated?: (device: Device) => void;
}

export default function DeviceDetailsModal({ isOpen, deviceId, onClose, canControlDevices, groupIds, handlerIdMap, onDeviceUpdated }: Props) {
    const [selectedDevice, setSelectedDevice] = React.useState<Device | null>(null);
    const [events, setEvents] = React.useState<Event[]>([]);
    const [campaigns, setCampaigns] = React.useState<Campaign[]>([]);
    const [loadingDetails, setLoadingDetails] = React.useState(false);
    const [errorDetails, setErrorDetails] = React.useState<string | null>(null);

    const [draftName, setDraftName] = React.useState<string>("");
    const [draftGroups, setDraftGroups] = React.useState<number[]>([]);
    const [draftHandlers, setDraftHandlers] = React.useState<number[]>([]);
    const [savingDevice, setSavingDevice] = React.useState(false);

    const loadDetails = React.useCallback(async (id: number) => {
        setLoadingDetails(true);
        setErrorDetails(null);
        const res = await APIManager.getDeviceDetails(id);
        if (res.success && res.data) {
            setSelectedDevice(res.data.device);
            setEvents(res.data.events);
            setCampaigns(res.data.campaigns);
        } else {
            setSelectedDevice(null);
            setEvents([]);
            setCampaigns([]);
            setErrorDetails(res.message || "Failed to load device details");
        }
        setLoadingDetails(false);
    }, []);

    React.useEffect(() => {
        if (!isOpen) return;
        if (deviceId === null) return;
        loadDetails(deviceId);
    }, [isOpen, deviceId, loadDetails]);

    React.useEffect(() => {
        if (!selectedDevice) return;
        setDraftName(selectedDevice.device_name ?? "");
        setDraftGroups(selectedDevice.groups ?? []);
        setDraftHandlers(selectedDevice.handlers ?? []);
    }, [selectedDevice]);

    React.useEffect(() => {
        if (isOpen) return;
        setSelectedDevice(null);
        setEvents([]);
        setCampaigns([]);
        setErrorDetails(null);
        setLoadingDetails(false);
        setSavingDevice(false);
    }, [isOpen]);

    const nameToSave = React.useMemo(() => {
        const trimmed = draftName.trim();
        return trimmed.length === 0 ? null : trimmed;
    }, [draftName]);

    const handlerItems = React.useMemo(() => {
        const merged: Record<string, string> = { ...handlerIdMap };

        const addUnknown = (id: number) => {
            const key = String(id);
            if (key in merged) return;
            merged[key] = "Unknown";
        };

        (selectedDevice?.handlers ?? []).forEach(addUnknown);
        draftHandlers.forEach(addUnknown);

        return merged;
    }, [handlerIdMap, selectedDevice, draftHandlers]);

    const isDirty = React.useMemo(() => {
        if (!selectedDevice) return false;
        const nameChanged = (selectedDevice.device_name ?? null) !== nameToSave;
        const groupsChanged = !sameIds(selectedDevice.groups ?? [], draftGroups);
        const handlersChanged = !sameIds(selectedDevice.handlers ?? [], draftHandlers);
        return nameChanged || groupsChanged || handlersChanged;
    }, [selectedDevice, nameToSave, draftGroups, draftHandlers]);

    const saveDevice = async () => {
        if (deviceId === null) return;
        if (!canControlDevices) return;
        if (!isDirty) return;

        setSavingDevice(true);
        const res = await APIManager.updateDevice(deviceId, {
            device_name: nameToSave,
            groups: draftGroups,
            handlers: draftHandlers.length === 0 ? null : draftHandlers,
        });

        if (res.success) {
            toast.success("Device updated");
            if (res.data?.device) {
                setSelectedDevice(res.data.device);
                onDeviceUpdated?.(res.data.device);
            } else {
                await loadDetails(deviceId);
            }
        } else {
            toast.error(res.message || "Failed to update device");
        }

        setSavingDevice(false);
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose} title={deviceId === null ? "Device Details" : `Device ${deviceId}`} maxWidthClass="max-w-5xl">
            {deviceId === null && <p className="text-sm text-text-gray">Select a device to view details.</p>}

            {deviceId !== null && loadingDetails && (
                <div className="flex items-center gap-4">
                    <OrbitProgress color="var(--color-text-primary)" size="small" text="" textColor="" />
                    <p className="text-sm text-text-secondary">Loading device details…</p>
                </div>
            )}

            {deviceId !== null && !loadingDetails && errorDetails && <p className="text-sm text-text-secondary">{errorDetails}</p>}

            {deviceId !== null && !loadingDetails && !errorDetails && selectedDevice && (
                <div className="flex flex-col gap-6">
                    <div className="rounded-md outline outline-secondary bg-background/30 p-4">
                        <div className="flex items-start justify-between gap-4">
                            <div className="min-w-0">
                                <p className="text-xs uppercase tracking-wide text-text-gray">Device</p>
                                <p className="mt-2 text-sm text-text-primary">{selectedDevice.device_name || "(unnamed)"}</p>
                            </div>

                            {canControlDevices && (
                                <div className="shrink-0 flex items-center gap-3">
                                    <Button
                                        title={savingDevice ? "Saving" : "Save"}
                                        onClick={saveDevice}
                                        loading={savingDevice}
                                        disabled={!isDirty || savingDevice}
                                        className="rounded-xl"
                                    />
                                </div>
                            )}
                        </div>

                        {!canControlDevices && <p className="mt-2 text-xs text-text-secondary">You don't have permission to edit devices.</p>}

                        <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
                            <Input
                                title="Device Name"
                                placeholder="(unnamed)"
                                value={draftName}
                                onChange={setDraftName}
                                disabled={!canControlDevices}
                            />

                            {Object.keys(groupIds).length > 0 ? (
                                <IdMultiSelect
                                    title="Groups"
                                    items={groupIds}
                                    selected={draftGroups}
                                    onChange={(next) => {
                                        if (!canControlDevices) return;
                                        setDraftGroups(next);
                                    }}
                                    emptyText="No groups available"
                                />
                            ) : (
                                <Input
                                    title="Groups (IDs)"
                                    placeholder="e.g. 1, 2, 3"
                                    value={draftGroups.join(", ")}
                                    onChange={(v) => setDraftGroups(parseIdList(v))}
                                    disabled={!canControlDevices}
                                />
                            )}

                            <IdMultiSelect
                                title="Handlers"
                                items={handlerItems}
                                selected={draftHandlers}
                                onChange={(next) => {
                                    if (!canControlDevices) return;
                                    setDraftHandlers(next);
                                }}
                                emptyText="No handlers available"
                            />
                        </div>

                        <div className="mt-4 grid grid-cols-1 gap-2">
                            <div className="flex items-center justify-between gap-4">
                                <p className="text-sm text-text-gray">MAC</p>
                                <p className="text-sm text-text-secondary">{selectedDevice.mac_address}</p>
                            </div>
                            <div className="flex items-center justify-between gap-4">
                                <p className="text-sm text-text-gray">IP</p>
                                <p className="text-sm text-text-secondary">{selectedDevice.last_known_ip_address || "—"}</p>
                            </div>
                            <div className="flex items-center justify-between gap-4">
                                <p className="text-sm text-text-gray">OS</p>
                                <p className="text-sm text-text-secondary">{selectedDevice.operating_system_details || "—"}</p>
                            </div>
                            <div className="flex items-center justify-between gap-4">
                                <p className="text-sm text-text-gray">Groups</p>
                                <p className="text-sm text-text-secondary">{selectedDevice.groups?.length ?? 0}</p>
                            </div>
                            <div className="flex items-center justify-between gap-4">
                                <p className="text-sm text-text-gray">Handlers</p>
                                <p className="text-sm text-text-secondary">{selectedDevice.handlers?.length ?? 0}</p>
                            </div>
                        </div>

                        {selectedDevice.note && <p className="mt-3 text-xs text-text-secondary">{selectedDevice.note}</p>}
                    </div>

                    <div>
                        <p className="text-xs uppercase tracking-wide text-text-gray">Involved Campaigns</p>
                        <div className="mt-3">
                            <SimpleTable
                                emptyText="No campaigns"
                                rows={campaigns}
                                getRowKey={(c) => c.campaign_id}
                                columns={[
                                    {
                                        key: "name",
                                        header: "Campaign",
                                        render: (c) => (
                                            <div className="min-w-0">
                                                <p className="font-medium text-text-primary truncate">{c.name}</p>
                                                <p className="mt-1 text-xs text-text-gray truncate">{c.description}</p>
                                            </div>
                                        ),
                                    },
                                    {
                                        key: "severity",
                                        header: "Severity",
                                        className: "w-24",
                                        render: (c) => (
                                            <span className="inline-flex items-center rounded-md bg-highlight/15 px-2 py-1 text-xs uppercase tracking-wide text-highlight">
                                                {c.severity}
                                            </span>
                                        ),
                                    },
                                    {
                                        key: "status",
                                        header: "Status",
                                        className: "w-28",
                                        render: (c) => <span className="text-sm text-text-secondary capitalize">{c.status}</span>,
                                    },
                                    {
                                        key: "updated",
                                        header: "Last Updated",
                                        className: "w-44",
                                        render: (c) => <span className="text-sm text-text-secondary">{formatIso(c.last_updated)}</span>,
                                    },
                                ]}
                            />
                        </div>
                    </div>

                    <div>
                        <p className="text-xs uppercase tracking-wide text-text-gray">Involved Events</p>
                        <div className="mt-3">
                            <SimpleTable
                                emptyText="No events"
                                rows={events}
                                getRowKey={(e) => e.event_id}
                                columns={[
                                    {
                                        key: "time",
                                        header: "Time",
                                        className: "w-44",
                                        render: (e) => <span className="text-sm text-text-secondary">{formatTimestampNs(e.timestamp_ns)}</span>,
                                    },
                                    {
                                        key: "violation",
                                        header: "Violation",
                                        render: (e) => (
                                            <div className="min-w-0">
                                                <p className="text-text-primary truncate">{e.violation_type}</p>
                                                <p className="mt-1 text-xs text-text-gray truncate">{e.violation_response}</p>
                                            </div>
                                        ),
                                    },
                                    {
                                        key: "process",
                                        header: "Process",
                                        render: (e) => <span className="text-sm text-text-secondary">{e.process?.name || "—"}</span>,
                                    },
                                ]}
                            />
                        </div>
                    </div>
                </div>
            )}
        </Modal>
    );
}
