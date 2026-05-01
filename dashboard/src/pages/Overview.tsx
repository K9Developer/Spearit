import Box from "@/components/Box";
import Button from "@/components/Button";
import APIManager, { type OverviewData } from "@/utils/api_manager";
import React from "react";
import { OrbitProgress } from "react-loading-indicators";
import { Activity, AlertTriangle, Cpu, RefreshCw, ShieldAlert, Siren, Users } from "lucide-react";
import StatCard from "./overview/StatCard";
import SectionCard from "./overview/SectionCard";
import SimpleTable from "./overview/SimpleTable";

const formatMaybePercent = (value: number) => {
    if (value < 0) return "—";
    return `${Math.round(value)}%`;
};

const formatMaybeSeconds = (date: number) => {
    const delta = Date.now() - date;
    const value = delta / 1000;
    console.log({ now: Date.now(), hb_date: date });
    if (value < 0) return "—";
    if (value < 60) return `${Math.round(value)}s`;
    if (value < 3600) return `${Math.round(value / 60)}m`;
    return `${Math.round(value / 3600)}h`;
};

const formatIso = (iso: string) => {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return new Intl.DateTimeFormat(undefined, { year: "numeric", month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit" }).format(d);
};

export default function Overview() {
    const [data, setData] = React.useState<OverviewData | null>(null);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState<string | null>(null);

    const load = React.useCallback(async () => {
        setLoading(true);
        setError(null);
        const res = await APIManager.getOverviewData();
        if (res.success && res.data) {
            setData(res.data);
        } else {
            setData(null);
            setError(res.message || "Failed to load overview");
        }
        setLoading(false);
    }, []);

    React.useEffect(() => {
        load();
    }, [load]);

    return (
        <div className="h-full min-h-0 overflow-y-auto">
            <div className="px-6 py-6">
                <div className="flex items-start justify-between gap-6">
                    <div className="min-w-0">
                        <p className="text-xs uppercase tracking-wide text-text-gray">Dashboard</p>
                        <h1 className="mt-1 text-2xl font-semibold text-text-primary">Overview</h1>
                        <p className="mt-2 text-sm text-text-secondary">System status, current activity, and recent changes</p>
                    </div>

                    <div className="shrink-0">
                        <Button
                            title={loading ? "Refreshing" : "Refresh"}
                            onClick={load}
                            loading={loading}
                            icon={!loading ? <RefreshCw size={18} /> : undefined}
                            className="rounded-xl"
                        />
                    </div>
                </div>

                <div className="mt-6">
                    {loading && (
                        <Box.Secondary className="p-6! flex items-center gap-4">
                            <OrbitProgress color="var(--color-text-primary)" size="small" text="" textColor="" />
                            <p className="text-sm text-text-secondary">Loading overview data…</p>
                        </Box.Secondary>
                    )}

                    {!loading && error && (
                        <Box.Secondary className="p-6!">
                            <p className="text-sm text-text-secondary">{error}</p>
                        </Box.Secondary>
                    )}
                </div>

                {!loading && data && (
                    <>
                        <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4">
                            <StatCard label="Registered Devices" value={data.registered_devices} icon={<Users size={22} />} />
                            <StatCard label="Alerts (24h)" value={data.alerts_24h} icon={<Siren size={22} />} />
                            <StatCard label="Critical Campaigns" value={data.critical_campaigns} icon={<AlertTriangle size={22} />} />
                            <StatCard label="Baseline Deviations" value={data.baseline_deviations} icon={<Activity size={22} />} />
                            <StatCard label="Rule Violations / h" value={data.rule_violations_ph} icon={<ShieldAlert size={22} />} />
                        </div>

                        <div className="mt-6 grid grid-cols-1 xl:grid-cols-3 gap-6">
                            <div className="xl:col-span-2 flex flex-col gap-6">
                                <SectionCard title="Active Campaigns">
                                    <SimpleTable
                                        emptyText="No active campaigns"
                                        rows={data.active_campaigns}
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
                                </SectionCard>

                                <SectionCard title="Recent Alerts">
                                    <SimpleTable
                                        emptyText="No alerts"
                                        rows={data.alerts}
                                        columns={[
                                            {
                                                key: "message",
                                                header: "Message",
                                                render: (a) => (
                                                    <div className="min-w-0">
                                                        <p className="text-text-primary truncate">{a.message}</p>
                                                        <p className="mt-1 text-xs text-text-gray">{formatIso(a.created_at)}</p>
                                                    </div>
                                                ),
                                            },
                                            {
                                                key: "type",
                                                header: "Type",
                                                className: "w-28",
                                                render: (a) => <span className="text-xs uppercase tracking-wide text-text-secondary">{a.type}</span>,
                                            },
                                        ]}
                                    />
                                </SectionCard>
                            </div>

                            <div className="flex flex-col gap-6">
                                <SectionCard title="System Health">
                                    <div className="grid grid-cols-1 gap-3">
                                        <div className="flex items-center justify-between gap-4">
                                            <p className="text-sm text-text-gray">Spearhead Status</p>
                                            <div className="flex items-center gap-2">
                                                <span className="text-highlight">
                                                    <Cpu size={18} />
                                                </span>
                                                <span className="text-sm font-medium text-text-primary">{data.system_health.spearhead_status}</span>
                                            </div>
                                        </div>

                                        <div className="flex items-center justify-between gap-4">
                                            <p className="text-sm text-text-gray">Wrappers Coverage</p>
                                            <p className="text-sm font-medium text-text-primary">
                                                {formatMaybePercent(data.system_health.wrappers_connected_precentage)}
                                            </p>
                                        </div>

                                        <div className="flex items-center justify-between gap-4">
                                            <p className="text-sm text-text-gray">Last Heartbeat</p>
                                            <p className="text-sm font-medium text-text-primary">
                                                {formatMaybeSeconds(data.system_health.last_heartbeat_age)}
                                            </p>
                                        </div>
                                    </div>
                                </SectionCard>

                                <SectionCard title="Top Noisy Devices">
                                    <SimpleTable
                                        emptyText="No events recorded"
                                        rows={data.event_stats.top_noisy_devices}
                                        columns={[
                                            {
                                                key: "device",
                                                header: "Device",
                                                render: (d) => (
                                                    <div className="min-w-0">
                                                        <p className="text-text-primary truncate">{d.device_name}</p>
                                                        <p className="mt-1 text-xs text-text-gray">ID {d.device_id}</p>
                                                    </div>
                                                ),
                                            },
                                            {
                                                key: "events",
                                                header: "Events",
                                                className: "w-24",
                                                render: (d) => <span className="text-sm text-text-secondary">{d.event_count}</span>,
                                            },
                                        ]}
                                    />
                                </SectionCard>

                                <SectionCard title="Recently Changed Rules">
                                    <SimpleTable
                                        emptyText="No recent rule changes"
                                        rows={data.recently_changed_rules}
                                        columns={[
                                            {
                                                key: "rule",
                                                header: "Rule",
                                                render: (r) => (
                                                    <div className="min-w-0">
                                                        <p className="text-text-primary truncate">{r.rule_name}</p>
                                                        <p className="mt-1 text-xs text-text-gray">ID {r.rule_id}</p>
                                                    </div>
                                                ),
                                            },
                                            {
                                                key: "updated",
                                                header: "Last Updated",
                                                className: "w-44",
                                                render: (r) => <span className="text-sm text-text-secondary">{formatIso(r.last_updated)}</span>,
                                            },
                                        ]}
                                    />
                                </SectionCard>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
