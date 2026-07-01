/** @odoo-module **/
import { Component, onMounted, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { jsonrpc } from "@web/core/network/rpc_service";
import { useService } from "@web/core/utils/hooks";
import { AgeingBucketCard } from "../ageing_bucket_card/ageing_bucket_card";
import { AgeingBarChart } from "../ageing_barchart/ageing_barchart";
import { SalespersonFilter } from "../salesperson_filter/salesperson_filter";
import { AgeingDatagrid } from "../ageing_datagrid/ageing_datagrid";

const BUCKET_CONFIG = [
    { key: "0-30",  label: "0-30 Days",  color: "#10B981" },
    { key: "31-60", label: "31-60 Days", color: "#F59E0B" },
    { key: "61-90", label: "61-90 Days", color: "#F97316" },
    { key: "90+",   label: "90+ Days",   color: "#EF4444" },
];

class AgeingDashboard extends Component {
    static components = { AgeingBucketCard, AgeingBarChart, SalespersonFilter, AgeingDatagrid };
    static template = "customer_ageing_dashboard.AgeingDashboard";
    static props = ["*"];

    setup() {
        this.state = useState({
            salespersonIds: undefined,
            metrics: {},
            customers: [],
            totals: null,
            totalCount: 0,
            page: 1,
            limit: 50,
            search: "",
            asOf: new Date().toISOString().slice(0, 10),
        });
        this.action = useService("action");
        this._onFilterChange = this._onFilterChange.bind(this);
        this._onGridCellClick = this._onGridCellClick.bind(this);
    }

    async _fetchData() {
        const ids = this.state.salespersonIds;
        const payload = { as_of: this.state.asOf };
        if (ids !== undefined) {
            payload.salesperson_ids = ids;
        }
        try {
            const [metrics, customerData] = await Promise.all([
                jsonrpc("/customer_ageing/metrics", payload),
                jsonrpc("/customer_ageing/customers", {
                    ...payload,
                    limit: this.state.limit,
                    page: this.state.page,
                    search: this.state.search,
                }),
            ]);
            this.state.metrics = metrics;
            this.state.customers = customerData.rows || [];
            this.state.totals = customerData.totals || null;
            this.state.totalCount = customerData.total_count || 0;
        } catch (e) {
            console.error("AgeingDashboard fetch error", e);
        }
    }

    _onFilterChange(ids) {
        this.state.salespersonIds = ids.slice();
        this.state.page = 1;
        if (!ids || ids.length === 0) {
            this.state.metrics = {};
            this.state.customers = [];
            this.state.totals = null;
            return;
        }
        this._fetchData();
    }

    _onBucketClick(bucketKey) {
        this._navigateToDetail(bucketKey, null, "All Customers");
    }

    _onGridCellClick(colKey, row, isTotalRow) {
        if (colKey === "partner") {
            this._navigateToDetail(null, row.partner_id, row.partner_name);
        } else if (isTotalRow) {
            this._navigateToDetail(colKey === "total" ? null : colKey, null, "All Customers");
        } else {
            this._navigateToDetail(colKey === "total" ? null : colKey, row.partner_id, row.partner_name);
        }
    }

    _navigateToDetail(bucketKey, partnerId, partnerName) {
        const params = {
            bucket_key: bucketKey || "",
            partner_id: partnerId ? String(partnerId) : "",
            partner_name: partnerName || "",
            as_of: this.state.asOf,
        };
        const ids = this.state.salespersonIds;
        if (ids !== undefined) {
            params.salesperson_ids = JSON.stringify(ids);
        }
        this.action.doAction({
            type: "ir.actions.client",
            tag: "customer_ageing_detail_report",
            name: "Aged Payables Detail Report",
            params: params,
        });
    }

    get bucketConfig() {
        return BUCKET_CONFIG;
    }

    get bucketData() {
        const b = this.state.metrics.buckets || {};
        return BUCKET_CONFIG.map((cfg) => ({
            ...cfg,
            value: b[cfg.key] || 0,
            count: 0,
        }));
    }

    get formattedOutstanding() {
        const n = parseFloat(this.state.metrics.total_outstanding) || 0;
        return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    get totalCustomers() {
        return this.state.metrics.total_customers || 0;
    }

    get overdueCustomers() {
        return this.state.metrics.overdue_customers || 0;
    }

    get totalInvoices() {
        return this.state.metrics.total_invoices || 0;
    }

    get asOfDisplay() {
        return this.state.metrics.as_of || this.state.asOf;
    }

    onSearchInput(ev) {
        this.state.search = ev.target.value;
    }

    onSearchKeydown(ev) {
        if (ev.key === "Enter") {
            this.state.page = 1;
            this._fetchData();
        }
    }

    onSearchClick() {
        this.state.page = 1;
        this._fetchData();
    }

    onAsOfChange(ev) {
        this.state.asOf = ev.target.value;
    }

    onApplyDate() {
        this.state.page = 1;
        this._fetchData();
    }
}

registry.category("actions").add("customer_ageing_dashboard", AgeingDashboard);
