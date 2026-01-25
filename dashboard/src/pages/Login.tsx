import React from "react";
import Page from "../components/Page";
import Box from "../components/Box";
import Input from "../components/Input";
import { Eye, EyeClosed } from "lucide-react";

const Login = () => {
    const [showPassword, setShowPassword] = React.useState(false);

    return (
        <Page title="Login" limitWidth={true}>
            <Box.Primary className="flex flex-col items-center gap-5">
                <p className="text-xl font-bold tracking-widest">LOGIN</p>
                <div className="flex flex-col w-full gap-5">
                    <Input title="Email" placeholder="e.g. example@gmail.com" className="w-full" />
                    <Input
                        title="Password"
                        placeholder="Enter your password"
                        type={showPassword ? "text" : "password"}
                        className="w-full"
                        icon={showPassword ? <EyeClosed className="cursor-pointer" /> : <Eye className="cursor-pointer" />}
                        onIconClick={() => setShowPassword(!showPassword)}
                    />
                </div>
            </Box.Primary>
        </Page>
    );
};

export default Login;
