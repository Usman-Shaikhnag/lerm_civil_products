/** @odoo-module **/

import { Component, useState, onWillUpdateProps } from "@odoo/owl";
import { bindAll } from "../../utils";

export class DMSHeader extends Component {
    static template = "document_management.DMSHeader";

    static props = {
        viewLabel: String,
        viewMode: String,
        onSetViewMode: Function,
        searchQuery: String,
        onSearch: Function,
        onUpload: Function,
        onNewFolder: Function,
        onToggleSidebar: Function,
        sidebarOpen: Boolean,
    };

    setup() {
        this.state = useState({ value: this.props.searchQuery });
        bindAll(this, ["onSearchInput"]);
        onWillUpdateProps((next) => {
            if (next.searchQuery !== this.props.searchQuery) {
                this.state.value = next.searchQuery;
            }
        });
    }

    onSearchInput(ev) {
        this.state.value = ev.target.value;
        this.props.onSearch(ev.target.value);
    }
}
