/** @odoo-module **/
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class AgeingBucketCard extends Component {
    static props = ["*"];
    static template = "customer_ageing_dashboard.AgeingBucketCard";

    get formattedValue() {
        const n = parseFloat(this.props.value) || 0;
        return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    get label() {
        return this.props.label || "";
    }

    get color() {
        return this.props.color || "#8B5CF6";
    }

    get count() {
        return this.props.count || 0;
    }

    onClick() {
        this.props.onClick?.(this.props.bucketKey);
    }
}

registry.category("components").add("AgeingBucketCard", AgeingBucketCard);
