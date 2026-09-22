/** @odoo-module **/

import { Component } from "@odoo/owl";

export class DMSSidebarNode extends Component {
    static template = "document_management.DMSSidebarNode";
    static components = { DMSSidebarNode };

    static props = {
        folder: Object,
        folders: Array,
        currentFolderId: String,
        onNavigate: Function,
    };

    get children() {
        return this.props.folders.filter(
            (f) => String(f.parentId) === String(this.props.folder.id)
        );
    }

    get isActive() {
        return String(this.props.currentFolderId) === String(this.props.folder.id);
    }
}

export class DMSSidebar extends Component {
    static template = "document_management.DMSSidebar";
    static components = { DMSSidebarNode };

    static props = {
        folders: Array,
        currentFolderId: String,
        nav: String,
        onNavigate: Function,
        onSelectNav: Function,
        onToggleSidebar: Function,
        onToggleStar: Function,
        starredCount: Number,
    };

    get rootFolders() {
        return this.props.folders.filter((f) => f.parentId === "root");
    }
}
