import React from "react";
import { UserContext } from "./userContext";
import type { User } from "./userTypes";

export const UserProvider = ({ children }: { children: React.ReactNode }) => {
    const [user, setUser] = React.useState<User | null>(null);

    const login = (userData: User) => setUser(userData);
    const logout = () => {
        localStorage.removeItem("token");
        setUser(null);
    };

    return (
        <UserContext.Provider
            value={{
                user,
                isLoggedIn: user !== null,
                login,
                logout,
            }}
        >
            {children}
        </UserContext.Provider>
    );
};
