import React, { useEffect } from "react";

interface Props {
    title?: string;
    children: React.ReactNode;
    limitWidth?: boolean;
    className?: string;
}

const Page = ({ title, children, className, limitWidth = false }: Props) => {
    useEffect(() => {
        if (title) {
            document.title = title + " - Spearit Dashboard";
        } else {
            document.title = "Spearit Dashboard";
        }
    }, [title]);

    return (
        <div className="w-screen h-screen flex justify-center">
            <div className={`${limitWidth ? "max-w-[90vw] w-[90vw] lg:max-w-[50vw] lg:w-[50vw]" : "w-full"} ${className}`}>{children}</div>
        </div>
    );
};

export default Page;
