/** @odoo-module **/

import { Component, useRef } from "@odoo/owl";

export class DriveHeader extends Component {
  static template = "document_filestore.DriveHeader";

  static props = {
    folderName: String,
    onUploadClick: Function,
    onCreateFolder: { type: Function, optional: true },
    onSearch: { type: Function, optional: true },
    toggleSidebar: { type: Function, optional: true },
    isSidebarOpen: { type: Boolean, optional: true },
  };

  setup() {
    this.searchInput = useRef("searchInput");
  }

  handleCreateFolder() {
    this.props.onCreateFolder?.();
  }

  handleUploadClick() {
    this.props.onUploadClick();
  }

  handleSearchInput() {
    if (this.props.onSearch) {
      this.props.onSearch(this.searchInput.el.value);
    }
  }
}
