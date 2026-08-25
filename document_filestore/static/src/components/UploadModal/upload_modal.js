/** @odoo-module **/

import { Component, useState, useRef } from "@odoo/owl";

export class UploadModal extends Component {
  static template = "document_filestore.UploadModal";

  static props = {
    isOpen: Boolean,
    onClose: Function,
    currentFolderId: String, // "root" or actual folder id as string
    currentFolderName: { type: String, optional: true }, // ✅ new clean label
    onUploadComplete: Function,
  };

  setup() {
    this.inputRef = useRef("fileInput");
    this.state = useState({
      isUploading: false,
      uploadProgress: 0,
    });
  }

  async handleFileSelect() {
    const file = this.inputRef.el.files[0];
    if (!file) return;

    this.state.isUploading = true;
    this.state.uploadProgress = 0;

    const reader = new FileReader();

    reader.onprogress = (ev) => {
      if (ev.lengthComputable) {
        this.state.uploadProgress = Math.round((ev.loaded / ev.total) * 100);
      }
    };

    reader.onload = async (ev) => {
      const fileData = {
        name: file.name,
        type: file.type,
        size: file.size,
        data: ev.target.result, // base64 data URL
      };

      if (this.inputRef?.el) {
        this.inputRef.el.value = "";
      }
      this.state.isUploading = false;
      this.state.uploadProgress = 0;

      await this.props.onUploadComplete(fileData);
    };

    reader.onerror = () => {
      alert("Error reading file.");
      this.state.isUploading = false;
    };

    reader.readAsDataURL(file);
  }
}
