/** @odoo-module **/

/**
 * Bind component methods to the instance.
 *
 * OWL 1.x rewrites free variables inside arrow expressions to captured values,
 * so `t-on-click="() => someMethod(x)"` captures the *unbound* prototype method
 * and invokes it bare, losing `this`. Binding the methods in `setup()` fixes it.
 */
export function bindAll(component, methodNames) {
    for (const name of methodNames) {
        if (typeof component[name] === "function") {
            component[name] = component[name].bind(component);
        }
    }
}

export function fileIcon(file) {
    if (file.isFolder) {
        return "fa-folder";
    }
    switch (file.kind) {
        case "image":
            return "fa-file-image-o";
        case "pdf":
            return "fa-file-pdf-o";
        case "word":
            return "fa-file-word-o";
        case "excel":
            return "fa-file-excel-o";
        case "csv":
            return "fa-table";
        default:
            return "fa-file-o";
    }
}

export function kindColor(file) {
    if (file.isFolder) {
        return "#f5c04b";
    }
    switch (file.kind) {
        case "image":
            return "#1f6feb";
        case "pdf":
            return "#d9381e";
        case "word":
            return "#1a7fbf";
        case "excel":
            return "#1a7f37";
        case "csv":
            return "#2f6f4f";
        default:
            return "#6e7781";
    }
}

export function formatDate(value) {
    if (!value) {
        return "";
    }
    const d = new Date(value);
    if (isNaN(d.getTime())) {
        return "";
    }
    return d.toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
    });
}

export function formatDateTime(value) {
    if (!value) {
        return "";
    }
    const d = new Date(value);
    if (isNaN(d.getTime())) {
        return "";
    }
    return d.toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

export function statusBadge(status) {
    const map = {
        draft: ["Draft", "#57606a"],
        under_review: ["Under Review", "#9a6700"],
        active: ["Active", "#1a7f37"],
        expired: ["Expired", "#d9381e"],
        archived: ["Archived", "#6e7781"],
    };
    return map[status] || ["", "#6e7781"];
}

export function grantLabel(grant) {
    if (grant.user_name) {
        return grant.user_name;
    }
    if (grant.role_name) {
        return grant.role_name + " (role)";
    }
    if (grant.team_name) {
        return grant.team_name + " (team)";
    }
    if (grant.department_name) {
        return grant.department_name + " (dept)";
    }
    return "Unknown";
}
