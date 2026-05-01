import { createContext } from "react";
import type { UserContextType } from "./userTypes";

export const UserContext = createContext<UserContextType | undefined>(undefined);
