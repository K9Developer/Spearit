import { API_BASE_URL } from "@/constants";
import { useUser, type User } from "@/context/User";
import type { Campaign } from "./types";

interface APIResponse {
    success: boolean;
    message: string;
    data?: any;
}

/*data = {
        "registered_devices": 0,
        "alerts_24h": 0,
        "critical_campaigns": 0,
        "baseline_deviations": 0,
        "rule_violations_ph": 0, # per hour
        "active_campaigns": [],
        "alerts": [],
        "event_stats": {
            "top_noisy_devices": [],
            "10_min_interval_counts": []
        },
        "recently_changed_rules": [],
        "system_health": {
            "spearhead_status": "OK",
            "wrappers_connected_precentage": -1,
            "last_heartbeat_age": -1
        }
    } */
interface APIOverviewDataResponse extends APIResponse {
    data?: {
        registered_devices: number;
        alerts_24h: number;
        critical_campaigns: number;
        baseline_deviations: number;
        rule_violations_ph: number;
        active_campaigns: Campaign[];
        alerts: Notification[];
        event_stats: {
            top_noisy_devices: {
                device_id: number;
                device_name: string;
                event_count: number;
            }[];
            "10_min_interval_counts": {
                start: string; // ISO date string
                end: string; // ISO date string
                count: number;
            }[];
        };
        recently_changed_rules: {
            rule_id: number;
            rule_name: string;
            last_updated: string; // ISO date string
        }[];
        system_health: {
            spearhead_status: string;
            wrappers_connected_precentage: number;
            last_heartbeat_age: number;
        };
    };
}

export default class APIManager {
    private static async request(endpoint: string, data: any, method: string = "GET"): Promise<APIResponse> {
        try {
            const token = localStorage.getItem("token");
            if (token) {
                data.token = token;
            }
            console.log(`Making API request to ${API_BASE_URL}${endpoint} with data:`, data);
            const res = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: method,
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify(data),
            });

            const resData = await res.json();
            if (resData?.message === "Invalid or expired token") {
                localStorage.removeItem("token");
                window.location.href = "/";
                return { success: false, message: "Session expired. Please log in again." };
            }
            if (!res.ok) {
                return { success: false, message: resData.message || "Request Failed" };
            }

            return { success: resData?.status != "error", message: resData.message || "", data: resData.data };
        } catch (error) {
            return {
                success: false,
                message: error instanceof Error ? error.message : "An unknown error occurred",
            };
        }
    }
    
    static async loginWithCredentials(email: string, password: string, userContextLogin: (user: User) => void): Promise<APIResponse> {
        const res = await this.request("/users/login_user_credentials", { email, password }, "POST");
        if (!res.data?.token) {
            return { success: false, message: "Invalid credentials" };
        }
        console.log("Login successful, received token:", res.data.token);
        localStorage.setItem("token", res.data.token);
        
        userContextLogin({
            id: res.data.user.id,
            fullname: res.data.user.fullname,
            email: res.data.user.email,
        })

        return res;
    }

    static async loginWithToken(userContextLogin: (user: User) => void): Promise<APIResponse> {
        const res = await this.request("/users/login_user_token", {}, "POST");
        if (res.success && res.data?.token) {
            localStorage.setItem("token", res.data.token);
            userContextLogin({
                id: res.data.user.id,
                fullname: res.data.user.fullname,
                email: res.data.user.email,
            });
        }
        return res;
    }

    static async getOverviewData(): Promise<APIOverviewDataResponse> {
        return await this.request("/overview", {}, "POST");
    }
}