import React, { useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import NotFound from "./pages/NotFound";
import Login from "./pages/Login";
import toast, { Toaster, useToasterStore } from "react-hot-toast";

export function ToastLimiter({ max_toasts }: { max_toasts: number } = { max_toasts: 3 }) {
    const { toasts } = useToasterStore();
    useEffect(() => {
        const visible = toasts.filter((t) => t.visible).sort((a, b) => (b.createdAt ?? 0) - (a.createdAt ?? 0));

        visible.slice(max_toasts).forEach((t) => toast.dismiss(t.id)); // dismiss older ones
    }, [toasts, max_toasts]);
    return null;
}

export default function App() {
    return (
        <div>
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
            {/* <nav style={{ display: "flex", gap: 12, marginBottom: 16 }}>
                <Link to="/">Home</Link>
                <Link to="/about">About</Link>
            </nav> */}

            <Routes>
                <Route path="*" element={<NotFound />} />
                <Route path="/login" element={<Login />} />
            </Routes>
        </div>
    );
}
