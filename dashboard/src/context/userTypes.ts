import type { Permission } from "@/utils/types";

export type User = {
    id: number;
    fullname: string;
    email: string;
    permissions: Permission[];
};

export type UserContextType = {
    user: User | null;
    isLoggedIn: boolean;
    login: (user: User) => void;
    logout: () => void;
};
