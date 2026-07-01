/** @odoo-module **/
import { Component } from "@odoo/owl";

export class ExportDialog extends Component {
    static template = "gl_report.ExportDialog";
}

ExportDialog.props = ["exporting", "totalRecords", "onExport", "onClose"];
