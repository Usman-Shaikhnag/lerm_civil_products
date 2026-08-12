/** @odoo-module **/

import { Component, useState, useRef } from "@odoo/owl";
import { jsonrpc } from "@web/core/network/rpc_service";
import { bindAll } from "../../utils";

export class DMSUploadModal extends Component {
    static template = "document_management.DMSUploadModal";

    static props = {
        folderId: String,
        fastapiUrl: String,
        onClose: Function,
        onUploaded: Function,
    };

    setup() {
        this.fileInput = useRef("fileInput");
        this.state = useState({
            files: [],
            dragOver: false,
            uploading: false,
        });
        bindAll(this, [
            "openPicker",
            "onInputChange",
            "onDrop",
            "setDragOver",
            "addFiles",
            "removeFile",
            "startUpload",
            "uploadOne",
            "xhrUpload",
        ]);
    }

    openPicker() {
        this.fileInput.el.click();
    }

    onInputChange(ev) {
        this.addFiles(Array.from(ev.target.files || []));
        ev.target.value = "";
    }

    onDrop(ev) {
        ev.preventDefault();
        this.state.dragOver = false;
        this.addFiles(Array.from(ev.dataTransfer.files || []));
    }

    setDragOver(v) {
        this.state.dragOver = v;
    }

    addFiles(files) {
        const items = files.map((f) => ({
            file: f,
            name: f.name,
            size: f.size,
            progress: 0,
            status: "pending",
            error: "",
        }));
        this.state.files = this.state.files.concat(items);
    }

    removeFile(idx) {
        this.state.files.splice(idx, 1);
    }

    async startUpload() {
        if (this.state.uploading || this.state.files.length === 0) {
            return;
        }
        this.state.uploading = true;
        const done = [];
        for (let i = 0; i < this.state.files.length; i++) {
            const item = this.state.files[i];
            item.status = "uploading";
            try {
                const meta = await this.uploadOne(item, i);
                item.status = "done";
                item.progress = 100;
                done.push(meta);
            } catch (e) {
                item.status = "error";
                item.error = e.message || "Upload failed";
            }
        }
        this.state.uploading = false;
        if (done.length > 0) {
            this.props.onUploaded(done);
        }
    }

    async uploadOne(item, index) {
        const res = await jsonrpc("/dms/get_token", {
            folder_id: this.props.folderId === "root" ? false : parseInt(this.props.folderId),
            op: "upload",
        });
        const token = res.token;
        const formData = new FormData();
        formData.append("file", item.file, item.name);

        const result = await this.xhrUpload(
            `${this.props.fastapiUrl}/api/v1/files/upload?token=${encodeURIComponent(token)}`,
            formData,
            (pct) => (this.state.files[index].progress = pct)
        );

        const registered = await jsonrpc("/dms/register_upload", {
            name: result.name,
            original_name: item.name,
            folder_id:
                this.props.folderId === "root" ? false : parseInt(this.props.folderId),
            mime_type: result.mime,
            size: result.size,
            sha256: result.sha256,
            storage_path: result.storage_path,
        });
        return { name: result.name, id: registered.id };
    }

    xhrUpload(url, formData, onProgress) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open("POST", url);
            xhr.upload.onprogress = (ev) => {
                if (ev.lengthComputable) {
                    onProgress(Math.round((ev.loaded / ev.total) * 100));
                }
            };
            xhr.onload = () => {
                let data = {};
                try {
                    data = JSON.parse(xhr.responseText);
                } catch (e) {
                    data = { detail: xhr.responseText };
                }
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(data);
                } else {
                    reject(new Error(data.detail || "Upload failed"));
                }
            };
            xhr.onerror = () => reject(new Error("Network error during upload"));
            xhr.send(formData);
        });
    }
}
