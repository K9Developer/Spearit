import React, { useEffect, useRef, useState } from "react";

interface Props {
    isOpen: boolean;
    onClose: () => void;
    title?: string;
    children?: React.ReactNode;
}

const ANIM = 150;

export default function Modal({ isOpen, onClose, title, children }: Props) {
    const [mounted, setMounted] = useState(false);
    const [visible, setVisible] = useState(false);
    const closeTimer = useRef<number | null>(null);
    const raf1 = useRef<number | null>(null);
    const raf2 = useRef<number | null>(null);

    useEffect(() => {
        // cleanup helpers
        const clearTimers = () => {
            if (closeTimer.current) window.clearTimeout(closeTimer.current);
            if (raf1.current) cancelAnimationFrame(raf1.current);
            if (raf2.current) cancelAnimationFrame(raf2.current);
            closeTimer.current = raf1.current = raf2.current = null;
        };

        if (isOpen) {
            clearTimers();
            setMounted(true);
            setVisible(false); // reset start state every time

            // ensure DOM paints "hidden" before switching to visible
            raf1.current = requestAnimationFrame(() => {
                raf2.current = requestAnimationFrame(() => setVisible(true));
            });
        } else {
            setVisible(false);
            closeTimer.current = window.setTimeout(() => setMounted(false), ANIM);
        }

        return clearTimers;
    }, [isOpen]);

    if (!mounted) return null;

    return (
        <div
            className={`fixed inset-0 z-50 flex items-center justify-center transition-opacity duration-150 ${
                visible ? "opacity-100" : "opacity-0 pointer-events-none"
            }`}
        >
            <div
                className={`absolute inset-0 bg-black/30 backdrop-blur-lg transition-opacity duration-150 ${visible ? "opacity-100" : "opacity-0"}`}
                onClick={onClose}
            />
            <div
                className={`relative z-10 w-full max-w-lg mx-4 bg-foreground rounded-md shadow-lg max-h-[80vh] overflow-y-auto transform transition-all duration-150 ${visible ? "opacity-100 scale-100 translate-y-0" : "opacity-0 scale-95 translate-y-2"}`}
            >
                <div className="flex justify-between items-center sticky top-0 bg-foreground py-3 px-5 shadow-2xl">
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
