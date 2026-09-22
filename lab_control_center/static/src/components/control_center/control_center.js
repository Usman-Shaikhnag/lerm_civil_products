/** @odoo-module */
import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";

const actionRegistry = registry.category("actions");

class ControlCenter extends Component {
    setup() {
        this.action = useService("action");
        this.state = useState({
            role: "",
            role_label: "",
            scope_label: "",
            kpis: {},
            attention: {},
            pipeline: [],
            workload: [],
            aging: [],
            priority: [],
            priority_total: 0,
            companies: [],
            labs: [],
            disciplines: [],
        });
        this.filters = useState({
            as_of: this._today(),
            company_id: "ALL",
            lab_id: "ALL",
            discipline_id: "ALL",
            search: "",
            loading: false,
            loaded: false,
        });
        this._searchTimer = null;

        this.KPI_CONFIG = [
            { key: "total", label: "Total", icon: "fa-cubes", color: "#1d4ed8", action: "total" },
            { key: "overdue", label: "Overdue", icon: "fa-exclamation-triangle", color: "#dc2626", action: "overdue" },
            { key: "due_today", label: "Due Today", icon: "fa-clock-o", color: "#ea580c", action: "due_today" },
            { key: "testing", label: "Testing", icon: "fa-flask", color: "#2563eb", action: "testing" },
            { key: "approval", label: "Approval", icon: "fa-check-double", color: "#7c3aed", action: "approval" },
        ];
        this.ATTENTION_CONFIG = [
            { key: "overdue", label: "Overdue", icon: "fa-exclamation-triangle", color: "#dc2626", action: "overdue" },
            { key: "due_today", label: "Due Today", icon: "fa-clock-o", color: "#ea580c", action: "due_today" },
            { key: "at_risk", label: "At Risk", icon: "fa-warning", color: "#d97706", action: "at_risk" },
            { key: "approval", label: "Approval", icon: "fa-check-double", color: "#7c3aed", action: "approval" },
        ];
        this.FLAG_CONFIG = {
            overdue: { label: "Overdue", color: "#dc2626", bg: "#fee2e2" },
            due_today: { label: "Due Today", color: "#ea580c", bg: "#ffedd5" },
            at_risk: { label: "At Risk", color: "#b45309", bg: "#fef3c7" },
        };

        onWillStart(async () => {
            await this._loadOptions();
            await this.fetchData();
        });
    }

    get isManagement() {
        return this.state.role === "management";
    }

    get hasAccess() {
        return this.state.role !== "none";
    }

    get kpiCards() {
        return this.KPI_CONFIG.map((cfg) => ({
            ...cfg,
            count: this.state.kpis[cfg.key] || 0,
        }));
    }

    get attentionItems() {
        return this.ATTENTION_CONFIG.map((cfg) => ({
            ...cfg,
            count: this.state.attention[cfg.key] || 0,
        }));
    }

    get maxWorkload() {
        const max = Math.max(...this.state.workload.map((w) => w.count), 0);
        return max || 1;
    }

    get maxAging() {
        const max = Math.max(...this.state.aging.map((a) => a.count), 0);
        return max || 1;
    }

    get filteredLabs() {
        if (!this.isManagement) return [];
        if (this.filters.company_id === "ALL") return this.state.labs;
        const companyId = parseInt(this.filters.company_id, 10);
        return this.state.labs.filter((l) => l.company_id === companyId);
    }

    _today() {
        return new Date().toISOString().split("T")[0];
    }

    _fmtDate(value) {
        if (!value) return "—";
        const d = new Date(value + "T00:00:00");
        if (isNaN(d.getTime())) return value;
        const pad = (n) => n.toString().padStart(2, "0");
        const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        return `${pad(d.getDate())} ${months[d.getMonth()]} ${d.getFullYear()}`;
    }

    _pct(count, total) {
        return Math.max(4, Math.round((count / total) * 100));
    }

    _rpcPayload() {
        return {
            as_of: this.filters.as_of,
            company_id: this.filters.company_id,
            lab_id: this.filters.lab_id,
            discipline_id: this.filters.discipline_id,
            search: this.filters.search,
        };
    }

    async _loadOptions() {
        try {
            const opts = await jsonrpc("/labcc/options", {});
            this.state.role = opts.role;
            this.state.role_label = opts.role_label;
            this.state.scope_label = opts.scope_label;
            this.state.companies = opts.companies || [];
            this.state.labs = opts.labs || [];
            this.state.disciplines = opts.disciplines || [];
        } catch (error) {
            console.error("Failed to load control center options:", error);
        }
    }

    async fetchData() {
        this.filters.loading = true;
        try {
            const data = await jsonrpc("/labcc/data", this._rpcPayload());
            this.state.role = data.role;
            this.state.role_label = data.role_label;
            this.state.kpis = data.kpis || {};
            this.state.attention = data.attention || {};
            this.state.pipeline = data.pipeline || [];
            this.state.workload = data.workload || [];
            this.state.aging = data.aging || [];
            this.state.priority = data.priority || [];
            this.state.priority_total = data.priority_total || 0;
        } catch (error) {
            console.error("Failed to fetch control center data:", error);
        } finally {
            this.filters.loading = false;
            this.filters.loaded = true;
        }
    }

    async _onAsOfChange(ev) {
        this.filters.as_of = ev.target.value || this._today();
        await this.fetchData();
    }

    async _onCompanyChange(ev) {
        this.filters.company_id = ev.target.value;
        this.filters.lab_id = "ALL";
        await this.fetchData();
    }

    async _onLabChange(ev) {
        this.filters.lab_id = ev.target.value;
        await this.fetchData();
    }

    async _onDisciplineChange(ev) {
        this.filters.discipline_id = ev.target.value;
        await this.fetchData();
    }

    _onSearchInput(ev) {
        clearTimeout(this._searchTimer);
        this._searchTimer = setTimeout(async () => {
            this.filters.search = ev.target.value.trim();
            await this.fetchData();
        }, 450);
    }

    async _open(kind, extra = {}) {
        try {
            const res = await jsonrpc("/labcc/domain", {
                ...this._rpcPayload(),
                kind,
                extra,
            });
            if (res.error) return;
            this.action.doAction({
                type: "ir.actions.act_window",
                name: res.name,
                res_model: "lerm.srf.sample",
                views: [[false, "list"], [false, "form"]],
                domain: res.domain,
                context: res.context || {},
            });
        } catch (error) {
            console.error("Failed to open drill-down:", error);
        }
    }

    async _openSample(sampleId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Sample",
            res_model: "lerm.srf.sample",
            res_id: sampleId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    flagOf(item) {
        return this.FLAG_CONFIG[item.flag] || this.FLAG_CONFIG.due_today;
    }

    _stageColor(key) {
        const map = {
            allotted: "#2563eb",
            testing: "#0ea5e9",
            verification: "#f59e0b",
            approval: "#7c3aed",
        };
        return map[key] || "#6b7280";
    }

    _agingColor(key) {
        const map = {
            "0-1": "#dc2626",
            "2-3": "#ea580c",
            "4-7": "#d97706",
            "8+": "#16a34a",
        };
        return map[key] || "#2563eb";
    }

    _roleIconClass() {
        return this.state.role === "hod" ? "fa-user-tie" : "fa-building";
    }

    async _refresh() {
        await this.fetchData();
    }
}

ControlCenter.template = "lab_control_center.ControlCenter";
actionRegistry.add("lab_control_center", ControlCenter);
