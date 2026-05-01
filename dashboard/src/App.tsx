import React, { useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import NotFound from "./pages/NotFound";
import Login from "./pages/Login";
import toast, { Toaster, useToasterStore } from "react-hot-toast";
import APIManager from "./utils/api_manager";
import { OrbitProgress } from "react-loading-indicators";
import StartupNavigator from "./pages/StartupNavigator";
import { useUser } from "./context/User";
import Logo from "./components/Logo";
import { BarChart3, Home, Settings, Users } from "lucide-react";
import type { SidebarConfig } from "./components/Sidebar";
import Sidebar from "./components/Sidebar";
import Overview from "./pages/Overview";

export function ToastLimiter({ max_toasts }: { max_toasts: number } = { max_toasts: 3 }) {
    const { toasts } = useToasterStore();
    useEffect(() => {
        const visible = toasts.filter((t) => t.visible).sort((a, b) => (b.createdAt ?? 0) - (a.createdAt ?? 0));

        visible.slice(max_toasts).forEach((t) => toast.dismiss(t.id)); // dismiss older ones
    }, [toasts, max_toasts]);
    return null;
}

const sidebarConfig: SidebarConfig = {
    closable: true,
    title: "SpearIT",
    titleOpenIcon: <Logo showText={false} />,
    titleCloseIcon: <Logo showText={false} />,
    items: [
        { title: "Home", icon: <Home size={18} />, onClick: () => {} },
        { title: "Analytics", icon: <BarChart3 size={18} />, onClick: () => {} },
        { title: "Users", icon: <Users size={18} />, onClick: () => {} },
        {
            title: "Settings",
            icon: <Settings size={18} />,
            onClick: () => {},
            disabled: true,
            disabledHint: "Settings are disabled in this sample",
        },
    ],
};

export default function App() {
    const { user, isLoggedIn, login, logout } = useUser();
    console.log(isLoggedIn);
    return (
        <div className="flex h-screen overflow-hidden">
            <Sidebar config={sidebarConfig} visible={isLoggedIn} mode="push" defaultOpen={false} />

            <div className="flex-1 min-w-0 overflow-hidden">
                <Toaster
                    toastOptions={{
                        style: {
                            background: "var(--color-secondary)",
                            color: "#fff",
                            border: "1px solid rgba(255,255,255,0.2)",
                            borderRadius: "12px",
                            padding: "12px 14px",
                        },
                    }}
                />
                <ToastLimiter max_toasts={3} />

                <Routes>
                    <Route path="*" element={<NotFound />} />
                    <Route path="/" element={<StartupNavigator />} />
                    <Route path="/login" element={<Login />} />

                    <Route path="/dashboard" element={<Overview />} />
                </Routes>
            </div>
        </div>
    );
}
