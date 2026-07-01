/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class MobileFilters extends Component {
    static template = "gl_report.MobileFilters";

    setup() {
        this.glData = useService("gl_report.data");
        this.localFilters = useState({ ...this.props.filters });
    }

    apply() {
        this.props.onApply({ ...this.localFilters });
    }
}

MobileFilters.props = ["filters", "onApply", "onClose"];
