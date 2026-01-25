import React from "react";

type BoxChildProps = React.PropsWithChildren<{ className?: string }>;

type BoxComp = React.FC & {
    Primary: React.FC<BoxChildProps>;
    Secondary: React.FC<BoxChildProps>;
};

const Box: BoxComp = (() => {
    return <div>Box</div>;
}) as unknown as BoxComp;

Box.Primary = ({ children, className }) => <div className={`rounded-md p-5 bg-foreground ${className}`}>{children}</div>;
Box.Secondary = ({ children, className }) => <div className={`rounded-md p-5 bg-secondary ${className}`}>{children}</div>;

export default Box;
