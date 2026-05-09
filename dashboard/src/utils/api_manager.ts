import { API_BASE_URL } from "@/constants";
import { type User } from "@/context/userTypes";
import type { Campaign, Device, Event, ManagedUser, Notification, Permission } from "./types";

export interface APIResponse<TData = unknown> {
    success: boolean;
    message: string;
    data?: TData;
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
export interface APIOverviewDataResponse extends APIResponse {
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
                start: string;
                end: string;
                count: number;
            }[];
        };
        recently_changed_rules: {
            rule_id: number;
            rule_name: string;
            last_updated: string;
        }[];
        system_health: {
            spearhead_status: string;
            wrappers_connected_precentage: number;
            last_heartbeat_age: number;
        };
    };
}

export type OverviewData = NonNullable<APIOverviewDataResponse["data"]>;

export type UserManagementMetadata = {
    permission_types: Record<string, string>;
    group_ids: Record<string, string>;
    device_ids: Record<string, string>;
    handler_ids?: Record<string, string>;
};

export type APIUserManagementMetadataResponse = APIResponse<UserManagementMetadata>;

export type UsersListData = {
    users: ManagedUser[];
};

export type APIUsersListResponse = APIResponse<UsersListData>;

export type DevicesListData = {
    devices: Device[];
};

export type APIDevicesListResponse = APIResponse<DevicesListData>;

export type DeviceDetailsData = {
    device: Device;
    events: Event[];
    campaigns: Campaign[];
};

export type APIDeviceDetailsResponse = APIResponse<DeviceDetailsData>;

export type UpdateDeviceData = {
    device: Device;
};

export type APIUpdateDeviceResponse = APIResponse<UpdateDeviceData>;

export type DeviceCommunicationMapData = {
    connections: {
        from_device_id: number;
        to_device_id: number;
        count?: number;
    }[];
};

export type APIDeviceCommunicationMapResponse = APIResponse<DeviceCommunicationMapData>;

export type UserData = {
    user: ManagedUser;
};

export type APIUserResponse = APIResponse<UserData>;

type LoginResponse = APIResponse<{
    token: string;
    user: User;
}>;

export default class APIManager {
    private static async request<TData = unknown>(
        endpoint: string,
        data: Record<string, unknown> = {},
        method: string = "GET",
    ): Promise<APIResponse<TData>> {
        try {
            const token = localStorage.getItem("token");
            const payload: Record<string, unknown> = { ...data };
            if (token) {
                payload.token = token;
            }
            console.log(`Making API request to ${API_BASE_URL}${endpoint} with data:`, payload);
            const res = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: method,
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify(payload),
            });

            const resData = await res.json();
            if (resData?.message === "Invalid or expired token") {
                localStorage.removeItem("token");
                window.location.href = "/";
                return { success: false, message: "Session expired. Please log in again." } as APIResponse<TData>;
            }
            if (!res.ok) {
                return { success: false, message: resData.message || "Request Failed" } as APIResponse<TData>;
            }

            return {
                success: resData?.status != "error",
                message: resData.message || "",
                data: resData.data as TData,
            };
        } catch (error) {
            return {
                success: false,
                message: error instanceof Error ? error.message : "An unknown error occurred",
            } as APIResponse<TData>;
        }
    }
    
    static async loginWithCredentials(email: string, password: string, userContextLogin: (user: User) => void): Promise<APIResponse> {
        const res = await this.request<LoginResponse["data"]>("/users/login_user_credentials", { email, password }, "POST");
        if (!res.data?.token || !res.data.user) {
            return { success: false, message: "Invalid credentials" };
        }
        console.log("Login successful, received token:", res.data.token);
        localStorage.setItem("token", res.data.token);
        
        userContextLogin({
            id: res.data.user.id,
            fullname: res.data.user.fullname,
            email: res.data.user.email,
            permissions: (res.data.user.permissions ?? []) as Permission[],
        })

        return res;
    }

    static async loginWithToken(userContextLogin: (user: User) => void): Promise<APIResponse> {
        const res = await this.request<LoginResponse["data"]>("/users/login_user_token", {}, "POST");
        if (res.success && res.data?.token && res.data.user) {
            localStorage.setItem("token", res.data.token);
            userContextLogin({
                id: res.data.user.id,
                fullname: res.data.user.fullname,
                email: res.data.user.email,
                permissions: (res.data.user.permissions ?? []) as Permission[],
            });
        }
        return res;
    }

    static async getOverviewData(): Promise<APIOverviewDataResponse> {
        return await this.request<APIOverviewDataResponse["data"]>("/overview", {}, "POST");
    }

    static async getUserManagementMetadata(): Promise<APIUserManagementMetadataResponse> {
        return await this.request<UserManagementMetadata>("/users/metadata", {}, "POST");
    }

    static async listUsers(): Promise<APIUsersListResponse> {
        return await this.request<UsersListData>("/users/list", {}, "POST");
    }

    static async createUser(email: string, temporaryPassword: string, permissions: Permission[]): Promise<APIUserResponse> {
        return await this.request<UserData>(
            "/users/create",
            { email, temporary_password: temporaryPassword, permissions },
            "POST",
        );
    }

    static async updateUserPermissions(userId: number, permissions: Permission[]): Promise<APIUserResponse> {
        return await this.request<UserData>("/users/update_permissions", { user_id: userId, permissions }, "POST");
    }

    static async setUserPassword(userId: number, newPassword: string): Promise<APIResponse> {
        return await this.request("/users/set_password", { user_id: userId, new_password: newPassword }, "POST");
    }

    static async deleteUser(userId: number): Promise<APIResponse> {
        return await this.request("/users/delete", { user_id: userId }, "POST");
    }

    static async listDevices(): Promise<APIDevicesListResponse> {
        return await this.request<DevicesListData>("/devices/list", {}, "POST");
    }

    static async getDeviceDetails(deviceId: number): Promise<APIDeviceDetailsResponse> {
        return await this.request<DeviceDetailsData>("/devices/details", { device_id: deviceId }, "POST");
    }

    static async updateDevice(deviceId: number, update: { device_name?: string | null; groups?: number[]; handlers?: number[] | null }): Promise<APIUpdateDeviceResponse> {
        return await this.request<UpdateDeviceData>(
            "/devices/update",
            {
                device_id: deviceId,
                ...update,
            },
            "POST",
        );
    }

    static async getDeviceCommunicationMap(): Promise<APIDeviceCommunicationMapResponse> {
        return await this.request<DeviceCommunicationMapData>("/devices/communication_map", {}, "POST");
    }
}