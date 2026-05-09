import Box from "@/components/Box";
import Button from "@/components/Button";
import { useUser } from "@/context/useUser";
import APIManager from "@/utils/api_manager";
import { hasPermission } from "@/utils/permissions";
import type { Device } from "@/utils/types";
import { ArrowLeft, RefreshCw } from "lucide-react";
import React from "react";
import { OrbitProgress } from "react-loading-indicators";
import { useNavigate } from "react-router-dom";
import DeviceMap, { type DeviceConnection } from "./devices/DeviceMap";
import DeviceDetailsModal from "./devices/DeviceDetailsModal";

export default function DeviceMapping() {
    const navigate = useNavigate();
    const { user } = useUser();
    const canControlDevices = user ? hasPermission(user.permissions, "control_devices") : false;

    const [devices, setDevices] = React.useState<Device[]>([]);
    const [connections, setConnections] = React.useState<DeviceConnection[]>([]);

    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState<string | null>(null);

    const [detailsOpen, setDetailsOpen] = React.useState(false);
    const [selectedDeviceId, setSelectedDeviceId] = React.useState<number | null>(null);

    const [groupIds, setGroupIds] = React.useState<Record<string, string>>({});
    const [handlerIdMap, setHandlerIdMap] = React.useState<Record<string, string>>({});

    const load = React.useCallback(async () => {
        setLoading(true);
        setError(null);

        const [devicesRes, mapRes] = await Promise.all([APIManager.listDevices(), APIManager.getDeviceCommunicationMap()]);

        if (devicesRes.success && devicesRes.data) {
            setDevices(devicesRes.data.devices ?? []);
        } else {
            setDevices([]);
            setError(devicesRes.message || "Failed to load devices");
        }

        if (mapRes.success && mapRes.data) {
            setConnections((mapRes.data.connections ?? []) as DeviceConnection[]);
        } else {
            setConnections([]);
            setError((prev) => prev ?? (mapRes.message || "Failed to load device map"));
        }

        setLoading(false);
    }, []);

    React.useEffect(() => {
        load();
    }, [load]);

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

    const openDetails = (deviceId: number) => {
        setSelectedDeviceId(deviceId);
        setDetailsOpen(true);
    };

    const closeDetails = () => {
        setDetailsOpen(false);
        setSelectedDeviceId(null);
    };

    return (
        <div className="h-full min-h-0 overflow-y-auto">
            <div className="px-6 py-6 h-full">
                <div className="flex items-start justify-between gap-6">
                    <div className="min-w-0">
                        <p className="text-xs uppercase tracking-wide text-text-gray">Dashboard</p>
                        <h1 className="mt-1 text-2xl font-semibold text-text-primary">Device Mapping</h1>
                        <p className="mt-2 text-sm text-text-secondary">Communication graph between devices</p>
                    </div>

                    <div className="shrink-0">
                        <div className="flex items-center gap-3">
                            <Button
                                title="Back"
                                onClick={() => navigate("/dashboard/devices")}
                                icon={<ArrowLeft size={18} />}
                                className="rounded-xl"
                            />
                            <Button
                                title={loading ? "Refreshing" : "Refresh"}
                                onClick={load}
                                loading={loading}
                                icon={!loading ? <RefreshCw size={18} /> : undefined}
                                className="rounded-xl"
                            />
                        </div>
                    </div>
                </div>

                <div className="mt-6 h-full">
                    {loading && (
                        <Box.Secondary className="p-6! flex items-center gap-4">
                            <OrbitProgress color="var(--color-text-primary)" size="small" text="" textColor="" />
                            <p className="text-sm text-text-secondary">Loading device map…</p>
                        </Box.Secondary>
                    )}

                    {!loading && error && (
                        <Box.Secondary className="p-6!">
                            <p className="text-sm text-text-secondary">{error}</p>
                        </Box.Secondary>
                    )}

                    {!loading && !error && (
                        <DeviceMap devices={devices} connections={connections} onDeviceClick={(deviceId) => openDetails(deviceId)} />
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
        </div>
    );
}
