/** @odoo-module **/
import { Component } from "@odoo/owl";

export class ColumnChooser extends Component {
    static template = "gl_report.ColumnChooser";
}

ColumnChooser.props = ["columns", "onToggle", "onClose"];
