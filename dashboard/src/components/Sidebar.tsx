import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import Hint from "./Hint";

export interface SidebarItem {
    title: string;
    icon: React.ReactNode;
    onClick: () => void;
    disabled?: boolean;
    disabledHint?: string;
}

export interface SidebarConfig {
    closable: boolean;
    title: string;
    titleIcon?: React.ReactNode;
    titleOpenIcon?: React.ReactNode;
    titleCloseIcon?: React.ReactNode;
    items: SidebarItem[];
}

interface SidebarProps {
    config: SidebarConfig;
    className?: string;
    defaultOpen?: boolean;
    onToggle?: (isOpen: boolean) => void;
    visible?: boolean;
    mode?: "overlay" | "push";
}

const OPEN_WIDTH_CLASS = "w-64";
const CLOSED_WIDTH_CLASS = "w-[4.5rem]";

const Sidebar = ({ config, className = "", defaultOpen = true, onToggle, visible = true, mode = "overlay" }: SidebarProps) => {
    const [isOpen, setIsOpen] = React.useState(config.closable ? defaultOpen : true);
    const [hoveredItem, setHoveredItem] = React.useState<string | null>(null);
    const hoverTimeoutRef = React.useRef<number | null>(null);

    const fallbackOpenToggleIcon = <ChevronLeft size={18} />;
    const fallbackClosedToggleIcon = <ChevronRight size={18} />;

    const openTitleIcon = config.titleOpenIcon ?? config.titleIcon;
    const closedTitleIcon = config.titleCloseIcon ?? config.titleIcon ?? fallbackClosedToggleIcon;

    React.useEffect(() => {
        if (!config.closable) {
            setIsOpen(true);
        }
    }, [config.closable]);

    React.useEffect(() => {
        return () => {
            if (hoverTimeoutRef.current !== null) {
                window.clearTimeout(hoverTimeoutRef.current);
            }
        };
    }, []);

    const startHover = (title: string) => {
        if (hoverTimeoutRef.current !== null) {
            window.clearTimeout(hoverTimeoutRef.current);
        }

        hoverTimeoutRef.current = window.setTimeout(() => {
            setHoveredItem(title);
            hoverTimeoutRef.current = null;
        }, 500);
    };

    const stopHover = () => {
        if (hoverTimeoutRef.current !== null) {
            window.clearTimeout(hoverTimeoutRef.current);
            hoverTimeoutRef.current = null;
        }

        setHoveredItem(null);
    };

    const toggleSidebar = () => {
        if (!config.closable) return;

        setIsOpen((prev) => {
            const next = !prev;
            onToggle?.(next);
            return next;
        });
    };

    if (!visible) return null;

    const widthClass = isOpen ? OPEN_WIDTH_CLASS : CLOSED_WIDTH_CLASS;
    const containerModeClass = mode === "overlay" ? "fixed left-0 top-0 z-[9999] h-screen" : "relative h-screen shrink-0";

    return (
        <aside
            className={`
                ${containerModeClass}
                ${widthClass}
                bg-foreground outline outline-secondary shadow-xl
                transition-[width] duration-300 ease-in-out
                overflow-hidden
                ${className}
            `}
        >
            <div className="h-full flex flex-col">
                <div className="h-14 px-3 flex items-center border-b border-secondary">
                    <button
                        type="button"
                        onClick={toggleSidebar}
                        className={`
                            relative w-full h-full
                            ${config.closable ? "cursor-pointer" : "cursor-default"}
                        `}
                        disabled={!config.closable}
                    >
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="flex items-center justify-center min-w-0">
                                <span className="w-6 h-6 shrink-0 flex items-center justify-center text-highlight">
                                    {isOpen ? openTitleIcon : config.closable ? closedTitleIcon : openTitleIcon}
                                </span>

                                <span
                                    className={`
                                        uppercase text-xs font-semibold tracking-wide text-text-secondary whitespace-nowrap overflow-hidden
                                        transition-all duration-300 ease-in-out
                                        ${isOpen ? "opacity-100 max-w-[200px] ml-2" : "opacity-0 max-w-0 ml-0"}
                                    `}
                                >
                                    {config.title}
                                </span>
                            </div>
                        </div>

                        {config.closable && isOpen && (
                            <span className="absolute right-0 inset-y-0 flex items-center justify-center w-6 text-highlight">
                                {fallbackOpenToggleIcon}
                            </span>
                        )}
                    </button>
                </div>

                <nav className="flex-1 p-3 flex flex-col gap-2">
                    {config.items.map((item) => {
                        const hintText = item.disabled ? item.disabledHint || item.title : item.title;

                        return (
                            <div
                                key={item.title}
                                className="relative overflow-visible"
                                onPointerEnter={() => startHover(item.title)}
                                onPointerLeave={stopHover}
                            >
                                <Hint
                                    text={hintText}
                                    show={hoveredItem === item.title && item.disabled === true && item.disabledHint !== undefined}
                                    className="absolute bottom-full mb-0 w-max"
                                />

                                <button
                                    type="button"
                                    onClick={() => {
                                        if (!item.disabled) item.onClick();
                                    }}
                                    disabled={item.disabled}
                                    className={`
                                        w-full h-11 rounded-lg
                                        flex items-center
                                        px-3
                                        transition-colors duration-200
                                        ${item.disabled ? "opacity-45 cursor-not-allowed" : "hover:bg-background/70 cursor-pointer"}
                                    `}
                                >
                                    <span
                                        className={`
                                            shrink-0 w-6 h-6 flex items-center justify-center
                                            ${item.disabled ? "text-text-gray" : "text-highlight"}
                                        `}
                                    >
                                        {item.icon}
                                    </span>

                                    <span
                                        className={`
                                            ml-3 overflow-hidden whitespace-nowrap text-sm text-text-primary
                                            transition-all duration-300 ease-in-out
                                            ${isOpen ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-2 pointer-events-none"}
                                        `}
                                    >
                                        {item.title}
                                    </span>
                                </button>
                            </div>
                        );
                    })}
                </nav>
            </div>
        </aside>
    );
};

export default Sidebar;
