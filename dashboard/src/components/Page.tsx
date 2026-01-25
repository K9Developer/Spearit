import React, { useEffect } from "react";

interface Props {
    title?: string;
    children: React.ReactNode;
    limitWidth?: boolean;
}

const Page = ({ title, children, limitWidth = false }: Props) => {
    useEffect(() => {
        if (title) {
            document.title = title + " - Spearit Dashboard";
        } else {
            document.title = "Spearit Dashboard";
        }
    }, [title]);

    return (
        <div className="w-full h-full flex justify-center">
            <div className={`${limitWidth ? "max-w-[40vw] w-[40vw]" : "w-full"}`}>{children}</div>
        </div>
    );
};

export default Page;
