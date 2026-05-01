import React from "react";
import Box from "@/components/Box";

interface Props {
    title: string;
    right?: React.ReactNode;
    children: React.ReactNode;
    className?: string;
}

export default function SectionCard({ title, right, children, className }: Props) {
    return (
        <Box.Secondary className={`p-5! lg:py-6 lg:px-6 ${className ?? ""}`.trim()}>
            <div className="flex items-center justify-between gap-4">
                <p className="text-sm font-semibold tracking-wide uppercase text-text-secondary">{title}</p>
                {right}
            </div>
            <div className="mt-4">{children}</div>
        </Box.Secondary>
    );
}
