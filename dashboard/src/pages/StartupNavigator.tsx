import { useUser } from "@/context/useUser";
import APIManager from "@/utils/api_manager";
import { useEffect } from "react";
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
    }, [login, navigate]);

    return (
        <div className="inset-0 absolute flex justify-center items-center">
            <OrbitProgress color="var(--color-text-primary)" size="large" text="" textColor="" />
        </div>
    );
};

export default StartupNavigator;
