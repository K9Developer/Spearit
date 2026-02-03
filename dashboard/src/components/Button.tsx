import React from "react";
import Hint from "./Hint";
import { PuffLoader } from "react-spinners";

interface Props {
    title: string;
    hint?: string;
    disabledHint?: string;
    highlight?: boolean;
    disabled?: boolean;
    loading?: boolean;
    icon?: React.ReactNode;
    onClick?: () => void;
    className?: string;
}

const Button = ({ title, hint, disabledHint, highlight, disabled, loading, icon, onClick, className }: Props) => {
    const [isHovered, setIsHovered] = React.useState(false);

    return (
        <div className="relative flex justify-center items-center">
            {hint && (
                <Hint
                    text={disabled ? disabledHint || hint : hint}
                    show={(isHovered && !disabled) || (isHovered && disabled)}
                    className="absolute bottom-full mb-2 w-max"
                />
            )}
            <button
                className={`flex gap-3 items-center justify-center font-bold min-w-20 py-3 px-5 rounded-md ${highlight ? "bg-highlight text-foreground" : "bg-foreground"} ${disabled ? "opacity-50 cursor-not-allowed" : "hover:brightness-75 cursor-pointer"} transition-all shadow-lg duration-200 outline-none ${className}`}
                disabled={disabled}
                onPointerEnter={() => setIsHovered(true)}
                onPointerLeave={() => setIsHovered(false)}
                onClick={onClick}
            >
                {icon && !loading && icon}
                {loading && <PuffLoader size={23}/> }
                {title}
            </button>
        </div>
    );
};

export default Button;
