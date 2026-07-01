/** @odoo-module **/
import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { jsonrpc } from "@web/core/network/rpc_service";
import { useService } from "@web/core/utils/hooks";

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

const BUCKET_ORDER = ["0-30", "31-60", "61-90", "90+"];

class AgeingDetailReport extends Component {
    static template = "customer_ageing_dashboard.AgeingDetailReport";
    static props = ["*"];

    setup() {
        this.state = useState({
            loading: true,
            allInvoices: [],
            invoices: [],
            total: 0,
            invoiceCount: 0,
            partnerName: "",
            bucketKey: null,
            asOf: "",
            avgAgingDays: 0,
            highestBucket: "",
            highestInvoice: "",
            trend: {},
            trendMax: 1,
            renderKey: 0,
            filterBucket: null,
        });
        this.action = useService("action");

        this.filterByBucket = this.filterByBucket.bind(this);
        this.clearFilter = this.clearFilter.bind(this);
        this.openInvoice = this.openInvoice.bind(this);
        this.goBack = this.goBack.bind(this);

        onWillStart(async () => {
            await this._loadData();
        });
    }

    async _loadData() {
        const action = this.props.action || {};
        const params = action.params || {};

        this.state.bucketKey = params.bucket_key || null;
        this.state.partnerName = params.partner_name || "";
        this.state.asOf = params.as_of || "";

        const payload = {};
        if (params.as_of) payload.as_of = params.as_of;
        if (params.partner_id) payload.partner_id = parseInt(params.partner_id, 10);
        if (params.bucket_key) payload.bucket_key = params.bucket_key;
        if (params.salesperson_ids) {
            try {
                payload.salesperson_ids = JSON.parse(params.salesperson_ids);
            } catch (e) {}
        }

        try {
            const result = await jsonrpc("/customer_ageing/detail_invoices", payload);
            this.state.allInvoices = result.invoices || [];
            this.state.total = result.total || 0;
            this.state.invoiceCount = result.invoice_count || 0;
            this.state.avgAgingDays = result.avg_aging_days || 0;
            this.state.highestBucket = result.highest_bucket || "";
            this.state.highestInvoice = result.highest_invoice || "";
            this.state.trend = result.trend || {};
            this.state.trendMax = result.trend_max || 1;
            this.state.invoices = result.invoices || [];
            if (result.partner_name) {
                this.state.partnerName = result.partner_name;
            }
        } catch (e) {
            console.error("Detail report fetch error", e);
        } finally {
            this.state.loading = false;
        }
    }

    get bucketLabel() {
        if (!this.state.bucketKey) return "All Outstanding";
        return BUCKET_LABELS[this.state.bucketKey] || this.state.bucketKey;
    }

    get highestBucketLabel() {
        if (!this.state.highestBucket) return "\u2014";
        return BUCKET_LABELS[this.state.highestBucket] || this.state.highestBucket;
    }

    get bucketDistribution() {
        const buckets = { "0-30": 0, "31-60": 0, "61-90": 0, "90+": 0 };
        for (const inv of this.state.allInvoices) {
            const key = inv.aging_bucket;
            if (key in buckets) {
                buckets[key] += inv.outstanding_balance;
            }
        }
        const total = this.state.total || 1;
        return BUCKET_ORDER.map((key) => ({
            key,
            label: BUCKET_LABELS[key],
            color: BUCKET_COLORS[key],
            amount: buckets[key],
            percentage: (buckets[key] / total) * 100,
        }));
    }

    get riskInsights() {
        const insights = [];
        const distrib = this.bucketDistribution;
        const oldBucket = distrib.find((b) => b.key === "90+");
        if (oldBucket && oldBucket.percentage > 20) {
            insights.push({
                icon: "fa-circle-exclamation",
                color: "#EF4444",
                text: `${Math.round(oldBucket.percentage)}% of receivables are overdue 90+ days`,
            });
        }
        if (this.state.highestInvoice) {
            insights.push({
                icon: "fa-triangle-exclamation",
                color: "#F59E0B",
                text: `Highest overdue invoice: ${this.state.highestInvoice}`,
            });
        }
        if (this.state.avgAgingDays > 30) {
            insights.push({
                icon: "fa-chart-line",
                color: "#3B82F6",
                text: `Average ageing is ${this.state.avgAgingDays} days`,
            });
        }
        if (!insights.length) {
            insights.push({
                icon: "fa-circle-check",
                color: "#10B981",
                text: "No significant risk indicators detected",
            });
        }
        return insights;
    }

    get displayedInvoices() {
        if (!this.state.filterBucket) return this.state.allInvoices;
        return this.state.allInvoices.filter(
            (inv) => inv.aging_bucket === this.state.filterBucket
        );
    }

    get displayedTotal() {
        if (!this.state.filterBucket) return this.state.total;
        return this.displayedInvoices.reduce(
            (sum, inv) => sum + (inv.outstanding_balance || 0), 0
        );
    }

    get displayedCount() {
        if (!this.state.filterBucket) return this.state.invoiceCount;
        return this.displayedInvoices.length;
    }

    get activeFilterLabel() {
        if (!this.state.filterBucket) return "";
        return BUCKET_LABELS[this.state.filterBucket] || this.state.filterBucket;
    }

    formatAmount(v) {
        const n = parseFloat(v) || 0;
        return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    formatDate(d) {
        return d || "";
    }

    _csvEscape(val) {
        const s = String(val || "");
        if (s.includes(",") || s.includes('"') || s.includes("\n")) {
            return '"' + s.replace(/"/g, '""') + '"';
        }
        return s;
    }

    exportExcel() {
        const rows = this.displayedInvoices;
        const headers = ["Invoice Date", "Due Date", "Invoice Number", "Original Amount", "Outstanding Balance", "Aging Days", "Aging Bucket"];
        let csv = headers.join(",") + "\n";
        for (const inv of rows) {
            csv += [
                this._csvEscape(this.formatDate(inv.invoice_date)),
                this._csvEscape(this.formatDate(inv.due_date)),
                this._csvEscape(inv.invoice_number),
                this.formatAmount(inv.original_amount),
                this.formatAmount(inv.outstanding_balance),
                inv.aging_days,
                this._csvEscape(inv.aging_bucket),
            ].join(",") + "\n";
        }
        csv += "\n";
        csv += ["Total", "", "", "", this.formatAmount(this.displayedTotal), "", ""].join(",") + "\n";
        const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8;bom" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        const partner = (this.state.partnerName || "all_customers").replace(/\s+/g, "_");
        const bucket = (this.state.bucketKey || "all").replace("-", "_");
        link.download = `ageing_detail_${partner}_${bucket}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
    }

    exportPdf() {
        window.print();
    }

    filterByBucket(key) {
        if (this.state.filterBucket === key) {
            this.state.filterBucket = null;
        } else {
            this.state.filterBucket = key;
        }
    }

    clearFilter() {
        this.state.filterBucket = null;
    }

    openInvoice(invoiceId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Invoice",
            res_model: "account.move",
            res_id: invoiceId,
            view_mode: "form",
            views: [[false, "form"]],
        });
    }

    goBack() {
        this.action.doAction({
            type: "ir.actions.client",
            tag: "customer_ageing_dashboard",
            name: "Customer Ageing Dashboard",
            target: "current",
        });
    }
}

registry.category("actions").add("customer_ageing_detail_report", AgeingDetailReport);
