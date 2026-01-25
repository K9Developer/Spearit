import React, { useState } from "react";
import Page from "../components/Page";
import Box from "../components/Box";
import Input from "../components/Input";
import { Eye, EyeClosed } from "lucide-react";
import Button from "../components/Button";
import { Link } from "react-router-dom";
import ErrorHint from "../components/ErrorHint";

const Signup = () => {
    const [showPassword, setShowPassword] = useState(false);
    const [errors, setErrors] = useState({
        email: false,
        password: false,
        name: false
    })

    const handleMailChange = (email: string) => {
        const emailReg = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
        const valid = emailReg.test(email)
        setErrors(e => {
            e.email = !valid;
            return e;
        })
    }

    const handlePasswordChange = (pass: string) => {
        const valid = pass.length >= 8
        setErrors(e => {
            e.password = !valid;
            return e;
        })
    }

    const handleNameChange = (name: string) => {
        const valid = name.length >= 3;
        setErrors(e => {
            e.name = !valid;
            return e;
        })
    }

    return (
        <Page title="Login" limitWidth={true} className="p-12 flex justify-center">
            <Box.Primary className="flex flex-col items-center gap-5 w-[60vw] ">
                <p className="text-xl font-bold tracking-widest">SIGNUP</p>
                <div className="flex flex-col w-full gap-5">
                    <Input title="Email" placeholder="e.g. example@gmail.com" className="w-full" onBlur={(e) => handleMailChange(e.target.value)} errored />
                    <Input
                        title="Password"
                        placeholder="Enter your password"
                        type={showPassword ? "text" : "password"}
                        className="w-full"
                        icon={showPassword ? <EyeClosed className="cursor-pointer text-text-gray" /> : <Eye className="cursor-pointer" />}
                        onIconClick={() => setShowPassword(!showPassword)}
                        onBlur={(e) => handlePasswordChange(e.target.value)}
                    />
                    <Input title="Full Name" placeholder="e.g. John Doe" className="w-full" onBlur={(e) => handleNameChange(e.target.value)}/>
                    <div className="flex flex-col gap-2">
                        <p className="text-sm">Already have an account? <Link to={"/login"}>Log In</Link></p>
                    </div>

                    <div>
                        <ErrorHint message="Please enter a valid email"/>
                        <ErrorHint message="Please enter a valid password"/>
                    </div>
                    <Button
                        title="Sign Up"
                        highlight
                        className="px-20 rounded-xl mt-10"
                    />
                </div>
            </Box.Primary>
        </Page>
    );
};

export default Signup;
