/** @odoo-module **/
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

const BUCKET_ORDER = ["0-30", "31-60", "61-90", "90+"];
const BUCKET_LABELS = {
    "0-30": "0-30 Days",
    "31-60": "31-60 Days",
    "61-90": "61-90 Days",
    "90+": "90+ Days",
};
const BUCKET_COLORS = {
    "0-30": "#10B981",
    "31-60": "#F59E0B",
    "61-90": "#F97316",
    "90+": "#EF4444",
};

export class AgeingDatagrid extends Component {
    static props = ["*"];
    static template = "customer_ageing_dashboard.AgeingDatagrid";

    get bucketKeys() {
        return BUCKET_ORDER;
    }

    bucketColor(key) {
        return BUCKET_COLORS[key] || "#8B5CF6";
    }

    formatAmount(v) {
        const n = parseFloat(v) || 0;
        return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    bucketLabel(key) {
        return BUCKET_LABELS[key] || key;
    }

    bucketTooltip(row, key) {
        const label = this.bucketLabel(key);
        const count = (row || {}).invoice_count;
        if (count) {
            return `${count} invoice${count !== 1 ? "s" : ""} in ${label} bucket`;
        }
        return `View invoices in ${label} bucket`;
    }

    onCellClick = (colKey, row, isTotalRow) => {
        this.props.onCellClick?.(colKey, row, isTotalRow);
    }
}

registry.category("components").add("AgeingDatagrid", AgeingDatagrid);
