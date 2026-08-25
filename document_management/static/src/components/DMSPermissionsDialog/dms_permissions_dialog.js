/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";
import { grantLabel, bindAll } from "../../utils";

export class DMSPermissionsDialog extends Component {
    static template = "document_management.DMSPermissionsDialog";

    static props = {
        item: Object,
        meta: Object,
        onClose: Function,
        onSave: Function,
    };

    setup() {
        this.notification = useService("notification");
        this.state = useState({
            grants: [],
            owner: null,
            loading: true,
            principalType: "user",
            principalValue: false,
        });
        bindAll(this, ["load", "addGrant", "removeGrant", "grantName", "canManage", "save"]);
        this.load();
    }

    async load() {
        try {
            if (this.props.item.isFolder) {
                const data = await jsonrpc(`/dms/get_folder_permissions/${this.props.item.id}`, {});
                this.state.grants = data.permissions || [];
                this.state.owner = data.owner;
            } else {
                const data = await jsonrpc(`/dms/get_file_permissions/${this.props.item.id}`, {});
                this.state.grants = data.permissions || [];
                this.state.owner = data.owner;
            }
        } finally {
            this.state.loading = false;
        }
    }

    get principals() {
        const type = this.state.principalType;
        if (type === "user") return this.props.meta.users || [];
        if (type === "role") return this.props.meta.roles || [];
        if (type === "team") return this.props.meta.teams || [];
        return this.props.meta.departments || [];
    }

    addGrant() {
        const raw = this.state.principalValue;
        // The select's default option has value "false" (a string). Treat it
        // as "no selection" so we never add a grant without a principal.
        if (!raw || raw === "false") {
            this.notification.add("Please select a user, role, team or department first.", {
                type: "warning",
                title: "Permissions",
            });
            return;
        }
        const value = Number(raw);
        if (!value) {
            return;
        }
        const grant = {
            can_read: true,
            can_write: false,
            can_download: false,
            can_delete: false,
            can_manage: false,
        };
        if (this.state.principalType === "user") {
            const p = this.props.meta.users.find((u) => u.id === value);
            grant.user_id = value;
            grant.user_name = p ? p.name : "User";
        } else if (this.state.principalType === "role") {
            const p = this.props.meta.roles.find((u) => u.id === value);
            grant.role_id = value;
            grant.role_name = p ? p.name : "Role";
        } else if (this.state.principalType === "team") {
            const p = this.props.meta.teams.find((u) => u.id === value);
            grant.team_id = value;
            grant.team_name = p ? p.name : "Team";
        } else {
            const p = this.props.meta.departments.find((u) => u.id === value);
            grant.department_id = value;
            grant.department_name = p ? p.name : "Department";
        }
        this.state.grants.push(grant);
        this.state.principalValue = false;
    }

    removeGrant(idx) {
        this.state.grants.splice(idx, 1);
    }

    grantName(grant) {
        return grantLabel(grant);
    }

    canManage() {
        const item = this.props.item;
        return item.isFolder ? item.access.manage : item.access.manage;
    }

    save() {
        const toId = (v) => (v && v !== "false" ? Number(v) || false : false);
        const grants = this.state.grants
            .map((g) => ({
                user_id: toId(g.user_id),
                role_id: toId(g.role_id),
                team_id: toId(g.team_id),
                department_id: toId(g.department_id),
                can_read: g.can_read,
                can_write: g.can_write,
                can_download: g.can_download,
                can_delete: g.can_delete,
                can_manage: g.can_manage,
            }))
            .filter((g) => g.user_id || g.role_id || g.team_id || g.department_id);
        this.props.onSave(this.props.item, grants);
        this.props.onClose();
    }
}
