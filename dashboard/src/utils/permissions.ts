import type { Permission } from "@/utils/types";

export const hasPermission = (permissions: Permission[], type: string) => {
    if (permissions.some((p) => p.type === "root")) return true;
    return permissions.some((p) => p.type === type);
};
