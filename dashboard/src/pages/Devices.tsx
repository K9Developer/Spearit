import Box from "@/components/Box";
import Button from "@/components/Button";
import APIManager from "@/utils/api_manager";
import type { Campaign, Device, Event } from "@/utils/types";
import { HardDrive, RefreshCw } from "lucide-react";
import React from "react";
import { OrbitProgress } from "react-loading-indicators";
import SectionCard from "./overview/SectionCard";
import StatCard from "./overview/StatCard";
import SimpleTable from "./users/SimpleTable";

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

export default function Devices() {
    const [devices, setDevices] = React.useState<Device[]>([]);
    const [loadingList, setLoadingList] = React.useState(true);
    const [errorList, setErrorList] = React.useState<string | null>(null);

    const [selectedDeviceId, setSelectedDeviceId] = React.useState<number | null>(null);
    const [selectedDevice, setSelectedDevice] = React.useState<Device | null>(null);
    const [events, setEvents] = React.useState<Event[]>([]);
    const [campaigns, setCampaigns] = React.useState<Campaign[]>([]);
    const [loadingDetails, setLoadingDetails] = React.useState(false);
    const [errorDetails, setErrorDetails] = React.useState<string | null>(null);

    const loadList = React.useCallback(async () => {
        setLoadingList(true);
        setErrorList(null);
        const res = await APIManager.listDevices();
        if (res.success && res.data) {
            setDevices(res.data.devices);
        } else {
            setDevices([]);
            setErrorList(res.message || "Failed to load devices");
        }
        setLoadingList(false);
    }, []);

    const loadDetails = React.useCallback(async (deviceId: number) => {
        setLoadingDetails(true);
        setErrorDetails(null);
        const res = await APIManager.getDeviceDetails(deviceId);
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
        loadList();
    }, [loadList]);

    React.useEffect(() => {
        if (selectedDeviceId === null) return;
        loadDetails(selectedDeviceId);
    }, [selectedDeviceId, loadDetails]);

    return (
        <div className="h-full min-h-0 overflow-y-auto">
            <div className="px-6 py-6">
                <div className="flex items-start justify-between gap-6">
                    <div className="min-w-0">
                        <p className="text-xs uppercase tracking-wide text-text-gray">Dashboard</p>
                        <h1 className="mt-1 text-2xl font-semibold text-text-primary">Devices</h1>
                        <p className="mt-2 text-sm text-text-secondary">Device inventory and involved activity</p>
                    </div>

                    <div className="shrink-0">
                        <Button
                            title={loadingList ? "Refreshing" : "Refresh"}
                            onClick={loadList}
                            loading={loadingList}
                            icon={!loadingList ? <RefreshCw size={18} /> : undefined}
                            className="rounded-xl"
                        />
                    </div>
                </div>

                <div className="mt-6">
                    {loadingList && (
                        <Box.Secondary className="p-6! flex items-center gap-4">
                            <OrbitProgress color="var(--color-text-primary)" size="small" text="" textColor="" />
                            <p className="text-sm text-text-secondary">Loading devices…</p>
                        </Box.Secondary>
                    )}

                    {!loadingList && errorList && (
                        <Box.Secondary className="p-6!">
                            <p className="text-sm text-text-secondary">{errorList}</p>
                        </Box.Secondary>
                    )}
                </div>

                {!loadingList && !errorList && (
                    <>
                        <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
                            <StatCard label="Registered Devices" value={devices.length} icon={<HardDrive size={22} />} />
                        </div>

                        <div className="mt-6 grid grid-cols-1 xl:grid-cols-2 gap-6">
                            <SectionCard title="All Devices">
                                <SimpleTable
                                    emptyText="No devices"
                                    rows={devices}
                                    getRowKey={(d) => d.device_id}
                                    onRowClick={(d) => setSelectedDeviceId(d.device_id)}
                                    columns={[
                                        {
                                            key: "device",
                                            header: "Device",
                                            render: (d) => (
                                                <div className="min-w-0">
                                                    <p className="text-text-primary truncate">{d.device_name || "(unnamed)"}</p>
                                                    <p className="mt-1 text-xs text-text-gray">
                                                        ID {d.device_id} • {d.mac_address}
                                                    </p>
                                                </div>
                                            ),
                                        },
                                        {
                                            key: "os",
                                            header: "OS",
                                            render: (d) => <span className="text-sm text-text-secondary">{d.operating_system_details || "—"}</span>,
                                        },
                                        {
                                            key: "ip",
                                            header: "IP",
                                            className: "w-40",
                                            render: (d) => <span className="text-sm text-text-secondary">{d.last_known_ip_address || "—"}</span>,
                                        },
                                        {
                                            key: "groups",
                                            header: "Groups",
                                            className: "w-24",
                                            render: (d) => <span className="text-sm text-text-secondary">{d.groups?.length ?? 0}</span>,
                                        },
                                    ]}
                                />
                            </SectionCard>

                            <SectionCard title={selectedDeviceId === null ? "Device Details" : `Device ${selectedDeviceId}`}>
                                {selectedDeviceId === null && <p className="text-sm text-text-gray">Select a device to view events and campaigns.</p>}

                                {selectedDeviceId !== null && loadingDetails && (
                                    <div className="flex items-center gap-4">
                                        <OrbitProgress color="var(--color-text-primary)" size="small" text="" textColor="" />
                                        <p className="text-sm text-text-secondary">Loading device details…</p>
                                    </div>
                                )}

                                {selectedDeviceId !== null && !loadingDetails && errorDetails && (
                                    <p className="text-sm text-text-secondary">{errorDetails}</p>
                                )}

                                {selectedDeviceId !== null && !loadingDetails && !errorDetails && selectedDevice && (
                                    <div className="flex flex-col gap-6">
                                        <div className="rounded-md outline outline-secondary bg-background/30 p-4">
                                            <p className="text-xs uppercase tracking-wide text-text-gray">Device</p>
                                            <p className="mt-2 text-sm text-text-primary">{selectedDevice.device_name || "(unnamed)"}</p>

                                            <div className="mt-3 grid grid-cols-1 gap-2">
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
                                                            render: (c) => (
                                                                <span className="text-sm text-text-secondary">{formatIso(c.last_updated)}</span>
                                                            ),
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
                                                            render: (e) => (
                                                                <span className="text-sm text-text-secondary">
                                                                    {formatTimestampNs(e.timestamp_ns)}
                                                                </span>
                                                            ),
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
                                                            render: (e) => (
                                                                <span className="text-sm text-text-secondary">{e.process?.name || "—"}</span>
                                                            ),
                                                        },
                                                    ]}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </SectionCard>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
