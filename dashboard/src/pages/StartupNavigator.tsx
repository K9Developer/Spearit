import { useUser } from "@/context/User";
import APIManager from "@/utils/api_manager";
import React, { useEffect } from "react";
import { OrbitProgress } from "react-loading-indicators";
import { useNavigate } from "react-router-dom";

const StartupNavigator = () => {
    const { login } = useUser();
    const navigate = useNavigate();

    useEffect(() => {
        const checkToken = async () => {
            if (!localStorage.getItem("token")) {
                navigate("/login");
                return;
            }
            const res = await APIManager.loginWithToken(login);

            if (res.success) {
                navigate("/dashboard");
            } else {
                localStorage.removeItem("token");
                navigate("/login");
            }
        };
        checkToken();
    }, []);

    return (
        <div className="inset-0 absolute flex justify-center items-center">
            <OrbitProgress color="var(--color-text-primary)" size="large" text="" textColor="" />
        </div>
    );
};

export default StartupNavigator;
