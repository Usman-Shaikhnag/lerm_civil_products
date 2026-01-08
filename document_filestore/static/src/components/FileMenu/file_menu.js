/** @odoo-module **/

import {
  Component,
  useState,
  onMounted,
  onWillUnmount,
  useRef,
  onWillStart,
} from "@odoo/owl";

export class FileMenu extends Component {
  static template = "document_filestore.FileMenu";

  static props = {
    fileId: { type: String },
    fileName: { type: String },
    ownerId: Number,
    currentUserId: Number,
    downloadUrl: { type: String },
    onRenameFile: { type: Function },
    onDeleteFile: { type: Function },
    onUserRights: { type: Function, optional: true },
    access: String,
  };

  setup() {
    this.state = useState({ isOpen: false });
    this.menuRef = useRef("menuRef");

    this.isOwner = () => {
      // env.session.uid = logged in user
      return Number(this.props.ownerId) === Number(this.props.currentUserId);
    };
    this.handleClickOutside = this.handleClickOutside.bind(this);
    this.handleManageAccessClick = this.handleManageAccessClick.bind(this);
    onMounted(() =>
      document.addEventListener("click", this.handleClickOutside)
    );
    onWillUnmount(() =>
      document.removeEventListener("click", this.handleClickOutside)
    );
    // onWillStart(() => {
    //   console.log(this.props.access);
    // });
  }

  handleClickOutside(ev) {
    if (
      this.state.isOpen &&
      this.menuRef.el &&
      !this.menuRef.el.contains(ev.target)
    ) {
      this.state.isOpen = false;
    }
  }

  toggleMenu(ev) {
    ev.stopPropagation();
    this.state.isOpen = !this.state.isOpen;
  }

  rename() {
    if (this.props.access === "view") return;
    this.props.onRenameFile(this.props.fileId, this.props.fileName);
    this.state.isOpen = false;
  }

  delete() {
    if (this.props.access !== "full") return;
    if (confirm(`Delete file "${this.props.fileName}"?`)) {
      this.props.onDeleteFile(this.props.fileId);
    }
    this.state.isOpen = false;
  }
  get canEdit() {
    return this.props.access === "edit" || this.props.access === "full";
  }

  get canDelete() {
    return this.props.access === "full";
  }

  handleManageAccessClick(ev) {
    ev.stopPropagation();
    this.props.onUserRights({
      id: this.props.fileId,
      name: this.props.fileName,
      isFolder: false,
    });
    this.state.isOpen = false;
  }
}
