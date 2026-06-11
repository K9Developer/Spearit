import Box from "@/components/Box";
import Button from "@/components/Button";
import Modal from "@/components/Modal";
import SectionCard from "@/pages/overview/SectionCard";
import StatCard from "@/pages/overview/StatCard";
import SearchFilters, { type SearchFilterOption } from "@/pages/shared/SearchFilters";
import SimpleTable from "@/pages/users/SimpleTable";
import APIManager from "@/utils/api_manager";
import type { Campaign, Event } from "@/utils/types";
import { CheckCircle2, Clock3, RefreshCw, SquareStack, XCircle } from "lucide-react";
import React from "react";
import { OrbitProgress } from "react-loading-indicators";
import { useNavigate, useSearchParams } from "react-router-dom";

type SearchScope = "all" | "name" | "description" | "device" | "event" | "status" | "severity";
type CampaignStatusFilter = "all" | Campaign["status"];
type CampaignSeverityFilter = "all" | Campaign["severity"];

const searchScopeOptions: SearchFilterOption[] = [
    { value: "all", label: "All fields" },
    { value: "name", label: "Name" },
    { value: "description", label: "Description" },
    { value: "device", label: "Device" },
    { value: "event", label: "Event" },
    { value: "status", label: "State" },
    { value: "severity", label: "Severity" },
];

const statusOptions: SearchFilterOption[] = [
    { value: "all", label: "All states" },
    { value: "ONGOING", label: "Ongoing" },
    { value: "COMPLETED", label: "Completed" },
    { value: "ABORTED", label: "Aborted" },
];

const severityOptions: SearchFilterOption[] = [
    { value: "all", label: "All severities" },
    { value: "LOW", label: "Low" },
    { value: "MEDIUM", label: "Medium" },
    { value: "HIGH", label: "High" },
];

const formatDateTime = (value: string) => {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;

    return new Intl.DateTimeFormat(undefined, {
        year: "numeric",
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    }).format(date);
};

const campaignEventTimeMs = (event: Event) => Math.round(event.timestamp_ns / 1_000_000);

const campaignEventSummary = (event: Event) =>
    [
        event.event_id,
        event.device_id ?? "",
        event.device_name ?? "",
        event.protocol_name,
        event.protocol_libc_name,
        event.violation_type,
        event.violation_response,
        event.direction,
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

const campaignSearchText = (campaign: Campaign) =>
    [
        campaign.campaign_id,
        campaign.name,
        campaign.description,
        campaign.detailed_description,
        campaign.status,
        campaign.severity,
        campaign.initial_event_time,
        campaign.last_updated,
        campaign.involved_device_ids.join(" "),
        ...campaign.events.map(campaignEventSummary),
    ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

const campaignSearchByScope = (campaign: Campaign, needle: string, scope: SearchScope) => {
    if (!needle) return true;

    const haystack = (() => {
        switch (scope) {
            case "name":
                return `${campaign.name} ${campaign.campaign_id}`;
            case "description":
                return `${campaign.description} ${campaign.detailed_description}`;
            case "device":
                return campaign.involved_device_ids.join(" ");
            case "event":
                return campaign.events.map(campaignEventSummary).join(" ");
            case "status":
                return campaign.status;
            case "severity":
                return campaign.severity;
            case "all":
            default:
                return campaignSearchText(campaign);
        }
    })();

    return haystack.toLowerCase().includes(needle);
};

const campaignStatusTone: Record<Campaign["status"], string> = {
    ONGOING: "bg-highlight/15 text-highlight",
    COMPLETED: "bg-emerald-500/15 text-emerald-300",
    ABORTED: "bg-rose-500/15 text-rose-300",
};

const campaignSeverityTone: Record<Campaign["severity"], string> = {
    LOW: "bg-sky-500/15 text-sky-300",
    MEDIUM: "bg-amber-500/15 text-amber-300",
    HIGH: "bg-rose-500/15 text-rose-300",
};

function CampaignDetailsModal({
    campaign,
    onClose,
    onOpenDevice,
    onOpenEvent,
    onOpenCampaignEvents,
}: {
    campaign: Campaign | null;
    onClose: () => void;
    onOpenDevice: (deviceId: number) => void;
    onOpenEvent: (eventId: number) => void;
    onOpenCampaignEvents: (campaign: Campaign) => void;
}) {
    const recentEvents = React.useMemo(() => {
        if (!campaign) return [];
        return [...campaign.events].sort((a, b) => campaignEventTimeMs(b) - campaignEventTimeMs(a)).slice(0, 6);
    }, [campaign]);

    return (
        <Modal
            isOpen={campaign !== null}
            onClose={onClose}
            title={campaign ? `Campaign ${campaign.campaign_id}` : "Campaign"}
            maxWidthClass="max-w-5xl"
        >
            {campaign && (
                <div className="flex flex-col gap-6">
                    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                        <div className="rounded-md outline outline-secondary bg-background/30 p-4">
                            <p className="text-xs uppercase tracking-wide text-text-gray">Core</p>
                            <div className="mt-3 grid grid-cols-1 gap-2 text-sm">
                                <div className="flex items-center justify-between gap-4">
                                    <span className="text-text-gray">Name</span>
                                    <span className="text-text-secondary text-right">{campaign.name}</span>
                                </div>
                                <div className="flex items-center justify-between gap-4">
                                    <span className="text-text-gray">State</span>
                                    <span
                                        className={`rounded-md px-2 py-1 text-xs font-semibold uppercase tracking-wide ${campaignStatusTone[campaign.status]}`}
                                    >
                                        {campaign.status}
                                    </span>
                                </div>
                                <div className="flex items-center justify-between gap-4">
                                    <span className="text-text-gray">Severity</span>
                                    <span
                                        className={`rounded-md px-2 py-1 text-xs font-semibold uppercase tracking-wide ${campaignSeverityTone[campaign.severity]}`}
                                    >
                                        {campaign.severity}
                                    </span>
                                </div>
                                <div className="flex items-center justify-between gap-4">
                                    <span className="text-text-gray">Started</span>
                                    <span className="text-text-secondary text-right">{formatDateTime(campaign.initial_event_time)}</span>
                                </div>
                                <div className="flex items-center justify-between gap-4">
                                    <span className="text-text-gray">Updated</span>
                                    <span className="text-text-secondary text-right">{formatDateTime(campaign.last_updated)}</span>
                                </div>
                            </div>
                        </div>

                        <div className="rounded-md outline outline-secondary bg-background/30 p-4">
                            <p className="text-xs uppercase tracking-wide text-text-gray">Scope</p>
                            <div className="mt-3 grid grid-cols-1 gap-2 text-sm">
                                <div className="flex items-center justify-between gap-4">
                                    <span className="text-text-gray">Devices</span>
                                    <span className="text-text-secondary">{campaign.involved_device_ids.length}</span>
                                </div>
                                <div className="flex items-center justify-between gap-4">
                                    <span className="text-text-gray">Events</span>
                                    <span className="text-text-secondary">{campaign.events.length}</span>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => onOpenCampaignEvents(campaign)}
                                    disabled={campaign.events.length === 0}
                                    className="mt-2 inline-flex w-fit items-center justify-center rounded-lg bg-highlight/15 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-highlight outline outline-highlight/40 transition-colors hover:bg-highlight/20 disabled:cursor-not-allowed disabled:bg-background/30 disabled:text-text-gray disabled:outline-secondary"
                                >
                                    View campaign events
                                </button>
                                <div className="flex flex-col gap-2">
                                    <span className="text-text-gray">Device IDs</span>
                                    <div className="flex flex-wrap gap-2">
                                        {campaign.involved_device_ids.length > 0 ? (
                                            campaign.involved_device_ids.map((deviceId) => (
                                                <button
                                                    key={deviceId}
                                                    type="button"
                                                    onClick={() => onOpenDevice(deviceId)}
                                                    className="inline-flex items-center rounded-md bg-background/60 px-2 py-1 text-xs text-highlight outline outline-secondary transition-colors hover:bg-background/80"
                                                >
                                                    Device {deviceId}
                                                </button>
                                            ))
                                        ) : (
                                            <span className="text-text-secondary">No linked devices</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                        <div className="rounded-md outline outline-secondary bg-background/30 p-4">
                            <p className="text-xs uppercase tracking-wide text-text-gray">Description</p>
                            <div className="mt-3 space-y-3 text-sm text-text-secondary">
                                <p>{campaign.description}</p>
                                {campaign.detailed_description ? <p className="leading-relaxed">{campaign.detailed_description}</p> : null}
                            </div>
                        </div>

                        <div className="rounded-md outline outline-secondary bg-background/30 p-4">
                            <p className="text-xs uppercase tracking-wide text-text-gray">Latest Event Snapshot</p>
                            <div className="mt-3 flex flex-col gap-3 text-sm text-text-secondary">
                                {recentEvents.length > 0 ? (
                                    recentEvents.slice(0, 3).map((event) => (
                                        <button
                                            key={event.event_id}
                                            type="button"
                                            onClick={() => onOpenEvent(event.event_id)}
                                            className="rounded-md bg-background/30 p-3 text-left outline outline-secondary transition-colors hover:bg-background/45"
                                        >
                                            <div className="flex items-center justify-between gap-4">
                                                <span className="text-text-primary">Event {event.event_id}</span>
                                                <span className="text-xs uppercase tracking-wide text-text-gray">
                                                    {formatDateTime(
                                                        event.timestamp ? event.timestamp : new Date(campaignEventTimeMs(event)).toISOString(),
                                                    )}
                                                </span>
                                            </div>
                                            <p className="mt-2 text-xs text-text-gray truncate">
                                                {event.source.ip}:{event.source.port} → {event.dest.ip}:{event.dest.port} • {event.protocol_name}
                                            </p>
                                        </button>
                                    ))
                                ) : (
                                    <p>No events attached to this campaign.</p>
                                )}
                            </div>
                        </div>
                    </div>

                    <div>
                        <p className="text-xs uppercase tracking-wide text-text-gray">Recent Events</p>
                        <div className="mt-3">
                            <SimpleTable
                                emptyText="No events available"
                                rows={recentEvents}
                                getRowKey={(event) => event.event_id}
                                onRowClick={(event) => onOpenEvent(event.event_id)}
                                columns={[
                                    {
                                        key: "time",
                                        header: "Time",
                                        className: "w-48",
                                        render: (event) => (
                                            <span className="text-sm text-text-secondary">
                                                {formatDateTime(
                                                    event.timestamp ? event.timestamp : new Date(campaignEventTimeMs(event)).toISOString(),
                                                )}
                                            </span>
                                        ),
                                    },
                                    {
                                        key: "device",
                                        header: "Device",
                                        className: "w-40",
                                        render: (event) => (
                                            <span className="text-sm text-text-primary">{event.device_name || event.device_id || "—"}</span>
                                        ),
                                    },
                                    {
                                        key: "flow",
                                        header: "Flow",
                                        render: (event) => (
                                            <div className="min-w-0">
                                                <p className="text-text-primary truncate">
                                                    {event.source.ip}:{event.source.port} → {event.dest.ip}:{event.dest.port}
                                                </p>
                                                <p className="mt-1 text-xs text-text-gray truncate">
                                                    {event.protocol_name} • {event.direction}
                                                </p>
                                            </div>
                                        ),
                                    },
                                    {
                                        key: "violation",
                                        header: "Violation",
                                        className: "w-40",
                                        render: (event) => (
                                            <div className="min-w-0">
                                                <p className="text-text-primary truncate">{event.violation_type}</p>
                                                <p className="mt-1 text-xs text-text-gray truncate">{event.violation_response}</p>
                                            </div>
                                        ),
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

export default function Campaigns() {
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();
    const [campaigns, setCampaigns] = React.useState<Campaign[]>([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState<string | null>(null);
    const [search, setSearch] = React.useState("");
    const [searchScope, setSearchScope] = React.useState<SearchScope>("all");
    const [statusFilter, setStatusFilter] = React.useState<CampaignStatusFilter>("all");
    const [severityFilter, setSeverityFilter] = React.useState<CampaignSeverityFilter>("all");
    const [selectedCampaign, setSelectedCampaign] = React.useState<Campaign | null>(null);

    const load = React.useCallback(async () => {
        setLoading(true);
        setError(null);

        const res = await APIManager.listCampaigns();
        if (res.success && res.data) {
            setCampaigns((res.data.campaigns ?? []).slice().sort((a, b) => new Date(b.last_updated).getTime() - new Date(a.last_updated).getTime()));
        } else {
            setCampaigns([]);
            setError(res.message || "Failed to load campaigns");
        }

        setLoading(false);
    }, []);

    React.useEffect(() => {
        load();
    }, [load]);

    React.useEffect(() => {
        const campaignIdParam = searchParams.get("campaign_id");
        if (!campaignIdParam) return;

        const campaignId = Number(campaignIdParam);
        if (!Number.isFinite(campaignId)) return;

        const match = campaigns.find((campaign) => campaign.campaign_id === campaignId);
        if (match) {
            setSelectedCampaign(match);
        }
    }, [campaigns, searchParams]);

    const filteredCampaigns = React.useMemo(() => {
        const needle = search.trim().toLowerCase();

        return campaigns.filter((campaign) => {
            if (statusFilter !== "all" && campaign.status !== statusFilter) return false;
            if (severityFilter !== "all" && campaign.severity !== severityFilter) return false;
            if (needle && !campaignSearchByScope(campaign, needle, searchScope)) return false;
            return true;
        });
    }, [campaigns, search, searchScope, severityFilter, statusFilter]);

    const summary = React.useMemo(() => {
        const ongoing = campaigns.filter((campaign) => campaign.status === "ONGOING").length;
        const completed = campaigns.filter((campaign) => campaign.status === "COMPLETED").length;
        const aborted = campaigns.filter((campaign) => campaign.status === "ABORTED").length;

        return { total: campaigns.length, ongoing, completed, aborted };
    }, [campaigns]);

    const campaignColumns = React.useMemo(
        () => [
            {
                key: "campaign",
                header: "Campaign",
                render: (campaign: Campaign) => (
                    <div className="min-w-0">
                        <div className="flex items-center gap-3 min-w-0">
                            <p className="font-medium text-text-primary truncate">{campaign.name}</p>
                            <span
                                className={`inline-flex items-center rounded-md px-2 py-1 text-[11px] font-semibold uppercase tracking-wide ${campaignStatusTone[campaign.status]}`}
                            >
                                {campaign.status}
                            </span>
                        </div>
                        <p className="mt-1 text-xs text-text-gray truncate">{campaign.description}</p>
                    </div>
                ),
            },
            {
                key: "severity",
                header: "Severity",
                className: "w-28",
                render: (campaign: Campaign) => (
                    <span
                        className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-semibold uppercase tracking-wide ${campaignSeverityTone[campaign.severity]}`}
                    >
                        {campaign.severity}
                    </span>
                ),
            },
            {
                key: "devices",
                header: "Devices",
                className: "w-24",
                render: (campaign: Campaign) => <span className="text-sm text-text-secondary">{campaign.involved_device_ids.length}</span>,
            },
            {
                key: "events",
                header: "Events",
                className: "w-24",
                render: (campaign: Campaign) => <span className="text-sm text-text-secondary">{campaign.events.length}</span>,
            },
            {
                key: "updated",
                header: "Last Updated",
                className: "w-44",
                render: (campaign: Campaign) => <span className="text-sm text-text-secondary">{formatDateTime(campaign.last_updated)}</span>,
            },
        ],
        [],
    );

    const clearFilters = () => {
        setSearch("");
        setSearchScope("all");
        setStatusFilter("all");
        setSeverityFilter("all");
    };

    const openDevice = (deviceId: number) => {
        navigate(`/dashboard/devices?device_id=${deviceId}`);
    };

    const openEvent = (eventId: number) => {
        navigate(`/dashboard/events?event_id=${eventId}`);
    };

    const openCampaignEvents = (campaign: Campaign) => {
        const eventIds = [...new Set(campaign.events.map((event) => event.event_id).filter((eventId) => Number.isFinite(eventId)))];
        if (eventIds.length === 0) return;

        const params = new URLSearchParams();
        params.set("campaign_id", String(campaign.campaign_id));
        params.set("event_ids", eventIds.join(","));
        navigate(`/dashboard/events?${params.toString()}`);
    };

    const closeCampaignDetails = () => {
        setSelectedCampaign(null);
        setSearchParams({}, { replace: true });
    };

    return (
        <div className="h-full min-h-0 overflow-y-auto">
            <div className="px-6 py-6">
                <div className="flex items-start justify-between gap-6">
                    <div className="min-w-0">
                        <p className="text-xs uppercase tracking-wide text-text-gray">Dashboard</p>
                        <h1 className="mt-1 text-2xl font-semibold text-text-primary">Campaigns</h1>
                        <p className="mt-2 text-sm text-text-secondary">
                            A searchable view of all campaigns with state-aware filtering and a detail view for each campaign.
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
                            <p className="text-sm text-text-secondary">Loading campaigns…</p>
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
                            <StatCard label="All Campaigns" value={summary.total} icon={<SquareStack size={22} />} />
                            <StatCard label="Ongoing" value={summary.ongoing} icon={<Clock3 size={22} />} />
                            <StatCard label="Completed" value={summary.completed} icon={<CheckCircle2 size={22} />} />
                            <StatCard label="Aborted" value={summary.aborted} icon={<XCircle size={22} />} />
                        </div>

                        <div className="mt-6 grid grid-cols-1 gap-6">
                            <SectionCard
                                title="Campaign Filters"
                                right={
                                    <span className="text-xs uppercase tracking-wide text-text-gray">
                                        {filteredCampaigns.length} matching campaigns
                                    </span>
                                }
                            >
                                <SearchFilters
                                    search={search}
                                    onSearchChange={setSearch}
                                    searchPlaceholder="Search by campaign name, description, state, device, or event data"
                                    searchHelperText="Search is global by default, but you can narrow it to a field when you need a tighter slice."
                                    scopeLabel="Scope"
                                    scopeValue={searchScope}
                                    onScopeChange={setSearchScope}
                                    scopeOptions={searchScopeOptions}
                                    secondaryLabel="State"
                                    secondaryValue={statusFilter}
                                    onSecondaryChange={setStatusFilter}
                                    secondaryOptions={statusOptions}
                                    secondaryHelperText="Use state to keep the list aligned with the campaign lifecycle."
                                    resultText={`${filteredCampaigns.length} of ${summary.total}`}
                                    clearLabel="Clear"
                                    onClear={clearFilters}
                                />

                                <div className="mt-4 flex flex-wrap gap-2">
                                    {severityOptions.slice(1).map((option) => (
                                        <button
                                            key={option.value}
                                            type="button"
                                            onClick={() =>
                                                setSeverityFilter(
                                                    (option.value as CampaignSeverityFilter) === severityFilter
                                                        ? "all"
                                                        : (option.value as CampaignSeverityFilter),
                                                )
                                            }
                                            className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide outline transition-colors ${
                                                severityFilter === option.value
                                                    ? "bg-highlight/15 text-highlight outline-highlight/40"
                                                    : "bg-background/30 text-text-gray outline-secondary hover:bg-background/45"
                                            }`}
                                        >
                                            {option.label}
                                        </button>
                                    ))}
                                    {severityFilter !== "all" && (
                                        <button
                                            type="button"
                                            onClick={() => setSeverityFilter("all")}
                                            className="rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide text-text-secondary outline outline-secondary hover:bg-background/45"
                                        >
                                            Reset severity
                                        </button>
                                    )}
                                </div>
                            </SectionCard>

                            <SectionCard
                                title="Campaigns"
                                right={<span className="text-xs uppercase tracking-wide text-text-gray">Click any campaign for details</span>}
                            >
                                <SimpleTable
                                    emptyText="No campaigns match the current filters"
                                    rows={filteredCampaigns}
                                    getRowKey={(campaign) => campaign.campaign_id}
                                    onRowClick={(campaign) => {
                                        navigate(`/dashboard/campaigns?campaign_id=${campaign.campaign_id}`);
                                        setSelectedCampaign(campaign);
                                    }}
                                    columns={campaignColumns}
                                />
                            </SectionCard>
                        </div>
                    </>
                )}
            </div>

            <CampaignDetailsModal
                campaign={selectedCampaign}
                onClose={closeCampaignDetails}
                onOpenDevice={openDevice}
                onOpenEvent={openEvent}
                onOpenCampaignEvents={openCampaignEvents}
            />
        </div>
    );
}
