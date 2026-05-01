export interface Event {
    event_id: number;
    protocol: string;
    timestamp_ns: number;
    violated_rule_id: number;
    violation_type: string;
    violation_response: string;
    is_connection_establishing: boolean;
    direction: "inbound" | "outbound";
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
    status: "ongoing" | "completed" | "aborted";
    severity: "low" | "medium" | "high";
    initial_event_time: string; // ISO date string
    last_updated: string; // ISO date string
    involved_device_ids: number[];
    events: Event[];
}

export interface Notification {
    notification_id: number;
    message: string;
    type: "info" | "warning" | "danger";
    created_at: string; // ISO date string
}