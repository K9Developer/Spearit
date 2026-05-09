import Box from "@/components/Box";
import Button from "@/components/Button";
import { useUser } from "@/context/useUser";
import APIManager from "@/utils/api_manager";
import { hasPermission } from "@/utils/permissions";
import type { Device } from "@/utils/types";
import { HardDrive, RefreshCw, Workflow } from "lucide-react";
import React from "react";
import { OrbitProgress } from "react-loading-indicators";
import { useNavigate } from "react-router-dom";
import SectionCard from "./overview/SectionCard";
import StatCard from "./overview/StatCard";
import SimpleTable from "./users/SimpleTable";
import DeviceDetailsModal from "./devices/DeviceDetailsModal";

export default function Devices() {
    const navigate = useNavigate();
    const { user } = useUser();
    const canControlDevices = user ? hasPermission(user.permissions, "control_devices") : false;

    const [devices, setDevices] = React.useState<Device[]>([]);
    const [loadingList, setLoadingList] = React.useState(true);
    const [errorList, setErrorList] = React.useState<string | null>(null);

    const [detailsOpen, setDetailsOpen] = React.useState(false);
    const [selectedDeviceId, setSelectedDeviceId] = React.useState<number | null>(null);

    const [groupIds, setGroupIds] = React.useState<Record<string, string>>({});
    const [handlerIdMap, setHandlerIdMap] = React.useState<Record<string, string>>({});

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

    React.useEffect(() => {
        loadList();
    }, [loadList]);

    React.useEffect(() => {
        // best-effort for displaying group names and handler usernames in the editor
        let cancelled = false;

        const loadEditorMetadata = async () => {
            const [metaRes, usersRes] = await Promise.all([APIManager.getUserManagementMetadata(), APIManager.listUsers()]);
            if (cancelled) return;

            if (metaRes.success && metaRes.data) {
                setGroupIds(metaRes.data.group_ids ?? {});
            } else {
                setGroupIds({});
            }

            if (usersRes.success && usersRes.data) {
                const nextHandlerMap: Record<string, string> = {};
                for (const u of usersRes.data.users ?? []) {
                    nextHandlerMap[String(u.id)] = u.fullname || u.email || `User ${u.id}`;
                }
                setHandlerIdMap(nextHandlerMap);
            } else if (metaRes.success && metaRes.data?.handler_ids) {
                setHandlerIdMap(metaRes.data.handler_ids ?? {});
            } else {
                setHandlerIdMap({});
            }
        };

        loadEditorMetadata();
        return () => {
            cancelled = true;
        };
    }, []);

    const closeDetails = () => {
        setDetailsOpen(false);
        setSelectedDeviceId(null);
    };

    const openDetails = (deviceId: number) => {
        setSelectedDeviceId(deviceId);
        setDetailsOpen(true);
    };

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
                        <div className="flex items-center gap-3">
                            <Button
                                title="View Device Mapping"
                                onClick={() => navigate("/dashboard/devices/map")}
                                icon={<Workflow size={18} />}
                                className="rounded-xl"
                                disabled={loadingList || devices.length === 0}
                            />
                            <Button
                                title={loadingList ? "Refreshing" : "Refresh"}
                                onClick={loadList}
                                loading={loadingList}
                                icon={!loadingList ? <RefreshCw size={18} /> : undefined}
                                className="rounded-xl"
                            />
                        </div>
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

                        <div className="mt-6 grid grid-cols-1 gap-6">
                            <SectionCard title="All Devices">
                                <SimpleTable
                                    emptyText="No devices"
                                    rows={devices}
                                    getRowKey={(d) => d.device_id}
                                    onRowClick={(d) => openDetails(d.device_id)}
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
                        </div>
                    </>
                )}
            </div>

            <DeviceDetailsModal
                isOpen={detailsOpen}
                deviceId={selectedDeviceId}
                onClose={closeDetails}
                canControlDevices={canControlDevices}
                groupIds={groupIds}
                handlerIdMap={handlerIdMap}
                onDeviceUpdated={(updated) => {
                    setDevices((prev) => prev.map((d) => (d.device_id === updated.device_id ? updated : d)));
                }}
            />
        </div>
    );
}
