import React, { useEffect, useState } from "react";
import Page from "../components/Page";
import Box from "../components/Box";
import Input from "../components/Input";
import { Eye, EyeClosed } from "lucide-react";
import Button from "../components/Button";
import { Link } from "react-router-dom";
import ErrorHint from "@/components/ErrorHint";
import { Info } from "lucide-react";
import Logo from "@/components/Logo";

const Login = () => {
    const [showPassword, setShowPassword] = useState(false);

    const [emailError, setEmailError] = useState(false);
    const [passwordError, setPasswordError] = useState(false);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const handleMailChange = (email: string, onlyValid: boolean = false) => {
        if (!email) return;
        const emailReg = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        const valid = emailReg.test(email);
        if (onlyValid && !valid) return;
        setEmailError(!valid);
    };

    const handlePasswordChange = (pass: string, onlyValid: boolean = false) => {
        if (!pass) return;
        const valid = pass.length >= 8;
        if (onlyValid && !valid) return;
        setPasswordError(!valid);
    };

    useEffect(() => {
        if (!email) setEmailError(false);
        if (!password) setPasswordError(false);
        handleMailChange(email, false);
        handlePasswordChange(password, false);
    }, [email, password]);

    return (
        <Page title="Login" limitWidth={false} className="flex flex-col items-center gap-14" animated>
            <Box.Primary className="flex flex-col items-center gap-5 lg:w-[40vw] bg-background! mt-32 relative">
                <p className="text-xl">LOGIN</p>
                <div className="flex flex-col w-full gap-5">
                    <Input title="Email" placeholder="e.g. example@gmail.com" className="w-full" onChange={setEmail} errored={emailError} />
                    <Input
                        title="Password"
                        placeholder="Enter your password"
                        type={showPassword ? "text" : "password"}
                        className="w-full"
                        icon={
                            showPassword ? (
                                <EyeClosed className="cursor-pointer" stroke="var(--color-text-gray)" />
                            ) : (
                                <Eye className="cursor-pointer" stroke="var(--color-text-gray)" />
                            )
                        }
                        onIconClick={() => setShowPassword(!showPassword)}
                        onChange={setPassword}
                        errored={passwordError}
                    />
                    <div className="flex flex-col gap-6">
                        <p className="text-sm">
                            <Link to={"/forgot"}>Forgot your password?</Link>
                        </p>
                        <Box.Secondary className="p-4! text-sm text-text-secondary flex items-center gap-2">
                            <Info className="w-4 h-4" />
                            <p className="mt-1">If you don't have an account, please request one from an admin.</p>
                        </Box.Secondary>
                    </div>
                    <div>
                        {emailError && <ErrorHint message="Please enter a valid email address" />}
                        {passwordError && <ErrorHint message="Please enter a valid password" />}
                    </div>
                    <Button title="Log in" highlight className="px-20 rounded-xl" disabled={emailError || passwordError || !email || !password} />
                    <div className="h-px w-full bg-secondary my-8"></div>
                    <div className="w-full flex justify-center">
                        <Logo size={48} showText />
                    </div>
                </div>
            </Box.Primary>
        </Page>
    );
};

export default Login;
