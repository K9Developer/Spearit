import React from "react";
import Page from "../components/Page";
import Box from "../components/Box";
import Input from "../components/Input";
import { Eye, EyeClosed } from "lucide-react";
import Button from "../components/Button";
import { Link } from "react-router-dom";

const Login = () => {
    const [showPassword, setShowPassword] = React.useState(false);

    return (
        <Page title="Login" limitWidth={true} className="p-12 flex justify-center">
            <Box.Primary className="flex flex-col items-center gap-5 w-[60vw] ">
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
                    <div className="flex flex-col gap-2">
                        <p className="text-sm"><Link to={"/forgot"}>Forgot your password?</Link></p>
                        <p className="text-sm">New to SpearIT? <Link to={"/signup"}>Sign Up</Link></p>
                    </div>

                    <Button
                        title="Log in"
                        highlight
                        className="px-20 rounded-xl"
                    />
                </div>
            </Box.Primary>
        </Page>
    );
};

export default Login;
