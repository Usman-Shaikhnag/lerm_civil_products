/** @odoo-module **/

import { Component } from "@odoo/owl";

export class Breadcrumbs extends Component {
    static template = "document_filestore.Breadcrumbs";
    static props = {
        breadcrumbs: { type: Array },           // [{ id, name }]
        onFolderClick: { type: Function, optional: true },
    };

    handleCrumbClick(id) {
        this.props.onFolderClick?.(id);
    }
}
