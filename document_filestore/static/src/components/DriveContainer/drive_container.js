/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { FolderMenu } from "../FolderMenu/folder_menu";
import { FileMenu } from "../FileMenu/file_menu";

export class DriveContainer extends Component {
  static template = "document_filestore.DriveContainer";
  static components = { FolderMenu, FileMenu };

  // Accept exactly what the template passes, with types
  static props = {
    items: Array,
    onFolderClick: Function,
    onFileClick: Function,
    currentFolderId: String,
    folders: { type: Array, optional: true }, // kept optional for compatibility
    onRenameFolder: Function,
    onDeleteFolder: Function,
    onUserRights: Function,
    onRenameFile: { type: Function },
    onDeleteFile: { type: Function },
  };

  setup() {
    this.state = useState({
      renamingId: null,
      renameInput: "",
      activeItem: null,
      dataLoading: false,
    });
    // onWillStart(() => {
    //   console.log("Drive Container Flies",this.props.items);
    // });
    // this.openFileUserRights = this.openFileUserRights.bind(this);
  }

  handleStartRename(itemId, currentName) {
    this.state.renamingId = itemId;
    this.state.renameInput = currentName;
  }

  handleRenameKeydown(ev) {
    if (ev.key === "Enter") {
      this.handleRenameSubmit();
      ev.preventDefault();
      ev.stopPropagation();
    } else if (ev.key === "Escape") {
      this.state.renamingId = null;
      this.state.renameInput = "";
      ev.preventDefault();
      ev.stopPropagation();
    }
  }

  handleRenameInputBlur() {
    this.handleRenameSubmit();
  }

  async handleRenameSubmit() {
    const id = this.state.renamingId;
    if (!id) return;

    const item = this.props.items.find((i) => i.id === id);
    const originalName = item?.name;
    const newName = this.state.renameInput.trim();

    if (newName && newName !== originalName) {
      if (item.isFolder) {
        await this.props.onRenameFolder(id, newName);
      } else {
        await this.props.onRenameFile(id, newName); // ✅ FILE RENAME FIX
      }
    }

    this.state.renamingId = null;
    this.state.renameInput = "";
  }

  async handleRenameFile(fileId, newName) {
    await this.props.onRenameFile(fileId, newName);
    this.state.renamingId = null;
    this.state.renameInput = "";
  }

  // async openFileUserRights(item) {
  //   debugger;
  //   this.state.activeItem = item;
  //   this.state.isPermissionModalOpen = true;
  // }
}
