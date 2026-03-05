/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

const userMenu = registry.category("user_menuitems");

export class DriveSidebar extends Component {
  static template = "document_filestore.DriveSidebar";

  static props = {
    onFolderClick: Function,
    currentFolderId: String,
    onViewAllFolders: Function,
    viewAllFolders: Boolean,
    folders: Array,
  };

  handleSignOut() {
    const logoutItem = userMenu.get("logout");
    if (logoutItem?.callback) logoutItem.callback();
    else window.location.href = "/web/session/logout";
  }

  handleMyDriveClick() {
    this.props.onFolderClick("root");
  }

  get rootFolders() {
    // ✅ FIXED → Use "root" instead of null
    return this.props.folders.filter((f) => f.parentId === "root");
  }
}
