/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { fileIcon, kindColor, formatDate, bindAll } from "../../utils";

export class DMSMenu extends Component {
    static template = "document_management.DMSMenu";

    static props = {
        item: Object,
        can: Function,
        onAction: Function,
    };
}

export class DMSDrive extends Component {
    static template = "document_management.DMSDrive";
    static components = { DMSMenu };

    static props = {
        items: Array,
        viewMode: String,
        currentFolderId: String,
        onFolderClick: Function,
        onFileClick: Function,
        onDownload: Function,
        onRename: Function,
        onDelete: Function,
        onStar: Function,
        onProperties: Function,
        onPermissions: Function,
    };

    setup() {
        this.state = useState({
            menuId: null,
            renamingId: null,
            renameInput: "",
        });
        bindAll(this, [
            "itemIcon",
            "itemColor",
            "itemMeta",
            "itemDate",
            "can",
            "handleItemClick",
            "toggleMenu",
            "startRename",
            "submitRename",
            "onRenameKeydown",
            "menuAction",
            "openRecord",
        ]);
    }

    itemIcon(item) {
        return fileIcon(item);
    }

    itemColor(item) {
        return kindColor(item);
    }

    itemMeta(item) {
        if (item.isFolder) {
            const count = item.itemCount || 0;
            return count === 1 ? "1 item" : `${count} items`;
        }
        return item.sizeDisplay || "";
    }

    itemDate(item) {
        return formatDate(item.dateUploaded || item.lastAccessDate);
    }

    can(item, flag) {
        return item.isFolder ? item.access[flag] : item.access[flag];
    }

    openRecord(item) {
        if (item.resModel && item.resId) {
            window.open(
                `/web#id=${item.resId}&model=${encodeURIComponent(item.resModel)}&view_type=form`,
                "_blank"
            );
        }
    }

    handleItemClick(item) {
        if (item.isFolder) {
            this.props.onFolderClick(item.id);
        } else {
            this.props.onFileClick(item);
        }
    }

    toggleMenu(item) {
        this.state.menuId = this.state.menuId === item.id ? null : item.id;
    }

    startRename(item) {
        this.state.menuId = null;
        this.state.renamingId = item.id;
        this.state.renameInput = item.name;
    }

    onRenameKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.submitRename();
        } else if (ev.key === "Escape") {
            this.state.renamingId = null;
        }
    }

    submitRename() {
        const id = this.state.renamingId;
        if (!id) return;
        const item = this.props.items.find((i) => i.id === id);
        if (item) {
            this.props.onRename(item, this.state.renameInput.trim());
        }
        this.state.renamingId = null;
    }

    menuAction(item, action) {
        this.state.menuId = null;
        switch (action) {
            case "open":
                if (item.isFolder) this.props.onFolderClick(item.id);
                else this.props.onFileClick(item);
                break;
            case "download":
                this.props.onDownload(item);
                break;
            case "rename":
                this.startRename(item);
                break;
            case "delete":
                this.props.onDelete(item);
                break;
            case "star":
                this.props.onStar(item);
                break;
            case "properties":
                this.props.onProperties(item);
                break;
            case "permissions":
                this.props.onPermissions(item);
                break;
        }
    }
}
