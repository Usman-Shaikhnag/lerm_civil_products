/** @odoo-module **/

import { Component, useState, onWillStart, onWillUpdateProps } from "@odoo/owl";
import { jsonrpc } from "@web/core/network/rpc_service";

export class DMSFilePreview extends Component {
    static template = "document_management.DMSFilePreview";

    static props = {
        file: Object,
        fastapiUrl: String,
        onClose: Function,
        onDownload: Function,
        onPrev: Function,
        onNext: Function,
    };

    setup() {
        this.state = useState({
            previewUrl: "",
            loading: true,
            error: "",
        });
        this.loadPreview();
        onWillUpdateProps(() => this.loadPreview());
    }

    async loadPreview() {
        this.state.loading = true;
        this.state.error = "";
        try {
            const res = await jsonrpc("/dms/get_token", {
                file_id: this.props.file.id,
                op: "preview",
            });
            this.state.previewUrl =
                `${this.props.fastapiUrl}/api/v1/files/preview?token=${encodeURIComponent(res.token)}`;
        } catch (e) {
            this.state.error = e.message?.data?.message || "Preview not available";
        } finally {
            this.state.loading = false;
        }
    }

    get kind() {
        return this.props.file.kind;
    }

    canPreview() {
        return ["pdf", "word", "excel", "csv", "image"].includes(this.kind);
    }

    canDownload() {
        const access = this.props.file.access;
        return !!(access && access.download);
    }
}
