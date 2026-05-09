import React from "react";

interface Props {
    isOpen: boolean;
    onClose: () => void;
    title?: string;
    maxWidthClass?: string;
    children?: React.ReactNode;
}

export default function Modal({ isOpen, onClose, title, maxWidthClass = "max-w-lg", children }: Props) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div className="absolute inset-0 bg-black/30 backdrop-blur-lg" onClick={onClose} />
            <div className={`relative z-10 w-full ${maxWidthClass} mx-4 bg-foreground rounded-md shadow-lg max-h-[80vh] overflow-y-auto`}>
                <div className="flex justify-between items-center sticky top-0 bg-foreground py-3 px-5 shadow-2xl z-50">
                    <p className="uppercase font-bold text-md">{title}</p>
                    <div onClick={onClose} className="cursor-pointer select-none p-2">
                        &times;
                    </div>
                </div>

                <div className="px-6 py-3">{children}</div>
            </div>
        </div>
    );
}
