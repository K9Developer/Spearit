import React from "react";

interface Props {
    placeholder?: string;
    title?: string;
    type?: string;
    value?: string;
    defaultValue?: string;
    disabled?: boolean;
    icon?: React.ReactNode;
    onChange?: (value: string) => void;
    onIconClick?: () => void;
    onFocus?: (e: React.FocusEvent<HTMLInputElement>) => void;
    onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
    className?: string;
    errored?: boolean;
    ref?: React.Ref<HTMLInputElement>;
}

const Input = ({
    title,
    placeholder,
    type,
    value,
    defaultValue,
    disabled,
    icon,
    onChange,
    onIconClick,
    onFocus,
    onBlur,
    className,
    ref,
    errored = false,
}: Props) => {
    return (
        <div className="flex flex-col gap-1 relative">
            {title && <label className="text-xs text-text-primary uppercase select-none">{title}</label>}
            <div
                className={`transition-all flex flex-row items-center w-full outline outline-secondary rounded-md ${errored ? "outline-[#f5474f]!" : ""} ${className}`}
            >
                <input
                    className={`w-full px-3 py-2 text-sm text-text-primary placeholder:text-text-gray outline-none ${disabled ? "opacity-70 cursor-not-allowed" : ""}`}
                    placeholder={placeholder}
                    onChange={(e) => onChange && onChange(e.target.value)}
                    onFocus={onFocus}
                    onBlur={onBlur}
                    type={type}
                    value={value}
                    defaultValue={defaultValue}
                    disabled={disabled}
                    ref={ref}
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
