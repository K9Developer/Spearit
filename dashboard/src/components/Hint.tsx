import React from "react";

interface Props {
    text: string;
    show?: boolean;
    className?: string;
}

const Hint = ({ text, show, className }: Props) => {
    return (
        <div className={`${className} ${show === false ? "opacity-0" : "opacity-100"} transition-opacity duration-200`}>
            <div className="relative bg-foreground rounded-md p-2 shadow-lg">
                <p className="max-w-60 text-sm wrap-break-word">{text}</p>
                <div className="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-8 border-t-foreground"></div>
            </div>
        </div>
    );
};

export default Hint;
