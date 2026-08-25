/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";
import { browser } from "@web/core/browser/browser";

import { DMSSidebar } from "../DMSSidebar/dms_sidebar";
import { DMSHeader } from "../DMSHeader/dms_header";
import { DMSBreadcrumbs } from "../DMSBreadcrumbs/dms_breadcrumbs";
import { DMSDrive } from "../DMSDrive/dms_drive";
import { DMSFilePreview } from "../DMSFilePreview/dms_file_preview";
import { DMSUploadModal } from "../DMSUploadModal/dms_upload_modal";
import { DMSFolderModal } from "../DMSFolderModal/dms_folder_modal";
import { DMSPropertiesPanel } from "../DMSPropertiesPanel/dms_properties_panel";
import { DMSPermissionsDialog } from "../DMSPermissionsDialog/dms_permissions_dialog";

const actionRegistry = registry.category("actions");

export class DMSApp extends Component {
    static components = {
        DMSSidebar,
        DMSHeader,
        DMSBreadcrumbs,
        DMSDrive,
        DMSFilePreview,
        DMSUploadModal,
        DMSFolderModal,
        DMSPropertiesPanel,
        DMSPermissionsDialog,
    };
    static template = "document_management.DMSApp";

    setup() {
        this.notification = useService("notification");
        this.state = useState({
            loading: true,
            config: null,
            viewMode: "grid",
            nav: "drive",
            currentFolderId: "root",
            folders: [],
            files: [],
            searchQuery: "",
            searchResults: [],
            searchLoading: false,
            searchActive: false,
            searchTotal: 0,
            previewFile: null,
            previewIndex: -1,
            uploadOpen: false,
            folderModalOpen: false,
            propsFile: null,
            permItem: null,
            sidebarOpen: false,
            meta: {
                users: [],
                tags: [],
                types: [],
                departments: [],
                teams: [],
                roles: [],
                projects: [],
                customers: [],
                vendors: [],
                employees: [],
                customFields: [],
                models: [],
            },
        });

        // Bind methods passed as props so child components keep the right `this`.
        const bound = [
            "fetchConfig",
            "fetchMeta",
            "fetchDrive",
            "refresh",
            "navigate",
            "selectNav",
            "toggleSidebar",
            "setViewMode",
            "setSearch",
            "searchDocuments",
            "clearSearch",
            "closeUpload",
            "closeFolderModal",
            "prevPreview",
            "nextPreview",
            "openUpload",
            "openFolderModal",
            "canWriteCurrent",
            "handleCreateFolder",
            "openPreview",
            "closePreview",
            "handleDownload",
            "handleToggleStar",
            "handleRename",
            "handleDelete",
            "openProperties",
            "closeProperties",
            "openPermissions",
            "closePermissions",
            "handleUploaded",
            "handleSaveProperties",
            "handleSavePermissions",
        ];
        for (const name of bound) {
            this[name] = this[name].bind(this);
        }

        onWillStart(async () => {
            await Promise.all([this.fetchConfig(), this.fetchMeta(), this.fetchDrive()]);
            this.state.loading = false;
        });
    }

    get fastapiUrl() {
        return (this.state.config && this.state.config.fastapi_url) || "";
    }

    get currentUserId() {
        return (this.state.config && this.state.config.user_id) || 0;
    }

    get currentFolder() {
        if (this.state.currentFolderId === "root") {
            return null;
        }
        return (
            this.state.folders.find((f) => String(f.id) === String(this.state.currentFolderId)) ||
            null
        );
    }

    get breadcrumbs() {
        const trail = [{ id: "root", name: "My Drive" }];
        if (this.state.currentFolderId === "root") {
            return trail;
        }
        const stack = [];
        let cur = this.currentFolder;
        while (cur) {
            stack.unshift({ id: String(cur.id), name: cur.name });
            cur = this.state.folders.find(
                (f) => String(f.id) === String(cur.parentId === "root" ? -1 : cur.parentId)
            );
            if (!cur) break;
        }
        return trail.concat(stack);
    }

    get currentItems() {
        if (this.state.searchActive) {
            return this.state.searchResults;
        }
        const q = (this.state.searchQuery || "").trim().toLowerCase();
        let items = [];
        if (this.state.nav === "recent") {
            items = this.state.files
                .slice()
                .sort((a, b) => (b.dateUploaded || "").localeCompare(a.dateUploaded || ""))
                .slice(0, 60);
        } else if (this.state.nav === "shared") {
            items = [
                ...this.state.folders.filter(
                    (f) => f.access.read && f.ownerId !== this.currentUserId
                ),
                ...this.state.files.filter(
                    (f) => f.access.read && f.ownerId !== this.currentUserId
                ),
            ];
        } else if (this.state.nav === "starred") {
            items = this.state.files.filter((f) => f.starred);
        } else {
            const id = this.state.currentFolderId;
            items = [
                ...this.state.folders.filter((f) => String(f.parentId) === String(id)),
                ...this.state.files.filter((f) => String(f.folderId) === String(id)),
            ];
        }
        if (q) {
            items = items.filter(
                (i) => (i.name || "").toLowerCase().includes(q) || (i.originalName || "").toLowerCase().includes(q)
            );
        }
        return items;
    }

    get currentViewLabel() {
        const map = {
            drive: "My Drive",
            recent: "Recent",
            shared: "Shared with me",
            starred: "Starred",
        };
        return map[this.state.nav] || "My Drive";
    }

    get starredCount() {
        return this.state.files.filter((f) => f.starred).length;
    }

    // ------------------------------------------------------------------
    // Data loading
    // ------------------------------------------------------------------
    async fetchConfig() {
        try {
            this.state.config = await jsonrpc("/dms/config", {});
        } catch (e) {
            this.toast("Failed to load DMS configuration", "danger");
        }
    }

    async fetchMeta() {
        const key = this.state.meta;
        const [users, tags, types, departments, teams, roles, projects, customers, vendors, employees, customFields, models] =
            await Promise.all([
                jsonrpc("/dms/meta/users", {}),
                jsonrpc("/dms/meta/tags", {}),
                jsonrpc("/dms/meta/document_types", {}),
                jsonrpc("/dms/meta/departments", {}),
                jsonrpc("/dms/meta/teams", {}),
                jsonrpc("/dms/meta/roles", {}),
                jsonrpc("/dms/meta/projects", {}),
                jsonrpc("/dms/meta/partners", { partner_type: "customer" }),
                jsonrpc("/dms/meta/partners", { partner_type: "vendor" }),
                jsonrpc("/dms/meta/employees", {}),
                jsonrpc("/dms/meta/custom_fields", {}),
                jsonrpc("/dms/meta/models", {}),
            ]);
        key.users = users || [];
        key.tags = tags || [];
        key.types = types || [];
        key.departments = departments || [];
        key.teams = teams || [];
        key.roles = roles || [];
        key.projects = projects || [];
        key.customers = customers || [];
        key.vendors = vendors || [];
        key.employees = employees || [];
        key.customFields = customFields || [];
        key.models = models || [];
    }

    async fetchDrive() {
        try {
            const data = await jsonrpc("/dms/get_drive_contents", {});
            this.state.folders = (data.folders || []).map((f) => ({
                ...f,
                isFolder: true,
                parentId: f.parentId || "root",
            }));
            this.state.files = (data.files || []).map((f) => ({
                ...f,
                isFolder: false,
            }));
            const map = {};
            for (const f of this.state.folders) {
                map[f.id] = f;
            }
            for (const f of this.state.files) {
                if (f.folderId !== "root" && map[f.folderId]) {
                    map[f.folderId].fileCount = (map[f.folderId].fileCount || 0) + 1;
                }
            }
        } catch (e) {
            this.toast("Failed to load documents", "danger");
        }
    }

    refresh() {
        return this.fetchDrive();
    }

    toast(message, type = "info") {
        this.notification.add(message, {
            type,
            title: type === "danger" ? "Error" : "Documents",
            sticky: type === "danger",
        });
    }

    // ------------------------------------------------------------------
    // Navigation / UI actions
    // ------------------------------------------------------------------
    navigate(folderId) {
        this.state.currentFolderId = String(folderId);
        this.state.nav = "drive";
        this.clearSearch();
        this.state.sidebarOpen = false;
    }

    selectNav(nav) {
        this.state.nav = nav;
        this.state.currentFolderId = "root";
        this.clearSearch();
    }

    toggleSidebar() {
        this.state.sidebarOpen = !this.state.sidebarOpen;
    }

    setViewMode(mode) {
        this.state.viewMode = mode;
    }

    setSearch(q) {
        this.state.searchQuery = q;
        this.state.searchActive = (q || "").trim().length > 0;
        if (this.searchTimer) {
            clearTimeout(this.searchTimer);
        }
        if (!this.state.searchActive) {
            this.state.searchResults = [];
            return;
        }
        this.searchTimer = setTimeout(() => this.searchDocuments(), 300);
    }

    async searchDocuments() {
        const term = (this.state.searchQuery || "").trim();
        if (!term) {
            this.state.searchResults = [];
            return;
        }
        const seq = (this._searchSeq || 0) + 1;
        this._searchSeq = seq;
        this.state.searchLoading = true;
        try {
            const res = await jsonrpc("/dms/search", { term, limit: 50 });
            if (seq !== this._searchSeq) {
                return;
            }
            this.state.searchResults = (res.files || []).map((f) => ({
                ...f,
                isFolder: false,
            }));
            this.state.searchTotal = res.total || 0;
        } catch (e) {
            if (seq !== this._searchSeq) {
                return;
            }
            this.state.searchResults = [];
            this.state.searchTotal = 0;
            this.toast(e.message?.data?.message || "Search failed", "danger");
        } finally {
            if (seq === this._searchSeq) {
                this.state.searchLoading = false;
            }
        }
    }

    clearSearch() {
        if (this.searchTimer) {
            clearTimeout(this.searchTimer);
        }
        this._searchSeq = (this._searchSeq || 0) + 1;
        this.state.searchQuery = "";
        this.state.searchResults = [];
        this.state.searchTotal = 0;
        this.state.searchActive = false;
        this.state.searchLoading = false;
    }

    closeUpload() {
        this.state.uploadOpen = false;
    }

    closeFolderModal() {
        this.state.folderModalOpen = false;
    }

    prevPreview() {
        this.previewAt(-1);
    }

    nextPreview() {
        this.previewAt(1);
    }

    openUpload() {
        if (!this.canWriteCurrent()) {
            this.toast("You do not have write permission here", "warning");
            return;
        }
        this.state.uploadOpen = true;
    }

    canWriteCurrent() {
        if (this.state.currentFolderId === "root") {
            return this.state.config && this.state.config.is_manager;
        }
        const folder = this.currentFolder;
        return folder && folder.access.write;
    }

    openFolderModal() {
        if (!this.canWriteCurrent()) {
            this.toast("You do not have write permission here", "warning");
            return;
        }
        this.state.folderModalOpen = true;
    }

    async handleCreateFolder(name) {
        if (!name) {
            return;
        }
        await jsonrpc("/web/dataset/call_kw", {
            model: "dms.folder",
            method: "create",
            args: [
                {
                    name,
                    parent_id:
                        this.state.currentFolderId === "root"
                            ? false
                            : parseInt(this.state.currentFolderId),
                },
            ],
            kwargs: {},
        });
        await this.refresh();
        this.toast("Folder created", "success");
    }

    openPreview(file, items) {
        const list = items || this.currentItems;
        this.state.previewIndex = list.findIndex((i) => i.id === file.id);
        this.state.previewFile = file;
    }

    closePreview() {
        this.state.previewFile = null;
        this.state.previewIndex = -1;
    }

    previewAt(offset) {
        const list = this.currentItems.filter((i) => !i.isFolder);
        const idx = this.state.previewIndex + offset;
        if (idx >= 0 && idx < list.length) {
            const file = list[idx];
            this.state.previewIndex = idx;
            this.state.previewFile = file;
        }
    }

    async handleDownload(file) {
        try {
            const res = await jsonrpc("/dms/get_token", {
                file_id: file.id,
                op: "download",
            });
            const url = `${this.fastapiUrl}/api/v1/files/content?token=${encodeURIComponent(res.token)}`;
            browser.open(url, "_blank");
        } catch (e) {
            this.toast(e.message?.data?.message || "Download failed", "danger");
        }
    }

    async handleToggleStar(file) {
        await jsonrpc("/dms/toggle_star", { file_id: file.id });
        file.starred = !file.starred;
    }

    async handleRename(item, newName) {
        if (!newName || newName === item.name) {
            return;
        }
        try {
            if (item.isFolder) {
                await jsonrpc("/web/dataset/call_kw", {
                    model: "dms.folder",
                    method: "write",
                    args: [[parseInt(item.id)], { name: newName }],
                    kwargs: {},
                });
            } else {
                await jsonrpc("/dms/rename_file", { file_id: item.id, new_name: newName });
            }
            await this.refresh();
            this.toast("Renamed", "success");
        } catch (e) {
            this.toast(e.message?.data?.message || "Rename failed", "danger");
        }
    }

    async handleDelete(item) {
        const confirmed = window.confirm(
            item.isFolder
                ? `Delete folder "${item.name}" and all of its contents?`
                : `Delete file "${item.name}"?`
        );
        if (!confirmed) {
            return;
        }
        try {
            if (item.isFolder) {
                await jsonrpc("/dms/delete_folder", { folder_id: item.id });
                if (this.state.currentFolderId === String(item.id)) {
                    this.state.currentFolderId = "root";
                }
            } else {
                await jsonrpc("/dms/delete_file", { file_id: item.id });
            }
            await this.refresh();
            this.toast("Deleted", "success");
        } catch (e) {
            this.toast(e.message?.data?.message || "Delete failed", "danger");
        }
    }

    async openProperties(file) {
        try {
            const detail = await jsonrpc("/dms/get_file/" + file.id, {});
            this.state.propsFile = detail;
        } catch (e) {
            this.toast(e.message?.data?.message || "Could not open details", "danger");
        }
    }

    closeProperties() {
        this.state.propsFile = null;
    }

    openPermissions(item) {
        this.state.permItem = item;
    }

    closePermissions() {
        this.state.permItem = null;
    }

    async handleUploaded(files) {
        await this.refresh();
        this.state.uploadOpen = false;
        this.toast(`${files.length} file(s) uploaded`, "success");
    }

    async handleSaveProperties(detail) {
        try {
            await jsonrpc("/dms/update_document/" + detail.id, detail);
            await this.refresh();
            this.toast("Document updated", "success");
        } catch (e) {
            this.toast(e.message?.data?.message || "Update failed", "danger");
        }
    }

    async handleSavePermissions(item, grants) {
        try {
            if (item.isFolder) {
                await jsonrpc("/dms/save_folder_permissions", {
                    folder_id: item.id,
                    grants,
                });
            } else {
                await jsonrpc("/dms/save_file_permissions", {
                    file_id: item.id,
                    grants,
                });
            }
            await this.refresh();
            this.toast("Permissions updated", "success");
        } catch (e) {
            this.toast(e.message?.data?.message || "Permission update failed", "danger");
        }
    }
}

actionRegistry.add("document_management", DMSApp);
