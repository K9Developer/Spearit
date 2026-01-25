import React from "react";

interface Props {
    placeholder?: string;
    title?: string;
    type?: string;
    icon?: React.ReactNode;
    onChange?: (value: string) => void;
    onIconClick?: () => void;
    onFocus?: () => void;
    onBlur?: () => void;
    className?: string;
}

const Input = ({ title, placeholder, type, icon, onChange, onIconClick, onFocus, onBlur, className }: Props) => {
    return (
        <div className="flex flex-col gap-1 relative">
            {title && <label className="text-xs text-text-primary uppercase select-none">{title}</label>}
            <div className={"flex flex-row items-center w-full border border-secondary bg-foreground rounded-md " + (className || "")}>
                <input
                    className="w-full px-3 py-2 text-sm text-text-primary placeholder:text-text-gray outline-none"
                    placeholder={placeholder}
                    onChange={(e) => onChange && onChange(e.target.value)}
                    onFocus={onFocus}
                    onBlur={onBlur}
                    type={type}
                />
                {icon && (
                    <div className="pr-3 text-text-gray" onClick={onIconClick}>
                        {icon}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Input;
