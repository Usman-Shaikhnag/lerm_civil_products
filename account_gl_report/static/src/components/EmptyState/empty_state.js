/** @odoo-module **/
import { Component } from "@odoo/owl";

export class EmptyState extends Component {
    static template = "gl_report.EmptyState";
}

EmptyState.props = ["onReset"];
