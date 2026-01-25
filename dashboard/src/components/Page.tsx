import React, { useEffect } from "react";
import { MeshGradient } from "@mesh-gradient/react";
interface Props {
    title?: string;
    children: React.ReactNode;
    limitWidth?: boolean;
    className?: string;
    animated?: boolean;
}

const Page = ({ title, children, className, limitWidth = false, animated = false }: Props) => {
    useEffect(() => {
        if (title) {
            document.title = title + " - Spearit Dashboard";
        } else {
            document.title = "Spearit Dashboard";
        }
    }, [title]);

    return (
        <div className="w-screen h-screen flex justify-center relative">
            {animated && (
                <MeshGradient className="absolute inset-0 w-screen h-screen" options={{ colors: ["#030712", "#080f21", "#08051a", "#040212"] }} />
            )}
            <div className={`${limitWidth ? "max-w-[90vw] w-[90vw] lg:max-w-[50vw] lg:w-[50vw] z-10" : "w-full"} ${className}`}>{children}</div>
        </div>
    );
};

export default Page;
