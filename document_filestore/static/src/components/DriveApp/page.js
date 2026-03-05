/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { jsonrpc } from "@web/core/network/rpc_service";
import { DriveSidebar } from "../DriveSidebar/drive_sidebar";
import { DriveHeader } from "../DriveHeader/drive_header";
import { DriveContainer } from "../DriveContainer/drive_container";
import { Breadcrumbs } from "../Breadcrumbs/breadcrumbs";
import { UploadModal } from "../UploadModal/upload_modal";
import { FilePreview } from "../FilePreview/file_preview";
import { UserRightsModal } from "../UserRightsModal/user_rights_modal";

const actionRegistry = registry.category("actions");

class DriveApp extends Component {
  static components = {
    DriveSidebar,
    DriveHeader,
    DriveContainer,
    Breadcrumbs,
    UploadModal,
    FilePreview,
    UserRightsModal,
  };
  static template = "document_filestore.DriveApp";

  setup() {
    this.state = useState({
      currentFolderId: "root",
      folders: [],
      files: [],
      viewAllFolders: false,
      dataLoading: true,
      isUploadModalOpen: false,
      newFolderCount: 0,
      selectedFile: null,
      userRightsModalOpen: false,
      activeFolderForRights: null,
      activeItem: null,
    });
    this.handleFolderClick = this.handleFolderClick.bind(this);
    this.handleViewAllFolders = this.handleViewAllFolders.bind(this);
    this.handleCreateFolder = this.handleCreateFolder.bind(this);
    this.handleFileClick = this.handleFileClick.bind(this);
    this.closePreview = this.closePreview.bind(this);
    this.handleRenameFolder = this.handleRenameFolder.bind(this);
    this.handleDeleteFolder = this.handleDeleteFolder.bind(this);
    this.handleUserRights = this.handleUserRights.bind(this);
    this.handleUploadComplete = this.handleUploadComplete.bind(this);
    this.handleRenameFile = this.handleRenameFile.bind(this);
    this.handleDeleteFile = this.handleDeleteFile.bind(this);

    onWillStart(async () => {
      await this.fetchFoldersAndFiles();
    });
  }
  // ---------- Data ----------
  async fetchFoldersAndFiles() {
    this.state.dataLoading = true;
    try {
      const data = await jsonrpc("/my_drive/get_drive_contents", {});

      // Convert incoming data first
      const folders = (data.folders || []).map((f) => ({
        ...f,
        parentId: f.parentId || "root",
        isFolder: true,
      }));

      const files = data.files || [];
      folders.forEach((folder) => {
        const childFolders = folders.filter(
          (f) => f.parentId === folder.id
        ).length;
        const childFiles = files.filter((f) => f.parentId === folder.id).length;
        folder.itemCount = childFolders + childFiles;
      });

      // ✅ Save back to state
      this.state.folders = folders;
      this.state.files = files;
      // console.log("Files", this.state.files);
    } finally {
      this.state.dataLoading = false;
    }
  }

  get breadcrumbs() {
    const trail = [{ id: "root", name: "My Drive" }];
    if (this.state.currentFolderId === "root" || this.state.viewAllFolders)
      return trail;

    let cur = this.state.folders.find(
      (f) => f.id === this.state.currentFolderId
    );
    const stack = [];
    while (cur) {
      stack.unshift({ id: cur.id, name: cur.name });
      cur = this.state.folders.find((f) => f.id === cur.parentId);
    }
    return trail.concat(stack);
  }

  get currentFolderName() {
    if (this.state.viewAllFolders) return "All Folders";
    if (this.state.currentFolderId === "root") return "My Drive";
    const f = this.state.folders.find(
      (x) => x.id === this.state.currentFolderId
    );
    return f ? f.name : "My Drive";
  }

  get currentItems() {
    if (this.state.viewAllFolders)
      return [...this.state.folders, ...this.state.files];

    const id = this.state.currentFolderId;
    // console.log("CurrentItems - currentFolderId", this.state.currentFolderId);

    return [
      ...this.state.folders.filter((f) => f.parentId === id),
      ...this.state.files.filter((f) => f.parentId === id),
    ];
  }

  // ---------- Handlers required by children ----------
  handleFolderClick(folderId) {
    this.state.currentFolderId = folderId;
    this.state.viewAllFolders = false;
  }

  handleViewAllFolders() {
    this.state.viewAllFolders = true;
  }

  async handleCreateFolder() {
    const name = `New Folder ${this.state.newFolderCount + 1}`;
    this.state.newFolderCount += 1;

    await jsonrpc("/web/dataset/call_kw", {
      model: "document.folder",
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
    await this.fetchFoldersAndFiles();
  }

  handleFileClick(file) {
    this.state.selectedFile = file;
  }

  closePreview() {
    this.state.selectedFile = null;
  }

  async handleRenameFolder(folderId, newName) {
    await jsonrpc("/web/dataset/call_kw", {
      model: "document.folder",
      method: "write",
      args: [[parseInt(folderId)], { name: newName }],
      kwargs: {},
    });
    await this.fetchFoldersAndFiles();
  }

  async handleDeleteFolder(folderId) {
    await jsonrpc("/web/dataset/call_kw", {
      model: "document.folder",
      method: "unlink",
      args: [[parseInt(folderId)]],
      kwargs: {},
    });
    if (this.state.currentFolderId === folderId) {
      this.state.currentFolderId = "root";
    }
    await this.fetchFoldersAndFiles();
  }

  handleUserRights(item) {
    // console.log("✅ Opening UserRightsModal for folder:", folderId);
    this.state.activeItem = item;
    // this.state.activeFolderForRights = folderId;
    this.state.userRightsModalOpen = true;
  }

  async handleUploadComplete(file) {
    // file = { name, type, size, data(base64 dataURL) }
    const base64Data = file.data.split(",")[1];
    const folderId =
      this.state.currentFolderId === "root"
        ? false
        : parseInt(this.state.currentFolderId);

    try {
      this.state.dataLoading = true;
      const newFileRecord = await jsonrpc("/web/dataset/call_kw", {
        model: "document.file",
        method: "create_and_store_file",
        args: [
          {
            name: file.name,
            type: file.type,
            size: file.size,
            file_base64: base64Data,
          },
          folderId,
        ],
        kwargs: {},
      });
      // Optionally cache locally if needed
      // console.log("Uploaded:", newFileRecord);
      await this.fetchFoldersAndFiles();
    } catch (e) {
      console.error("Upload error:", e);
    } finally {
      this.state.dataLoading = false;
      this.state.isUploadModalOpen = false;
    }
  }

  async handleRenameFile(fileId, newName) {
    await jsonrpc("/web/dataset/call_kw", {
      model: "document.file",
      method: "write",
      args: [[parseInt(fileId)], { name: newName }],
      kwargs: {},
    });
    await this.fetchFoldersAndFiles();
  }
  async handleDeleteFile(fileId) {
    await jsonrpc("/web/dataset/call_kw", {
      model: "document.file",
      method: "unlink",
      args: [[parseInt(fileId)]],
      kwargs: {},
    });
    await this.fetchFoldersAndFiles();
  }
}

actionRegistry.add("document_filestore", DriveApp);
