import Box from "@/components/Box";
import Button from "@/components/Button";
import Modal from "@/components/Modal";
import SearchFilters, { type SearchFilterOption } from "@/pages/shared/SearchFilters";
import APIManager from "@/utils/api_manager";
import type { Device, Event } from "@/utils/types";
import { Activity, Filter, HardDrive, RefreshCw, Server } from "lucide-react";
import React from "react";
import { OrbitProgress } from "react-loading-indicators";
import { useNavigate, useSearchParams } from "react-router-dom";
import SectionCard from "./overview/SectionCard";
import StatCard from "./overview/StatCard";
import SimpleTable from "./users/SimpleTable";

type BreakdownMode = "overall" | "device" | "source_ip" | "dest_ip" | "protocol" | "process";
type IntervalMode = "15m" | "1h" | "6h" | "1d";
type SearchScope = "all" | "device" | "ip" | "process" | "protocol" | "violation";

const intervalMinutes: Record<IntervalMode, number> = {
    "15m": 15,
    "1h": 60,
    "6h": 360,
    "1d": 1440,
};

const intervalLabels: Record<IntervalMode, string> = {
    "15m": "15 minutes",
    "1h": "1 hour",
    "6h": "6 hours",
    "1d": "1 day",
};

const breakdownLabels: Record<BreakdownMode, string> = {
    overall: "All events",
    device: "Device",
    source_ip: "Source IP",
    dest_ip: "Destination IP",
    protocol: "Protocol",
    process: "Process",
};

const searchScopeLabels: Record<SearchScope, string> = {
    all: "All fields",
    device: "Device",
    ip: "IP",
    process: "Process",
    protocol: "Protocol",
    violation: "Violation",
};

const searchScopeOptions: SearchFilterOption[] = Object.entries(searchScopeLabels).map(([value, label]) => ({ value, label }));

const directionOptions: SearchFilterOption[] = [
    { value: "all", label: "All directions" },
    { value: "INBOUND", label: "Inbound" },
    { value: "OUTBOUND", label: "Outbound" },
];

const formatTimestampNs = (timestampNs: number) => {
    const ms = Math.round(timestampNs / 1_000_000);
    const date = new Date(ms);
    if (Number.isNaN(date.getTime())) return String(timestampNs);
    return new Intl.DateTimeFormat(undefined, {
        year: "numeric",
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    }).format(date);
};

const formatBucketLabel = (iso: string) => {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return iso;
    return new Intl.DateTimeFormat(undefined, {
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    }).format(date);
};

const eventTimeMs = (event: Event) => Math.round(event.timestamp_ns / 1_000_000);

const eventSourceIp = (event: Event) => event.source.ip || "Unknown source IP";

const eventDestIp = (event: Event) => event.dest.ip || "Unknown destination IP";

const eventDeviceLabel = (event: Event) => {
    const name = event.device_name?.trim();
    if (name) return name;
    if (typeof event.device_id === "number") return `Device ${event.device_id}`;
    return "Unknown device";
};

const normalizeKey = (value: string | null | undefined) => value?.trim().toLowerCase() ?? "";

const deviceLabel = (device: Device | null | undefined) => device?.device_name?.trim() || (device ? `Device ${device.device_id}` : "Unknown device");

const eventSearchText = (event: Event) =>
    [
        event.event_id,
        event.device_id ?? "",
        event.device_name ?? "",
        event.protocol_name,
        event.protocol_libc_name,
        event.direction,
        event.violated_rule_id,
        event.violation_type,
        event.violation_response,
        event.process?.process_id ?? "",
        event.process?.name ?? "",
        event.source?.ip ?? "",
        event.source?.port ?? "",
        event.source?.mac ?? "",
        event.dest?.ip ?? "",
        event.dest?.port ?? "",
        event.dest?.mac ?? "",
    ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

const eventSearchByScope = (event: Event, needle: string, scope: SearchScope) => {
    if (!needle) return true;

    const haystack = (() => {
        switch (scope) {
            case "device":
                return `${eventDeviceLabel(event)} ${event.device_id ?? ""} ${event.source.mac ?? ""} ${event.dest.mac ?? ""} ${eventSourceIp(event)} ${eventDestIp(event)}`;
            case "ip":
                return `${eventSourceIp(event)} ${eventDestIp(event)} ${event.source.port} ${event.dest.port}`;
            case "process":
                return `${event.process?.name ?? ""} ${event.process?.process_id ?? ""}`;
            case "protocol":
                return `${event.protocol_name ?? ""} ${event.protocol_libc_name ?? ""}`;
            case "violation":
                return `${event.violation_type ?? ""} ${event.violation_response ?? ""} ${event.violated_rule_id ?? ""}`;
            case "all":
            default:
                return eventSearchText(event);
        }
    })();

    return haystack.toLowerCase().includes(needle);
};

const eventBucketKey = (event: Event, scope: BreakdownMode, sourceDevice: Device | null, destDevice: Device | null) => {
    switch (scope) {
        case "device":
            return deviceLabel(sourceDevice ?? destDevice) || eventDeviceLabel(event);
        case "source_ip":
            return eventSourceIp(event);
        case "dest_ip":
            return eventDestIp(event);
        case "protocol":
            return event.protocol_name || event.protocol_libc_name || "Unknown protocol";
        case "process":
            return event.process?.name || "Unknown process";
        default:
            return "All events";
    }
};

const bucketStartMs = (timestampMs: number, intervalMs: number) => Math.floor(timestampMs / intervalMs) * intervalMs;

const colorPalette = ["#5dd6c0", "#7ea1ff", "#ffb86c", "#ff7d8a", "#9d7bff", "#f7d46b"];

const formatShortNumber = (value: number) => new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 }).format(value);

const minBucketCountByInterval: Record<IntervalMode, number> = {
    "15m": 16,
    "1h": 24,
    "6h": 28,
    "1d": 30,
};

const parseEventIdsParam = (params: URLSearchParams) => {
    const rawIds = params.getAll("event_ids").join(",");
    if (!rawIds.trim()) return [];

    const ids = rawIds
        .split(/[\s,]+/)
        .map((value) => Number(value.trim()))
        .filter((value) => Number.isFinite(value));

    return [...new Set(ids)];
};

function EventDetailsModal({ event, onClose }: { event: Event | null; onClose: () => void }) {
    const displayEvent = React.useMemo(() => {
        if (!event) return null;
        return {
            ...event,
            payload: {
                ...event.payload,
                data: event.payload?.data && event.payload.data.length > 300 ? `${event.payload.data.slice(0, 300)}...` : event.payload?.data,
            },
        };
    }, [event]);

    return (
        <Modal isOpen={event !== null} onClose={onClose} title={event ? `Event ${event.event_id}` : "Event"} maxWidthClass="max-w-4xl">
            {event && displayEvent && (
                <div className="flex flex-col gap-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="rounded-md outline outline-secondary bg-background/30 p-4">
                            <p className="text-xs uppercase tracking-wide text-text-gray">Core</p>
                            <div className="mt-3 grid grid-cols-1 gap-2 text-sm">
                                <div className="flex items-center justify-between gap-4">
                                    <span className="text-text-gray">Time</span>
                                    <span className="text-text-secondary">{formatTimestampNs(event.timestamp_ns)}</span>
                                </div>
                                <div className="flex items-center justify-between gap-4">
                                    <span className="text-text-gray">Device</span>
                                    <span className="text-text-secondary">{event.device_name || (event.device_id ?? "—")}</span>
                                </div>
                                <div className="flex items-center justify-between gap-4">
                                    <span className="text-text-gray">Direction</span>
                                    <span className="text-text-secondary">{event.direction}</span>
                                </div>
                                <div className="flex items-center justify-between gap-4">
                                    <span className="text-text-gray">Protocol</span>
                                    <span className="text-text-secondary">{event.protocol_name}</span>
                                </div>
                            </div>
                        </div>

                        <div className="rounded-md outline outline-secondary bg-background/30 p-4">
                            <p className="text-xs uppercase tracking-wide text-text-gray">Flow</p>
                            <div className="mt-3 grid grid-cols-1 gap-2 text-sm">
                                <div className="flex items-center justify-between gap-4">
                                    <span className="text-text-gray">Source</span>
                                    <span className="text-text-secondary">
                                        {event.source.ip}:{event.source.port}
                                    </span>
                                </div>
                                <div className="flex items-center justify-between gap-4">
                                    <span className="text-text-gray">Destination</span>
                                    <span className="text-text-secondary">
                                        {event.dest.ip}:{event.dest.port}
                                    </span>
                                </div>
                                <div className="flex items-center justify-between gap-4">
                                    <span className="text-text-gray">Process</span>
                                    <span className="text-text-secondary">{event.process.name}</span>
                                </div>
                                <div className="flex items-center justify-between gap-4">
                                    <span className="text-text-gray">Violation</span>
                                    <span className="text-text-secondary">{event.violation_type}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div>
                        <p className="text-xs uppercase tracking-wide text-text-gray">Event JSON</p>
                        <pre className="mt-3 max-h-96 overflow-auto rounded-md outline outline-secondary bg-background/40 p-4 text-xs text-text-secondary whitespace-pre-wrap wrap-break-word">
                            {JSON.stringify(displayEvent, null, 2)}
                        </pre>
                    </div>
                </div>
            )}
        </Modal>
    );
}

function SparklineChart({
    series,
    buckets,
    intervalLabel,
}: {
    series: { name: string; total: number; color: string; values: number[] }[];
    buckets: { label: string; start: string; end: string; startMs: number }[];
    intervalLabel: string;
}) {
    const width = 1100;
    const height = 320;
    const padding = { top: 24, right: 24, bottom: 48, left: 56 };
    const innerWidth = width - padding.left - padding.right;
    const innerHeight = height - padding.top - padding.bottom;
    const maxValue = Math.max(1, ...series.flatMap((s) => s.values));
    const yTicks = [0, 0.25, 0.5, 0.75, 1].map((t) => Math.round(maxValue * t));

    const pointsForSeries = (values: number[]) =>
        values
            .map((value, index) => {
                const x = padding.left + (buckets.length <= 1 ? innerWidth / 2 : (index / Math.max(1, buckets.length - 1)) * innerWidth);
                const y = padding.top + innerHeight - (value / maxValue) * innerHeight;
                return `${x},${y}`;
            })
            .join(" ");

    return (
        <div>
            <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-sm text-text-secondary">{intervalLabel} buckets across the filtered result set</p>
                <div className="flex flex-wrap items-center gap-3">
                    {series.slice(0, 6).map((item) => (
                        <div key={item.name} className="flex items-center gap-2 text-xs text-text-secondary">
                            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                            <span>{item.name}</span>
                            <span className="text-text-gray">{formatShortNumber(item.total)}</span>
                        </div>
                    ))}
                </div>
            </div>

            <div className="mt-4 rounded-xl outline outline-secondary bg-background/30 p-3">
                <svg viewBox={`0 0 ${width} ${height}`} className="h-80 w-full overflow-visible">
                    <defs>
                        <linearGradient id="events-chart-grid" x1="0" x2="0" y1="0" y2="1">
                            <stop offset="0%" stopColor="rgba(255,255,255,0.12)" />
                            <stop offset="100%" stopColor="rgba(255,255,255,0.02)" />
                        </linearGradient>
                    </defs>

                    {yTicks.map((tick) => {
                        const y = padding.top + innerHeight - (tick / maxValue) * innerHeight;
                        return (
                            <g key={tick}>
                                <line x1={padding.left} x2={width - padding.right} y1={y} y2={y} stroke="rgba(255,255,255,0.08)" strokeWidth={1} />
                                <text x={padding.left - 10} y={y + 4} textAnchor="end" className="fill-text-gray text-[11px]">
                                    {tick}
                                </text>
                            </g>
                        );
                    })}

                    {series.map((item) => (
                        <g key={item.name}>
                            <polyline
                                fill="none"
                                stroke={item.color}
                                strokeWidth={3.5}
                                strokeLinejoin="round"
                                strokeLinecap="round"
                                points={pointsForSeries(item.values)}
                            />
                            {item.values.map((value, index) => {
                                const x =
                                    padding.left + (buckets.length <= 1 ? innerWidth / 2 : (index / Math.max(1, buckets.length - 1)) * innerWidth);
                                const y = padding.top + innerHeight - (value / maxValue) * innerHeight;
                                return (
                                    <circle
                                        key={`${item.name}-${index}`}
                                        cx={x}
                                        cy={y}
                                        r={3.5}
                                        fill={item.color}
                                        stroke="rgba(0,0,0,0.15)"
                                        strokeWidth={1}
                                    />
                                );
                            })}
                        </g>
                    ))}

                    {buckets.map((bucket, index) => {
                        const x = padding.left + (buckets.length <= 1 ? innerWidth / 2 : (index / Math.max(1, buckets.length - 1)) * innerWidth);
                        return (
                            <g key={bucket.start}>
                                <line x1={x} x2={x} y1={padding.top} y2={padding.top + innerHeight} stroke="rgba(255,255,255,0.05)" />
                                {index % Math.max(1, Math.ceil(buckets.length / 6)) === 0 && (
                                    <text x={x} y={height - 14} textAnchor="middle" className="fill-text-gray text-[11px]">
                                        {bucket.label}
                                    </text>
                                )}
                            </g>
                        );
                    })}
                </svg>
            </div>
        </div>
    );
}

export default function Events() {
    const [searchParams, setSearchParams] = useSearchParams();
    const navigate = useNavigate();
    const [events, setEvents] = React.useState<Event[]>([]);
    const [devices, setDevices] = React.useState<Device[]>([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState<string | null>(null);
    const [search, setSearch] = React.useState("");
    const [searchScope, setSearchScope] = React.useState<SearchScope>("all");
    const [directionFilter, setDirectionFilter] = React.useState<"all" | "INBOUND" | "OUTBOUND">("all");
    const [intervalMode, setIntervalMode] = React.useState<IntervalMode>("1h");
    const [breakdownMode, setBreakdownMode] = React.useState<BreakdownMode>("overall");
    const [selectedEvent, setSelectedEvent] = React.useState<Event | null>(null);

    const eventIdFilterIds = React.useMemo(() => parseEventIdsParam(searchParams), [searchParams]);
    const eventIdFilterSet = React.useMemo(() => new Set(eventIdFilterIds), [eventIdFilterIds]);
    const campaignIdFilter = searchParams.get("campaign_id");

    const load = React.useCallback(async () => {
        setLoading(true);
        setError(null);

        const [eventsRes, devicesRes] = await Promise.all([APIManager.listEvents(), APIManager.listDevices()]);

        if (eventsRes.success && eventsRes.data) {
            setEvents((eventsRes.data.events ?? []).slice().sort((a, b) => eventTimeMs(b) - eventTimeMs(a)));
        } else {
            setEvents([]);
            setError(eventsRes.message || "Failed to load events");
        }

        if (devicesRes.success && devicesRes.data) {
            setDevices(devicesRes.data.devices ?? []);
        } else {
            setDevices([]);
        }

        setLoading(false);
    }, []);

    React.useEffect(() => {
        load();
    }, [load]);

    React.useEffect(() => {
        const eventIdParam = searchParams.get("event_id");
        if (!eventIdParam) return;

        const eventId = Number(eventIdParam);
        if (!Number.isFinite(eventId)) return;

        const match = events.find((event) => event.event_id === eventId);
        if (match) {
            setSelectedEvent(match);
        }
    }, [events, searchParams]);

    const devicesByMac = React.useMemo(() => {
        const map = new Map<string, Device>();
        for (const device of devices) {
            const mac = normalizeKey(device.mac_address);
            if (mac) map.set(mac, device);
        }
        return map;
    }, [devices]);

    const devicesByIp = React.useMemo(() => {
        const map = new Map<string, Device>();
        for (const device of devices) {
            const ip = normalizeKey(device.last_known_ip_address);
            if (ip) map.set(ip, device);
        }
        return map;
    }, [devices]);

    const resolveDevice = React.useCallback(
        (ip: string, mac: string) => {
            return devicesByMac.get(normalizeKey(mac)) ?? devicesByIp.get(normalizeKey(ip)) ?? null;
        },
        [devicesByMac, devicesByIp],
    );

    const openDevice = React.useCallback(
        (device: Device) => {
            navigate(`/dashboard/devices?device_id=${device.device_id}`);
        },
        [navigate],
    );

    const filteredEvents = React.useMemo(() => {
        const needle = search.trim().toLowerCase();

        return events.filter((event) => {
            if (eventIdFilterSet.size > 0 && !eventIdFilterSet.has(event.event_id)) return false;
            if (directionFilter !== "all" && event.direction !== directionFilter) return false;
            if (needle && !eventSearchByScope(event, needle, searchScope)) return false;
            return true;
        });
    }, [events, search, searchScope, directionFilter, eventIdFilterSet]);

    const overview = React.useMemo(() => {
        const deviceCounts = new Map<string, number>();
        const ipCounts = new Map<string, number>();

        for (const event of filteredEvents) {
            const sourceDevice = resolveDevice(eventSourceIp(event), event.source.mac);
            const destDevice = resolveDevice(eventDestIp(event), event.dest.mac);
            const device = sourceDevice ?? destDevice;
            const sourceIp = eventSourceIp(event);
            const destIp = eventDestIp(event);

            deviceCounts.set(deviceLabel(device), (deviceCounts.get(deviceLabel(device)) ?? 0) + 1);
            ipCounts.set(sourceIp, (ipCounts.get(sourceIp) ?? 0) + 1);
            ipCounts.set(destIp, (ipCounts.get(destIp) ?? 0) + 1);
        }

        return {
            total: events.length,
            matched: filteredEvents.length,
            uniqueDevices: deviceCounts.size,
            uniqueIps: ipCounts.size,
            topDevices: [...deviceCounts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5),
            topIps: [...ipCounts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5),
        };
    }, [events, filteredEvents, resolveDevice]);

    const chartData = React.useMemo(() => {
        if (filteredEvents.length === 0) {
            return {
                buckets: [] as { label: string; start: string; end: string; startMs: number }[],
                series: [] as { name: string; total: number; color: string; values: number[] }[],
                intervalLabel: intervalLabels[intervalMode],
            };
        }

        const intervalMs = intervalMinutes[intervalMode] * 60_000;
        const times = filteredEvents.map(eventTimeMs);
        const minMs = Math.min(...times);
        const maxMs = Math.max(...times);
        const firstEventBucketMs = bucketStartMs(minMs, intervalMs);
        const lastEventBucketMs = bucketStartMs(maxMs, intervalMs);
        const minBucketCount = minBucketCountByInterval[intervalMode];
        const naturalBucketCount = Math.floor((lastEventBucketMs - firstEventBucketMs) / intervalMs) + 1;
        const bucketCount = Math.max(minBucketCount, naturalBucketCount);
        const startMs = Math.min(firstEventBucketMs, lastEventBucketMs - (bucketCount - 1) * intervalMs);

        const buckets = Array.from({ length: bucketCount }, (_, index) => {
            const bucketStart = startMs + index * intervalMs;
            return {
                startMs: bucketStart,
                start: new Date(bucketStart).toISOString(),
                end: new Date(bucketStart + intervalMs).toISOString(),
                label: formatBucketLabel(new Date(bucketStart).toISOString()),
            };
        });

        const seriesMap = new Map<string, Map<number, number>>();
        const totals = new Map<string, number>();

        for (const event of filteredEvents) {
            const bucket = bucketStartMs(eventTimeMs(event), intervalMs);
            const sourceDevice = resolveDevice(eventSourceIp(event), event.source.mac);
            const destDevice = resolveDevice(eventDestIp(event), event.dest.mac);
            const group = eventBucketKey(event, breakdownMode, sourceDevice, destDevice);

            if (!seriesMap.has(group)) seriesMap.set(group, new Map<number, number>());
            const seriesBuckets = seriesMap.get(group)!;
            seriesBuckets.set(bucket, (seriesBuckets.get(bucket) ?? 0) + 1);
            totals.set(group, (totals.get(group) ?? 0) + 1);
        }

        const series = [...seriesMap.entries()]
            .map(([name, seriesBuckets]) => ({
                name,
                total: totals.get(name) ?? 0,
                values: buckets.map((bucket) => seriesBuckets.get(bucket.startMs) ?? 0),
            }))
            .sort((a, b) => b.total - a.total)
            .slice(0, breakdownMode === "overall" ? 1 : 5)
            .map((entry, idx) => ({ ...entry, color: colorPalette[idx % colorPalette.length] }));

        return { buckets, series, intervalLabel: intervalLabels[intervalMode] };
    }, [filteredEvents, intervalMode, breakdownMode, resolveDevice]);

    const eventColumns = React.useMemo(
        () => [
            {
                key: "time",
                header: "Time",
                className: "w-48",
                render: (event: Event) => <span className="text-sm text-text-secondary">{formatTimestampNs(event.timestamp_ns)}</span>,
            },
            {
                key: "source",
                header: "Source",
                className: "w-48",
                render: (event: Event) => (
                    <div className="min-w-0">
                        {(() => {
                            const sourceDevice = resolveDevice(eventSourceIp(event), event.source.mac);
                            return sourceDevice ? (
                                <button
                                    type="button"
                                    className="text-left min-w-0"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        openDevice(sourceDevice);
                                    }}
                                >
                                    <p className="text-text-primary truncate">{deviceLabel(sourceDevice)}</p>
                                    <p className="mt-1 text-xs text-text-gray truncate">
                                        {eventSourceIp(event)} • {event.source.mac}
                                    </p>
                                </button>
                            ) : (
                                <div>
                                    <p className="text-text-primary truncate">{eventSourceIp(event)}</p>
                                    <p className="mt-1 text-xs text-text-gray truncate">{event.source.mac}</p>
                                </div>
                            );
                        })()}
                    </div>
                ),
            },
            {
                key: "dest",
                header: "Destination",
                className: "w-48",
                render: (event: Event) => (
                    <div className="min-w-0">
                        {(() => {
                            const destDevice = resolveDevice(eventDestIp(event), event.dest.mac);
                            return destDevice ? (
                                <button
                                    type="button"
                                    className="text-left min-w-0"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        openDevice(destDevice);
                                    }}
                                >
                                    <p className="text-text-primary truncate">{deviceLabel(destDevice)}</p>
                                    <p className="mt-1 text-xs text-text-gray truncate">
                                        {eventDestIp(event)} • {event.dest.mac}
                                    </p>
                                </button>
                            ) : (
                                <div>
                                    <p className="text-text-primary truncate">{eventDestIp(event)}</p>
                                    <p className="mt-1 text-xs text-text-gray truncate">{event.dest.mac}</p>
                                </div>
                            );
                        })()}
                    </div>
                ),
            },
            {
                key: "process",
                header: "Process",
                className: "w-44",
                render: (event: Event) => <span className="text-sm text-text-secondary truncate">{event.process?.name || "Unknown process"}</span>,
            },
            {
                key: "protocol",
                header: "Protocol",
                className: "w-32",
                render: (event: Event) => (
                    <span className="text-sm text-text-secondary">{event.protocol_name || event.protocol_libc_name || "—"}</span>
                ),
            },
            {
                key: "violation",
                header: "Violation",
                className: "w-48",
                render: (event: Event) => (
                    <div className="min-w-0">
                        <p className="text-text-primary truncate">{event.violation_type}</p>
                        <p className="mt-1 text-xs text-text-gray truncate">{event.violation_response}</p>
                    </div>
                ),
            },
        ],
        [openDevice, resolveDevice],
    );

    const clearEventIdFilter = React.useCallback(() => {
        const nextParams = new URLSearchParams(searchParams);
        nextParams.delete("campaign_id");
        nextParams.delete("event_ids");
        setSearchParams(nextParams, { replace: true });
    }, [searchParams, setSearchParams]);

    const clearSearch = () => {
        setSearch("");
        setSearchScope("all");
        setDirectionFilter("all");
        clearEventIdFilter();
    };

    const closeEventDetails = () => {
        setSelectedEvent(null);
        const nextParams = new URLSearchParams(searchParams);
        nextParams.delete("event_id");
        setSearchParams(nextParams, { replace: true });
    };

    return (
        <div className="h-full min-h-0 overflow-y-auto">
            <div className="px-6 py-6">
                <div className="flex items-start justify-between gap-6">
                    <div className="min-w-0">
                        <p className="text-xs uppercase tracking-wide text-text-gray">Dashboard</p>
                        <h1 className="mt-1 text-2xl font-semibold text-text-primary">Events</h1>
                        <p className="mt-2 text-sm text-text-secondary">
                            A live view of the event stream with a default graph and a focused search panel below.
                        </p>
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
                            <p className="text-sm text-text-secondary">Loading events…</p>
                        </Box.Secondary>
                    )}

                    {!loading && error && (
                        <Box.Secondary className="p-6!">
                            <p className="text-sm text-text-secondary">{error}</p>
                        </Box.Secondary>
                    )}
                </div>

                {!loading && !error && (
                    <>
                        <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
                            <StatCard label="All Events" value={overview.total} icon={<Activity size={22} />} />
                            <StatCard label="Matched Events" value={overview.matched} icon={<Filter size={22} />} />
                            <StatCard label="Unique Devices" value={overview.uniqueDevices} icon={<HardDrive size={22} />} />
                            <StatCard label="Unique IPs" value={overview.uniqueIps} icon={<Server size={22} />} />
                        </div>

                        <div className="mt-6 grid grid-cols-1 gap-6">
                            <SectionCard
                                title="Events Over Time"
                                right={
                                    <div className="flex flex-wrap items-center gap-3">
                                        <div className="flex items-center gap-2 rounded-full bg-background/30 px-3 py-1 outline outline-secondary">
                                            <span className="text-xs uppercase tracking-wide text-text-gray">Group</span>
                                            <select
                                                value={breakdownMode}
                                                onChange={(e) => setBreakdownMode(e.target.value as BreakdownMode)}
                                                className="bg-transparent text-sm text-text-primary outline-none scheme-dark"
                                            >
                                                {Object.entries(breakdownLabels).map(([value, label]) => (
                                                    <option key={value} value={value} className="bg-background text-text-primary">
                                                        {label}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>

                                        <div className="flex items-center gap-2 rounded-full bg-background/30 px-3 py-1 outline outline-secondary">
                                            <span className="text-xs uppercase tracking-wide text-text-gray">Interval</span>
                                            <select
                                                value={intervalMode}
                                                onChange={(e) => setIntervalMode(e.target.value as IntervalMode)}
                                                className="bg-transparent text-sm text-text-primary outline-none scheme-dark"
                                            >
                                                {Object.entries(intervalLabels).map(([value, label]) => (
                                                    <option key={value} value={value} className="bg-background text-text-primary">
                                                        {label}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>
                                }
                            >
                                {chartData.buckets.length > 0 && chartData.series.length > 0 ? (
                                    <SparklineChart series={chartData.series} buckets={chartData.buckets} intervalLabel={chartData.intervalLabel} />
                                ) : (
                                    <Box.Secondary className="p-6!">
                                        <p className="text-sm text-text-secondary">No events available to chart.</p>
                                    </Box.Secondary>
                                )}
                            </SectionCard>

                            <SectionCard
                                title="Search Events"
                                right={
                                    <span className="text-xs uppercase tracking-wide text-text-gray">
                                        {formatShortNumber(overview.matched)} matching events
                                    </span>
                                }
                            >
                                <SearchFilters
                                    search={search}
                                    onSearchChange={setSearch}
                                    searchPlaceholder="Search by device, IP, process, protocol, violation, or event id"
                                    searchHelperText="Search is global by default, but you can narrow it to one scope without opening a complex filter panel."
                                    scopeLabel="Scope"
                                    scopeValue={searchScope}
                                    onScopeChange={(value) => setSearchScope(value as SearchScope)}
                                    scopeOptions={searchScopeOptions}
                                    secondaryLabel="Direction"
                                    secondaryValue={directionFilter}
                                    onSecondaryChange={(value) => setDirectionFilter(value as typeof directionFilter)}
                                    secondaryOptions={directionOptions}
                                    secondaryHelperText="Direction works as a fast state filter for the event stream."
                                    resultText={`${formatShortNumber(overview.matched)} of ${formatShortNumber(overview.total)}`}
                                    clearLabel="Clear"
                                    onClear={clearSearch}
                                />

                                {eventIdFilterIds.length > 0 && (
                                    <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl bg-background/30 px-4 py-3 outline outline-secondary">
                                        <div className="min-w-0">
                                            <p className="text-sm font-medium text-text-primary">
                                                {campaignIdFilter ? `Campaign ${campaignIdFilter} event filter` : "Event ID filter"}
                                            </p>
                                            <p className="mt-1 text-xs text-text-gray">
                                                Showing events whose IDs are in the URL filter: {eventIdFilterIds.join(", ")}
                                            </p>
                                        </div>
                                        <button
                                            type="button"
                                            onClick={clearEventIdFilter}
                                            className="shrink-0 rounded-lg px-3 py-2 text-xs font-semibold uppercase tracking-wide text-text-secondary outline outline-secondary transition-colors hover:bg-background/45"
                                        >
                                            Clear event filter
                                        </button>
                                    </div>
                                )}

                                <div className="mt-5">
                                    <SimpleTable
                                        emptyText="No events match the search"
                                        rows={filteredEvents}
                                        getRowKey={(event) => event.event_id}
                                        onRowClick={(event) => setSelectedEvent(event)}
                                        columns={eventColumns}
                                    />
                                </div>
                            </SectionCard>
                        </div>
                    </>
                )}
            </div>

            <EventDetailsModal event={selectedEvent} onClose={closeEventDetails} />
        </div>
    );
}
