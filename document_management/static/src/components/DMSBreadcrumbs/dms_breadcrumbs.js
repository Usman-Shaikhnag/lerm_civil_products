/** @odoo-module **/

import { Component } from "@odoo/owl";

export class DMSBreadcrumbs extends Component {
    static template = "document_management.DMSBreadcrumbs";

    static props = {
        crumbs: Array,
        onNavigate: Function,
    };
}
