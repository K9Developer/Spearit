import React, { useEffect } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";
import NotFound from "./pages/NotFound";
import Login from "./pages/Login";
import toast, { Toaster, useToasterStore } from "react-hot-toast";
import StartupNavigator from "./pages/StartupNavigator";
import { useUser } from "./context/useUser";
import Logo from "./components/Logo";
import { BarChart3, HardDrive, Home, LogOut, Settings, Users } from "lucide-react";
import type { SidebarConfig } from "./components/Sidebar";
import Sidebar from "./components/Sidebar";
import Overview from "./pages/Overview";
import UsersPage from "./pages/Users";
import DevicesPage from "./pages/Devices";

export function ToastLimiter({ max_toasts }: { max_toasts: number } = { max_toasts: 3 }) {
    const { toasts } = useToasterStore();
    useEffect(() => {
        const visible = toasts.filter((t) => t.visible).sort((a, b) => (b.createdAt ?? 0) - (a.createdAt ?? 0));

        visible.slice(max_toasts).forEach((t) => toast.dismiss(t.id)); // dismiss older ones
    }, [toasts, max_toasts]);
    return null;
}

export default function App() {
    const { isLoggedIn, logout } = useUser();
    const navigate = useNavigate();

    const sidebarConfig: SidebarConfig = React.useMemo(
        () => ({
            closable: true,
            title: "SpearIT",
            titleOpenIcon: <Logo showText={false} />,
            titleCloseIcon: <Logo showText={false} />,
            items: [
                { title: "Home", icon: <Home size={18} />, onClick: () => navigate("/dashboard") },
                { title: "Devices", icon: <HardDrive size={18} />, onClick: () => navigate("/dashboard/devices") },
                { title: "Users", icon: <Users size={18} />, onClick: () => navigate("/dashboard/users") },
                {
                    title: "Settings",
                    icon: <Settings size={18} />,
                    onClick: () => {},
                    disabled: true,
                    disabledHint: "Settings are disabled in this sample",
                },
                {
                    title: "Logout",
                    icon: <LogOut size={18} />,
                    onClick: () => {
                        logout();
                        navigate("/login");
                    },
                },
            ],
        }),
        [navigate, logout],
    );

    if (!isLoggedIn && window.location.pathname !== "/login") {
        return <StartupNavigator />;
    }

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
                    <Route path="/dashboard/devices" element={<DevicesPage />} />
                    <Route path="/dashboard/users" element={<UsersPage />} />
                </Routes>
            </div>
        </div>
    );
}
