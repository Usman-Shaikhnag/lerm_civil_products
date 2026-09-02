/** @odoo-module **/
import { Component } from "@odoo/owl";

export class GroupHeader extends Component {
    static template = "gl_report.GroupHeader";
}

GroupHeader.props = ["group", "onToggle", "collapsed"];
