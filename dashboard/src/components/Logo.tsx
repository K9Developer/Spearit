import LogoSvg from "../assets/logo.svg?react";

interface Props {
    color?: string;
    size?: number;
    showText?: boolean;
    className?: string;
}

const Logo = ({ className, color = "var(--color-text-primary)", size = 24, showText = false }: Props) => {
    return (
        <div className={`flex flex-row items-center ${className}`}>
            <LogoSvg width={size} height={size} style={{ fill: color, color: color }} />
            {showText && (
                <span style={{ color: color, fontSize: size * 0.5, marginLeft: 8, fontWeight: "bold" }} className="select-none">
                    SpearIT
                </span>
            )}
        </div>
    );
};

export default Logo;
