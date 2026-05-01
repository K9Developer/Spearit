import React from "react";
import Box from "@/components/Box";

interface Props {
    label: string;
    value: React.ReactNode;
    icon?: React.ReactNode;
    hint?: string;
    className?: string;
}

export default function StatCard({ label, value, icon, hint, className }: Props) {
    return (
        <Box.Secondary className={`p-5! lg:py-6 lg:px-6 ${className ?? ""}`.trim()}>
            <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                    <p className="text-xs uppercase tracking-wide text-text-gray">{label}</p>
                    <div className="mt-2 text-2xl font-semibold text-text-primary truncate">{value}</div>
                    {hint && <p className="mt-2 text-sm text-text-secondary">{hint}</p>}
                </div>
                {icon && <div className="shrink-0 text-highlight">{icon}</div>}
            </div>
        </Box.Secondary>
    );
}
