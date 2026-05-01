import Box from "@/components/Box";
import Button from "@/components/Button";
import Input from "@/components/Input";
import Modal from "@/components/Modal";
import { useUser } from "@/context/useUser";
import APIManager, { type UserManagementMetadata } from "@/utils/api_manager";
import type { ManagedUser, Permission } from "@/utils/types";
import { KeyRound, Pencil, Plus, RefreshCw, Trash2, Users as UsersIcon } from "lucide-react";
import React from "react";
import toast from "react-hot-toast";
import PermissionEditor from "./users/PermissionEditor";
import SimpleTable from "./users/SimpleTable";

const hasPermission = (permissions: Permission[], type: string) => {
    if (permissions.some((p) => p.type === "root")) return true;
    return permissions.some((p) => p.type === type);
};

const summarizePermissions = (permissions: Permission[]) => {
    if (permissions.length === 0) return "—";
    if (permissions.some((p) => p.type === "root")) return "root";
    const unique = Array.from(new Set(permissions.map((p) => p.type)));
    return unique.join(", ");
};

const hasDuplicatePermissionTypes = (permissions: Permission[]) => {
    const types = permissions.map((p) => p.type);
    return new Set(types).size !== types.length;
};

export default function Users() {
    const { user } = useUser();

    const canControlUsers = user ? hasPermission(user.permissions, "control_users") : false;
    const currentUserIsRoot = user ? user.permissions.some((p) => p.type === "root") : false;
    const currentUserPermissionTypes = React.useMemo(() => new Set((user?.permissions ?? []).map((p) => p.type)), [user]);

    const canGrantType = React.useCallback(
        (type: string) => {
            if (type === "root") return currentUserIsRoot;
            if (currentUserIsRoot) return true;
            return currentUserPermissionTypes.has(type);
        },
        [currentUserIsRoot, currentUserPermissionTypes],
    );

    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState<string | null>(null);

    const [metadata, setMetadata] = React.useState<UserManagementMetadata | null>(null);
    const [users, setUsers] = React.useState<ManagedUser[]>([]);

    const [createOpen, setCreateOpen] = React.useState(false);
    const [editOpen, setEditOpen] = React.useState(false);

    const [createEmail, setCreateEmail] = React.useState("");
    const [createTempPassword, setCreateTempPassword] = React.useState("");
    const [createPermissions, setCreatePermissions] = React.useState<Permission[]>([]);

    const [selectedUser, setSelectedUser] = React.useState<ManagedUser | null>(null);
    const [editPermissions, setEditPermissions] = React.useState<Permission[]>([]);
    const [selectedUserInitialHasRoot, setSelectedUserInitialHasRoot] = React.useState(false);
    const [selectedUserInitialHasControlUsers, setSelectedUserInitialHasControlUsers] = React.useState(false);

    const [newPassword, setNewPassword] = React.useState("");
    const [confirmPassword, setConfirmPassword] = React.useState("");

    const resetCreate = () => {
        setCreateEmail("");
        setCreateTempPassword("");
        setCreatePermissions([]);
    };

    const openCreate = () => {
        resetCreate();
        setCreateOpen(true);
    };

    const openEdit = (u: ManagedUser) => {
        setSelectedUser(u);
        setEditPermissions(u.permissions ?? []);
        setSelectedUserInitialHasRoot((u.permissions ?? []).some((p) => p.type === "root"));
        setSelectedUserInitialHasControlUsers((u.permissions ?? []).some((p) => p.type === "control_users"));
        setNewPassword("");
        setConfirmPassword("");
        setEditOpen(true);
    };

    const load = React.useCallback(async () => {
        if (!canControlUsers) {
            setLoading(false);
            setUsers([]);
            setMetadata(null);
            return;
        }

        setLoading(true);
        setError(null);

        const [metaRes, usersRes] = await Promise.all([APIManager.getUserManagementMetadata(), APIManager.listUsers()]);

        if (metaRes.success && metaRes.data) setMetadata(metaRes.data);
        else setMetadata({ permission_types: {}, device_ids: {}, group_ids: {} });

        if (usersRes.success && usersRes.data) {
            setUsers(usersRes.data.users);
        } else {
            setUsers([]);
            setError(usersRes.message || "Failed to load users");
        }

        setLoading(false);
    }, [canControlUsers]);

    React.useEffect(() => {
        load();
    }, [load]);

    const onCreate = async () => {
        if (!createEmail || !createTempPassword) return;
        if (hasDuplicatePermissionTypes(createPermissions)) {
            toast.error("Duplicate permission types are not allowed");
            return;
        }
        const disallowed = createPermissions.find((p) => !canGrantType(p.type));
        if (disallowed) {
            toast.error(`You can't grant '${disallowed.type}' unless you have it (or are root)`);
            return;
        }
        const res = await APIManager.createUser(createEmail, createTempPassword, createPermissions);
        if (res.success) {
            toast.success("User created");
            setCreateOpen(false);
            await load();
        } else {
            toast.error(res.message || "Failed to create user");
        }
    };

    const onSavePermissions = async () => {
        if (!selectedUser) return;
        if (hasDuplicatePermissionTypes(editPermissions)) {
            toast.error("Duplicate permission types are not allowed");
            return;
        }
        const nextHasRoot = editPermissions.some((p) => p.type === "root");
        const nextHasControlUsers = editPermissions.some((p) => p.type === "control_users");
        const editingSelf = user ? selectedUser.id === user.id : false;

        if (editingSelf && selectedUserInitialHasRoot && !nextHasRoot) {
            toast.error("You cannot remove your own root permissions");
            return;
        }

        if (editingSelf && selectedUserInitialHasControlUsers && !nextHasControlUsers) {
            toast.error("You cannot remove your own control_users permissions");
            return;
        }

        if (!editingSelf) {
            const initialTypes = new Set((selectedUser.permissions ?? []).map((p) => p.type));
            const nextTypes = new Set(editPermissions.map((p) => p.type));
            const addedTypes = Array.from(nextTypes).filter((t) => !initialTypes.has(t));
            const disallowed = addedTypes.find((t) => !canGrantType(t));
            if (disallowed) {
                toast.error(`You can't grant '${disallowed}' unless you have it (or are root)`);
                return;
            }
        }

        if (!currentUserIsRoot && nextHasRoot !== selectedUserInitialHasRoot) {
            toast.error("Only root users can change root permissions");
            return;
        }
        const res = await APIManager.updateUserPermissions(selectedUser.id, editPermissions);
        if (res.success) {
            toast.success("Permissions updated");
            setEditOpen(false);
            await load();
        } else {
            toast.error(res.message || "Failed to update permissions");
        }
    };

    const onSetPassword = async () => {
        if (!selectedUser) return;
        if (!newPassword || newPassword !== confirmPassword) {
            toast.error("Passwords do not match");
            return;
        }
        const res = await APIManager.setUserPassword(selectedUser.id, newPassword);
        if (res.success) {
            toast.success("Password updated");
            setNewPassword("");
            setConfirmPassword("");
        } else {
            toast.error(res.message || "Failed to update password");
        }
    };

    const onDeleteUser = async () => {
        if (!selectedUser) return;
        if (user && selectedUser.id === user.id) {
            toast.error("You can't delete your own user");
            return;
        }

        const ok = window.confirm(`Delete user '${selectedUser.email}'? This cannot be undone.`);
        if (!ok) return;

        const res = await APIManager.deleteUser(selectedUser.id);
        if (res.success) {
            toast.success("User deleted");
            setEditOpen(false);
            await load();
        } else {
            toast.error(res.message || "Failed to delete user");
        }
    };

    return (
        <div className="h-full min-h-0 overflow-y-auto">
            <div className="px-6 py-6">
                <div className="flex items-start justify-between gap-6">
                    <div className="min-w-0">
                        <p className="text-xs uppercase tracking-wide text-text-gray">Administration</p>
                        <h1 className="mt-1 text-2xl font-semibold text-text-primary">Users</h1>
                        <p className="mt-2 text-sm text-text-secondary">Create users, assign permissions, and reset passwords</p>
                    </div>

                    <div className="shrink-0 flex items-center gap-3">
                        <Button
                            title={loading ? "Refreshing" : "Refresh"}
                            onClick={load}
                            loading={loading}
                            icon={!loading ? <RefreshCw size={18} /> : undefined}
                            className="rounded-xl"
                        />
                        <Button
                            title="Create User"
                            onClick={openCreate}
                            icon={<Plus size={18} />}
                            className="rounded-xl"
                            disabled={!canControlUsers}
                        />
                    </div>
                </div>

                <div className="mt-6">
                    {!user && (
                        <Box.Secondary className="p-6!">
                            <p className="text-sm text-text-secondary">You are not logged in.</p>
                        </Box.Secondary>
                    )}

                    {user && !canControlUsers && (
                        <Box.Secondary className="p-6!">
                            <div className="flex items-center gap-3">
                                <span className="text-highlight">
                                    <UsersIcon size={20} />
                                </span>
                                <p className="text-sm text-text-secondary">You do not have permission to manage users.</p>
                            </div>
                        </Box.Secondary>
                    )}

                    {user && canControlUsers && (
                        <Box.Secondary className="p-6!">
                            {error && <p className="text-sm text-text-secondary">{error}</p>}
                            <SimpleTable
                                emptyText={loading ? "Loading…" : "No users"}
                                rows={users}
                                columns={[
                                    {
                                        key: "name",
                                        header: "Name",
                                        render: (u) => <span className="text-text-primary">{u.fullname}</span>,
                                    },
                                    {
                                        key: "email",
                                        header: "Email",
                                        render: (u) => <span className="text-text-secondary">{u.email}</span>,
                                    },
                                    {
                                        key: "permissions",
                                        header: "Permissions",
                                        render: (u) => <span className="text-text-gray">{summarizePermissions(u.permissions ?? [])}</span>,
                                    },
                                    {
                                        key: "actions",
                                        header: "",
                                        className: "w-24",
                                        render: (u) => (
                                            <div className="flex justify-end">
                                                <Button
                                                    title="Edit"
                                                    onClick={() => openEdit(u)}
                                                    icon={<Pencil size={18} color="black" />}
                                                    className="rounded-xl"
                                                    highlight
                                                />
                                            </div>
                                        ),
                                    },
                                ]}
                            />
                        </Box.Secondary>
                    )}
                </div>

                <Modal isOpen={createOpen} onClose={() => setCreateOpen(false)} title="Create User">
                    <div className="flex flex-col gap-5">
                        <Input title="Email" placeholder="user@example.com" onChange={setCreateEmail} />
                        <Input title="Temporary Password" placeholder="Set a temporary password" type="password" onChange={setCreateTempPassword} />

                        <div>
                            <p className="text-xs uppercase tracking-wide text-text-gray">Initial Permissions</p>
                            <div className="mt-3">
                                <PermissionEditor
                                    permissionTypes={metadata?.permission_types ?? {}}
                                    groupIds={metadata?.group_ids ?? {}}
                                    deviceIds={metadata?.device_ids ?? {}}
                                    canAssignType={canGrantType}
                                    lockedTypes={new Set<string>()}
                                    value={createPermissions}
                                    onChange={setCreatePermissions}
                                />
                            </div>
                        </div>

                        <div className="flex justify-end gap-3">
                            <Button title="Cancel" onClick={() => setCreateOpen(false)} className="rounded-xl" />
                            <Button
                                title="Create"
                                highlight
                                onClick={onCreate}
                                className="rounded-xl"
                                disabled={!createEmail || !createTempPassword}
                                icon={<Plus size={18} color="black" />}
                            />
                        </div>
                    </div>
                </Modal>

                <Modal isOpen={editOpen} onClose={() => setEditOpen(false)} title={selectedUser ? `Edit ${selectedUser.fullname}` : "Edit User"}>
                    {selectedUser && (
                        <div className="flex flex-col gap-6">
                            <div className="rounded-md outline outline-secondary bg-background/30 p-4">
                                <p className="text-xs uppercase tracking-wide text-text-gray">User</p>
                                <p className="mt-2 text-sm text-text-secondary">{selectedUser.email}</p>
                            </div>

                            <div>
                                <p className="text-xs uppercase tracking-wide text-text-gray">Permissions</p>
                                <div className="mt-3">
                                    <PermissionEditor
                                        permissionTypes={metadata?.permission_types ?? {}}
                                        groupIds={metadata?.group_ids ?? {}}
                                        deviceIds={metadata?.device_ids ?? {}}
                                        canAssignType={canGrantType}
                                        lockedTypes={
                                            user && selectedUser.id === user.id
                                                ? new Set([
                                                      ...(selectedUserInitialHasRoot ? ["root"] : []),
                                                      ...(selectedUserInitialHasControlUsers ? ["control_users"] : []),
                                                  ])
                                                : new Set<string>()
                                        }
                                        value={editPermissions}
                                        onChange={setEditPermissions}
                                    />
                                </div>

                                <div className="mt-4 flex justify-end">
                                    <Button
                                        title="Save Permissions"
                                        highlight
                                        onClick={onSavePermissions}
                                        className="rounded-xl"
                                        icon={<Pencil size={18} color="black" />}
                                    />
                                </div>
                            </div>

                            <div>
                                <p className="text-xs uppercase tracking-wide text-text-gray">Change Password</p>
                                <div className="mt-3 grid grid-cols-1 gap-4">
                                    <Input title="New Password" type="password" placeholder="Enter a new password" onChange={setNewPassword} />
                                    <Input
                                        title="Confirm Password"
                                        type="password"
                                        placeholder="Confirm the new password"
                                        onChange={setConfirmPassword}
                                    />
                                </div>
                                <div className="mt-4 flex justify-end">
                                    <Button
                                        title="Set Password"
                                        onClick={onSetPassword}
                                        className="rounded-xl"
                                        icon={<KeyRound size={18} />}
                                        disabled={!newPassword || newPassword !== confirmPassword}
                                    />
                                </div>
                            </div>

                            <div className="flex items-center justify-between gap-3 pt-2">
                                <p className="text-xs uppercase tracking-wide text-text-gray">Danger Zone</p>
                                <Button
                                    title="Delete User"
                                    onClick={onDeleteUser}
                                    className="rounded-xl"
                                    icon={<Trash2 size={18} />}
                                    disabled={user ? selectedUser.id === user.id : false}
                                />
                            </div>
                        </div>
                    )}
                </Modal>
            </div>
        </div>
    );
}
