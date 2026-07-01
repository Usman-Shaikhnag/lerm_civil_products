/** @odoo-module **/
import { Component } from "@odoo/owl";

export class SummaryCards extends Component {
    static template = "gl_report.SummaryCards";

    get cards() {
        if (!this.props.data) return [];
        const s = this.props.data.summary || {};
        return [
            { id: "opening", label: "Opening Balance", value: s.opening_balance, cssClass: this._balanceClass(s.opening_balance) },
            { id: "debit", label: "Total Debit", value: s.total_debit, cssClass: "card-debit" },
            { id: "credit", label: "Total Credit", value: s.total_credit, cssClass: "card-credit" },
            { id: "closing", label: "Closing Balance", value: s.closing_balance, cssClass: this._balanceClass(s.closing_balance) },
            { id: "count", label: "Transactions", value: s.transaction_count, cssClass: "" },
        ];
    }

    _balanceClass(val) {
        if (val > 0) return "card-positive";
        if (val < 0) return "card-negative";
        return "card-zero";
    }

    formatCurrency(val) {
        if (val == null) return "0.00";
        const num = typeof val === "number" ? val : parseFloat(val);
        return num.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }
}

SummaryCards.props = ["data", "loading"];
