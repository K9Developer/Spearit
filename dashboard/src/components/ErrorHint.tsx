import React from "react";
import { CircleAlert } from "lucide-react";

interface Props {
    message: string;
}

const ErrorHint = ({ message }: Props) => {
    return (
        <div className="flex flex-row items-center gap-2">
            <CircleAlert color="#f5474f" className="w-4 h-4" /> <p className="text-[#f5474f]">{message}</p>
        </div>
    );
};

export default ErrorHint;
