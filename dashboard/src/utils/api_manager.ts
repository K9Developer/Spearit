import { API_BASE_URL } from "@/constants";
import { useUser, type User } from "@/context/User";

interface APIResponse {
    success: boolean;
    message: string;
    data?: any;
}

export default class APIManager {
    private static async request(endpoint: string, data: any): Promise<APIResponse> {
        try {
            const token = localStorage.getItem("token");
            if (token) {
                data.token = token;
            }
            const res = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify(data),
            });

            const resData = await res.json();
            if (!res.ok) {
                return { success: false, message: resData.message || "Request Failed" };
            }
            return { success: true, message: resData.message || "", data: resData.data };
        } catch (error) {
            return {
                success: false,
                message: error instanceof Error ? error.message : "An unknown error occurred",
            };
        }
    }
    
    static async loginWithCredentials(email: string, password: string, userContextLogin: (user: User) => void): Promise<APIResponse> {
        const res = await this.request("/users/login_user_credentials", { email, password });
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
        const res = await this.request("/users/login_user_token", {});
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
}