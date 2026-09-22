/** @odoo-module **/
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

const BUCKET_META = {
    "0-30":  { label: "0-30 Days", color: "#10B981" },
    "31-60": { label: "31-60 Days", color: "#F59E0B" },
    "61-90": { label: "61-90 Days", color: "#F97316" },
    "90+":   { label: "90+ Days",  color: "#EF4444" },
};

export class AgeingBarChart extends Component {
    static props = ["*"];
    static template = "customer_ageing_dashboard.AgeingBarChart";

    get buckets() {
        return ["0-30", "31-60", "61-90", "90+"];
    }

    get maxValue() {
        const raw = this.props.buckets || {};
        return Math.max(...this.buckets.map((k) => parseFloat(raw[k]) || 0), 1);
    }

    getBarWidth(key) {
        const raw = parseFloat((this.props.buckets || {})[key]) || 0;
        return Math.max((raw / this.maxValue) * 100, raw > 0 ? 4 : 0);
    }

    getFormattedValue(key) {
        const n = parseFloat((this.props.buckets || {})[key]) || 0;
        return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    getMeta(key) {
        return BUCKET_META[key] || { label: key, color: "#8B5CF6" };
    }

    barStyle(widthPct, color) {
        return `width: ${widthPct}%; background: ${color};`;
    }

    isSmallBar(widthPct) {
        return widthPct <= 15;
    }
}

registry.category("components").add("AgeingBarChart", AgeingBarChart);
