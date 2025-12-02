/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { jsonrpc } from "@web/core/network/rpc_service";

export class UserRightsModal extends Component {
  static template = "document_filestore.UserRightsModal";

  // Props: support both file and folder
  static props = {
    itemId: String, // can be fileId or folderId
    itemName: String, // name of the file/folder
    isFolder: Boolean, // true if folder, false if file
    onClose: Function, // callback to close modal
  };

  setup() {
    this.state = useState({
      owner: null,
      users: [],
      selected: [],
      search: "",
      global_access: "view",
    });

    onWillStart(async () => {
      let data;

      // Fetch data based on item type
      if (this.props.isFolder) {
        data = await jsonrpc("/my_drive/get_available_users", {
          folder_id: this.props.itemId,
        });
      } else {
        data = await jsonrpc("/my_drive/get_file_permissions", {
          file_id: this.props.itemId,
        });
      }

      this.state.owner = data.owner;
      this.state.users = data.users;

      // Preselect users with existing permissions
      if (data.permissions) {
        this.state.selected = data.permissions.map((p) => ({
          user_id: p.user_id,
          name: p.name,
          access_level: p.access_level || "view",
        }));
      }

      // Determine if everyone has same access level (for global UI consistency)
      if (this.state.selected.length) {
        const unique = new Set(this.state.selected.map((u) => u.access_level));
        if (unique.size === 1) {
          this.state.global_access = this.state.selected[0].access_level;
        }
      }
    });
  }

  // --- Helpers ---
  findDuplicates(list) {
    const seen = new Set();
    const duplicates = [];
    for (const item of list) {
      if (seen.has(item.user_id)) {
        duplicates.push(item);
      } else {
        seen.add(item.user_id);
      }
    }
    return duplicates;
  }

  addUser(user) {
    if (!this.state.selected.some((u) => u.user_id === user.id)) {
      this.state.selected.push({
        user_id: user.id,
        name: user.name,
        access_level: this.state.global_access,
      });
    }
  }

  removeUser(user_id) {
    // Prevent deleting the owner
    if (this.state.owner && this.state.owner.user_id === user_id) return;
    this.state.selected = this.state.selected.filter(
      (u) => u.user_id !== user_id
    );
  }

  // --- Save Permissions ---
  async save() {
    const finalPermissions = this.state.selected.map((u) => ({
      user_id: u.user_id,
      access_level: this.state.global_access || u.access_level,
    }));
    
    if (this.props.isFolder) {
      await jsonrpc("/my_drive/save_folder_permissions", {
        folder_id: parseInt(this.props.itemId),
        permissions: finalPermissions,
      });
    } else {
      // debugger;
      await jsonrpc("/my_drive/save_file_permissions", {
        file_id: parseInt(this.props.itemId),
        permissions: finalPermissions,
      });
    }

    this.props.onClose();
  }
}
