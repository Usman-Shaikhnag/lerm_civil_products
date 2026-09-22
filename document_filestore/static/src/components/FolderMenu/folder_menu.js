/** @odoo-module **/

import {
  Component,
  useState,
  onMounted,
  onWillUnmount,
  useRef,
} from "@odoo/owl";

export class FolderMenu extends Component {
  static template = "document_filestore.FolderMenu";

  static props = {
    folderId: String,
    folderName: String,
    onRename: { type: Function, optional: true },
    onDelete: Function,
    onUserRights: Function,
    onRenameFolder: Function,
    access: { type: String },
    currentUserId: Number,
    ownerId: Number,
  };

  setup() {
    this.state = useState({ isOpen: false });
    this.menuRef = useRef("menuRef");

    this.isOwner = () => {
      // env.session.uid = logged in user
      return Number(this.props.ownerId) === Number(this.props.currentUserId);
    };

    this.handleClickOutside = this.handleClickOutside.bind(this);

    onMounted(() =>
      document.addEventListener("click", this.handleClickOutside)
    );
    onWillUnmount(() =>
      document.removeEventListener("click", this.handleClickOutside)
    );
  }

  handleClickOutside(ev) {
    if (this.menuRef.el && !this.menuRef.el.contains(ev.target)) {
      this.state.isOpen = false;
    }
  }

  handleToggleMenu(ev) {
    ev.stopPropagation();
    this.state.isOpen = !this.state.isOpen;
  }

  handleRenameClick(ev) {
    ev.stopPropagation();
    this.props.onRenameFolder();
    this.state.isOpen = false;
  }

  handleDeleteClick() {
    if (
      confirm(`Are you sure you want to delete "${this.props.folderName}"?`)
    ) {
      this.props.onDelete(this.props.folderId);
    }
    this.state.isOpen = false;
  }

  handleUserRightsClick(ev) {
    ev.stopPropagation();
    this.props.onUserRights({
      id: this.props.folderId,
      name: this.props.folderName,
      isFolder: true,
    });
    this.state.isOpen = false;
  }

  get isRoot() {
    return this.props.folderId === "root";
  }
}
