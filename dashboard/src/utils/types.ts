export interface Event {
    event_id: number;
    protocol_name: string;
    protocol_libc_name: string;
    timestamp_ns: number;
    violated_rule_id: number;
    violation_type: string;
    violation_response: string;
    is_connection_establishing: boolean;
    direction: "INBOUND" | "OUTBOUND";
    process: {
        process_id: number;
        name: string;
    };
    source: {
        ip: string;
        port: number;
        mac: string;
    };
    dest: {
        ip: string;
        port: number;
        mac: string;
    };
    payload: {
        full_size: number;
        data: string; // base64 encoded
    };
}

export interface Campaign {
    campaign_id: number;
    name: string;
    description: string;
    detailed_description: string;
    status: "ONGOING" | "COMPLETED" | "ABORTED";
    severity: "LOW" | "MEDIUM" | "HIGH";
    initial_event_time: string;
    last_updated: string;
    involved_device_ids: number[];
    events: Event[];
}

export interface Notification {
    notification_id: number;
    message: string;
    type: "info" | "warning" | "danger";
    created_at: string; // ISO date string
}

export interface Permission {
    type: string;
    affected_groups: number[];
    affected_devices: number[];
    affected_handlers?: number[];
}

export interface ManagedUser {
    id: number;
    fullname: string;
    email: string;
    permissions: Permission[];
}

export interface Device {
    device_id: number;
    device_name: string | null;
    operating_system_details: string | null;
    last_known_ip_address: string | null;
    mac_address: string;
    handlers: number[] | null;
    note: string | null;
    groups: number[];
    last_heartbeat_id: number | null;
}