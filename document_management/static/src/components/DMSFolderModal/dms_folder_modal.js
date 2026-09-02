/** @odoo-module **/

import { Component, useState, useRef } from "@odoo/owl";
import { bindAll } from "../../utils";

export class DMSFolderModal extends Component {
    static template = "document_management.DMSFolderModal";

    static props = {
        onClose: Function,
        onCreate: Function,
    };

    setup() {
        this.inputRef = useRef("nameInput");
        this.state = useState({ name: "" });
        bindAll(this, ["create", "onKeydown"]);
    }

    create() {
        const name = this.state.name.trim();
        if (!name) {
            return;
        }
        this.props.onCreate(name);
        this.props.onClose();
    }

    onKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.create();
        }
    }
}
