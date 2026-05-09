import React from "react";
import ReactFlow, {
    Background,
    BackgroundVariant,
    Controls,
    MiniMap,
    type Edge,
    type EdgeProps,
    MarkerType,
    type Node,
    type NodeProps,
    Handle,
    Position,
    Panel,
    EdgeLabelRenderer,
    BaseEdge,
} from "reactflow";
import "reactflow/dist/style.css";

import type { Device } from "@/utils/types";

export type DeviceConnection = {
    from_device_id: number;
    to_device_id: number;
    count?: number;
};

type DeviceGroup = "known" | "unknown";

type DeviceNodeData = {
    deviceId: number;
    label: string;
    ip: string | null;
    unknown: boolean;
    group: DeviceGroup;
    row: number;
};

type DeviceEdgeData = {
    count?: number;
    midX?: number;
};

const isUnknownIp = (ip: string | null) => !ip || ip === "0.0.0.0";

const NODE_W = 250;
const NODE_H = 95;
const GAP_Y = 56;
const COLUMN_GAP = 260;
const SAME_COLUMN_EDGE_OFFSET = 90;
const EXTRA_EDGE_LANE_GAP = 10;

const KNOWN_X = 0;
const UNKNOWN_X = NODE_W + COLUMN_GAP;

const HIDDEN_HANDLE_CLASS = "!opacity-0 !pointer-events-none !w-px !h-px !min-w-0 !min-h-0 !bg-transparent !border-0";

// ─── Node ────────────────────────────────────────────────────────────────────

const DeviceNode = ({ data }: NodeProps<DeviceNodeData>) => {
    return (
        <div
            className={[
                "rounded-lg px-3 py-2.5 transition-colors duration-150 cursor-pointer select-none",
                "border",
                data.unknown ? "bg-secondary border-secondary opacity-70" : "bg-background border-secondary shadow-sm hover:border-primary",
            ].join(" ")}
            style={{ width: NODE_W, minHeight: NODE_H }}
        >
            <Handle id="target-left" type="target" position={Position.Left} className={HIDDEN_HANDLE_CLASS} />
            <Handle id="source-left" type="source" position={Position.Left} className={HIDDEN_HANDLE_CLASS} />

            <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-text-primary truncate m-0">{data.label}</p>
                    <p className="text-[11px] text-text-tertiary mt-0.5 m-0 tabular-nums">ID {data.deviceId}</p>
                </div>

                {data.unknown && (
                    <span className="shrink-0 inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium tracking-wide uppercase bg-secondary text-text-secondary border border-secondary">
                        External
                    </span>
                )}
            </div>

            <div className="mt-2 pt-2 border-t border-secondary flex items-center gap-1.5">
                <span className={["w-1.5 h-1.5 rounded-full shrink-0", data.unknown || !data.ip ? "bg-text-tertiary" : "bg-success"].join(" ")} />
                <p className="text-[11px] text-text-secondary m-0 truncate font-mono tabular-nums">
                    {data.ip && data.ip !== "0.0.0.0" ? data.ip : "Unknown IP"}
                </p>
            </div>

            <Handle id="target-right" type="target" position={Position.Right} className={HIDDEN_HANDLE_CLASS} />
            <Handle id="source-right" type="source" position={Position.Right} className={HIDDEN_HANDLE_CLASS} />
        </div>
    );
};

// ─── Edge ────────────────────────────────────────────────────────────────────

const countToStrokeWidth = (count: number | undefined): number => {
    if (!count || count <= 1) return 1.5;
    return Math.min(5, 1.5 + Math.log2(count) * 0.75);
};

const EDGE_COLOR = "#94a3b8";
const EDGE_HOVER_COLOR = "#475569";

const DeviceEdge = ({ id, sourceX, sourceY, targetX, targetY, data, markerEnd, selected }: EdgeProps<DeviceEdgeData>) => {
    const [hovered, setHovered] = React.useState(false);
    const [pinned, setPinned] = React.useState(false);

    const fallbackMidX = sourceX === targetX ? sourceX + SAME_COLUMN_EDGE_OFFSET : sourceX + (targetX - sourceX) / 2;

    const midX = data?.midX ?? fallbackMidX;

    const edgePath = [`M ${sourceX},${sourceY}`, `L ${midX},${sourceY}`, `L ${midX},${targetY}`, `L ${targetX},${targetY}`].join(" ");

    const labelX = midX;
    const labelY = sourceY + (targetY - sourceY) / 2;

    const strokeWidth = countToStrokeWidth(data?.count);
    const hasCount = typeof data?.count === "number";
    const active = hovered || pinned || selected;

    return (
        <>
            <BaseEdge
                id={id}
                path={edgePath}
                markerEnd={markerEnd}
                style={{
                    stroke: active ? EDGE_HOVER_COLOR : EDGE_COLOR,
                    strokeWidth: active ? strokeWidth + 0.5 : strokeWidth,
                    transition: "stroke 120ms ease, stroke-width 120ms ease",
                    pointerEvents: "none",
                }}
            />

            <path
                className="react-flow__edge-interaction"
                d={edgePath}
                fill="none"
                stroke="rgba(0,0,0,0.001)"
                strokeWidth={10}
                pointerEvents="stroke"
                onPointerEnter={() => setHovered(true)}
                onPointerLeave={() => setHovered(false)}
                onClick={(event) => {
                    if (!hasCount) return;
                    event.stopPropagation();
                    setPinned((value) => !value);
                }}
                style={{
                    cursor: hasCount ? "pointer" : "default",
                }}
            />

            {hasCount && active && (
                <EdgeLabelRenderer>
                    <div
                        className="nodrag nopan"
                        style={{
                            position: "absolute",
                            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
                            pointerEvents: "none",
                            zIndex: 1000,
                        }}
                    >
                        <span
                            style={{
                                display: "inline-block",
                                fontSize: 11,
                                fontWeight: 500,
                                lineHeight: 1.4,
                                padding: "3px 8px",
                                borderRadius: 5,
                                background: "#1e293b",
                                color: "#f1f5f9",
                                whiteSpace: "nowrap",
                                boxShadow: "0 1px 4px rgba(0,0,0,0.25)",
                            }}
                        >
                            {data!.count} communication{data!.count !== 1 ? "s" : ""}
                        </span>
                    </div>
                </EdgeLabelRenderer>
            )}
        </>
    );
};

// ─── Types registry ──────────────────────────────────────────────────────────

const nodeTypes = { device: DeviceNode };
const edgeTypes = { device: DeviceEdge };

// ─── Layout helper ───────────────────────────────────────────────────────────

const getDeviceDegreeMap = (connections: DeviceConnection[]) => {
    const map = new Map<number, number>();

    for (const connection of connections) {
        const count = connection.count ?? 1;

        map.set(connection.from_device_id, (map.get(connection.from_device_id) ?? 0) + count);
        map.set(connection.to_device_id, (map.get(connection.to_device_id) ?? 0) + count);
    }

    return map;
};

const sortDevicesForMap = (devices: Device[], degreeMap: Map<number, number>) => {
    return [...devices].sort((a, b) => {
        const degreeDiff = (degreeMap.get(b.device_id) ?? 0) - (degreeMap.get(a.device_id) ?? 0);
        if (degreeDiff !== 0) return degreeDiff;

        const nameA = a.device_name || "";
        const nameB = b.device_name || "";
        const nameDiff = nameA.localeCompare(nameB);
        if (nameDiff !== 0) return nameDiff;

        return a.device_id - b.device_id;
    });
};

const layoutColumn = (list: Device[], group: DeviceGroup, x: number, yOffset: number): Node<DeviceNodeData>[] => {
    return list.map((device, row) => ({
        id: String(device.device_id),
        type: "device",
        zIndex: 1,
        position: {
            x,
            y: yOffset + row * (NODE_H + GAP_Y),
        },
        data: {
            deviceId: device.device_id,
            label: device.device_name || "(unnamed)",
            ip: device.last_known_ip_address,
            unknown: isUnknownIp(device.last_known_ip_address),
            group,
            row,
        },
    }));
};

const getColumnHeight = (count: number) => {
    if (count <= 0) return 0;
    return count * NODE_H + Math.max(0, count - 1) * GAP_Y;
};

// ─── Props ───────────────────────────────────────────────────────────────────

interface Props {
    devices: Device[];
    connections: DeviceConnection[];
    onDeviceClick: (deviceId: number) => void;
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function DeviceMap({ devices, connections, onDeviceClick }: Props) {
    const { nodes, edges } = React.useMemo(() => {
        const deviceIdSet = new Set(devices.map((device) => device.device_id));
        const degreeMap = getDeviceDegreeMap(connections);

        const known = sortDevicesForMap(
            devices.filter((device) => !isUnknownIp(device.last_known_ip_address)),
            degreeMap,
        );

        const unknown = sortDevicesForMap(
            devices.filter((device) => isUnknownIp(device.last_known_ip_address)),
            degreeMap,
        );

        const knownHeight = getColumnHeight(known.length);
        const unknownHeight = getColumnHeight(unknown.length);
        const totalHeight = Math.max(knownHeight, unknownHeight);

        const knownYOffset = Math.max(0, (totalHeight - knownHeight) / 2) + 80;
        const unknownYOffset = Math.max(0, (totalHeight - unknownHeight) / 2) + 80;

        const knownNodes = layoutColumn(known, "known", KNOWN_X, knownYOffset);
        const unknownNodes = layoutColumn(unknown, "unknown", UNKNOWN_X, unknownYOffset);

        const all = [...knownNodes, ...unknownNodes];
        const nodeById = new Map(all.map((node) => [node.id, node]));

        const mergedConnections = new Map<string, DeviceConnection>();

        for (const connection of connections) {
            if (
                !deviceIdSet.has(connection.from_device_id) ||
                !deviceIdSet.has(connection.to_device_id) ||
                connection.from_device_id === connection.to_device_id
            ) {
                continue;
            }

            const key = `${connection.from_device_id}->${connection.to_device_id}`;
            const existing = mergedConnections.get(key);

            if (!existing) {
                mergedConnections.set(key, {
                    ...connection,
                    count: connection.count ?? 1,
                });
                continue;
            }

            existing.count = (existing.count ?? 1) + (connection.count ?? 1);
        }

        const edgeList: Edge<DeviceEdgeData>[] = Array.from(mergedConnections.values()).map((connection, index) => {
            const sourceNode = nodeById.get(String(connection.from_device_id));
            const targetNode = nodeById.get(String(connection.to_device_id));

            let sourceHandle = "source-right";
            let targetHandle = "target-left";
            let midX = KNOWN_X + NODE_W + COLUMN_GAP / 2;

            if (sourceNode && targetNode) {
                const sourceGroup = sourceNode.data.group;
                const targetGroup = targetNode.data.group;

                if (sourceGroup === "known" && targetGroup === "unknown") {
                    sourceHandle = "source-right";
                    targetHandle = "target-left";
                    midX = KNOWN_X + NODE_W + COLUMN_GAP / 2;
                } else if (sourceGroup === "unknown" && targetGroup === "known") {
                    sourceHandle = "source-left";
                    targetHandle = "target-right";
                    midX = KNOWN_X + NODE_W + COLUMN_GAP / 2;
                } else if (sourceGroup === "known" && targetGroup === "known") {
                    sourceHandle = "source-right";
                    targetHandle = "target-right";
                    midX = KNOWN_X + NODE_W + SAME_COLUMN_EDGE_OFFSET + (index % 6) * EXTRA_EDGE_LANE_GAP;
                } else {
                    sourceHandle = "source-right";
                    targetHandle = "target-right";
                    midX = UNKNOWN_X + NODE_W + SAME_COLUMN_EDGE_OFFSET + (index % 6) * EXTRA_EDGE_LANE_GAP;
                }
            }

            return {
                id: `e-${connection.from_device_id}-${connection.to_device_id}-${index}`,
                source: String(connection.from_device_id),
                target: String(connection.to_device_id),
                sourceHandle,
                targetHandle,
                type: "device",
                data: {
                    count: connection.count,
                    midX,
                },
                markerEnd: {
                    type: MarkerType.ArrowClosed,
                    color: EDGE_COLOR,
                    width: 16,
                    height: 16,
                },
            };
        });

        return { nodes: all, edges: edgeList };
    }, [devices, connections]);

    const knownCount = devices.filter((device) => !isUnknownIp(device.last_known_ip_address)).length;
    const unknownCount = devices.length - knownCount;

    return (
        <div className="w-full flex flex-col h-full">
            {/* Header */}
            <div className="flex items-center justify-between gap-3 px-3.5 py-2.5 bg-secondary border border-secondary rounded-t-lg">
                <div className="flex items-center gap-2">
                    <span className="text-xs font-medium uppercase tracking-widest text-text-secondary">Device Map</span>
                    <span className="text-[11px] text-text-tertiary bg-background border border-secondary rounded px-2 py-0.5">
                        {devices.length} device{devices.length !== 1 ? "s" : ""}
                    </span>
                </div>

                <div className="flex items-center gap-4">
                    <span className="flex items-center gap-1.5 text-xs text-text-secondary">
                        <span className="w-2 h-2 rounded-full bg-success shrink-0" />
                        Internal ({knownCount})
                    </span>
                    <span className="flex items-center gap-1.5 text-xs text-text-secondary">
                        <span className="w-2 h-2 rounded-full bg-text-tertiary shrink-0" />
                        External ({unknownCount})
                    </span>
                </div>
            </div>

            {/* Graph canvas */}
            <div className="border border-t-0 border-secondary rounded-b-lg overflow-hidden bg-background h-[80%]">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    nodeTypes={nodeTypes}
                    edgeTypes={edgeTypes}
                    fitView
                    fitViewOptions={{ padding: 0.22, minZoom: 0.2, maxZoom: 1.5 }}
                    minZoom={0.1}
                    maxZoom={2}
                    onNodeClick={(_, node) => {
                        const id = Number(node.id);
                        if (Number.isFinite(id)) onDeviceClick(id);
                    }}
                    proOptions={{ hideAttribution: true }}
                    elevateEdgesOnSelect={false}
                    elevateNodesOnSelect={false}
                    nodesDraggable
                    elementsSelectable
                >
                    <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="#cbd5e1" style={{ opacity: 0.5 }} />

                    <MiniMap
                        zoomable
                        pannable
                        nodeColor={(node) => (node.data?.unknown ? "#94a3b8" : "#22c55e")}
                        maskColor="rgba(0,0,0,0.03)"
                        className="border border-secondary rounded-md !bg-secondary"
                    />

                    <Controls className="border border-secondary rounded-md overflow-hidden !shadow-none" />

                    {knownCount > 0 && unknownCount > 0 && (
                        <Panel position="top-center">
                            <p className="text-[11px] text-text-tertiary select-none pointer-events-none flex items-center gap-2">
                                <span className="inline-block w-6 h-px bg-secondary" />
                                internal · external
                                <span className="inline-block w-6 h-px bg-secondary" />
                            </p>
                        </Panel>
                    )}
                </ReactFlow>
            </div>
        </div>
    );
}
