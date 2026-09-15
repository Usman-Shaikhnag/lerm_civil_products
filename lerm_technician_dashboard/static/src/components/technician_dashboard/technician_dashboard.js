/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";

const actionRegistry = registry.category("actions");

export class TechnicianDashboard extends Component {
    static template = "lerm_technician_dashboard.TechnicianDashboard";

    stateColor = {
        "5-alloted": "#3b82f6",
        "4-rejected": "#ef4444",
        "1-draft": "#6366f1",
        "2-confirm": "#d97706",
        "3-approved": "#22c55e",
        "5-cancelled": "#9ca3af",
    };

    stateIcon = {
        "5-alloted": "fa-play-circle",
        "4-rejected": "fa-undo",
        "1-draft": "fa-calculator",
        "2-confirm": "fa-hourglass-half",
        "3-approved": "fa-check-circle",
        "5-cancelled": "fa-times-circle",
    };

    kpiDefs = [
        { key: "overdue", label: "Overdue", color: "#ef4444" },
        { key: "due_today", label: "Due Today", color: "#f59e0b" },
        { key: "in_progress", label: "In Progress", color: "#3b82f6" },
        { key: "completed", label: "Completed", color: "#22c55e" },
    ];

    matchTab(row, key) {
        switch (key) {
            case "all":
                return true;
            case "todo":
                return (
                    row.state === "5-alloted" ||
                    row.state === "4-rejected" ||
                    (row.state === "1-draft" && !row.test_started)
                );
            case "in_progress":
                return row.state === "1-draft" && row.test_started;
            case "waiting":
                return row.state === "2-confirm";
            case "completed":
                return row.state === "3-approved";
            default:
                return true;
        }
    }

    setup() {
        this.dash = useState({
            loading: true,
            error: false,
            data: null,
            workTab: "needs_action",
            sampleTab: "all",
            search: "",
            dueFilter: "all",
            typeFilter: "all",
        });
        this.action = useService("action");
        onWillStart(async () => {
            await this.load();
        });
    }

    async load() {
        this.dash.loading = true;
        this.dash.error = false;
        try {
            const data = await jsonrpc("/technician_dashboard/data", {});
            if (data && data.error) {
                throw new Error(data.error);
            }
            this.dash.data = data;
        } catch (err) {
            this.dash.error = err.message || "Failed to load dashboard data.";
        } finally {
            this.dash.loading = false;
        }
    }

    // -------------------------------------------------------------------------
    // header helpers
    // -------------------------------------------------------------------------

    get greeting() {
        const h = new Date().getHours();
        let word = "Hello";
        if (h >= 5 && h < 12) {
            word = "Good morning";
        } else if (h >= 12 && h < 17) {
            word = "Good afternoon";
        } else {
            word = "Good evening";
        }
        const name = this.dash.data ? this.dash.data.user.name || "" : "";
        return `${word}, ${name}`;
    }

    get todayLabel() {
        return new Date().toLocaleDateString(undefined, {
            weekday: "long",
            day: "numeric",
            month: "long",
        });
    }

    get initials() {
        const name = this.dash.data ? this.dash.data.user.name || "?" : "?";
        const parts = name.trim().split(/\s+/);
        return ((parts[0] || "")[0] || "") + ((parts[1] || "")[0] || "");
    }

    // -------------------------------------------------------------------------
    // generic helpers
    // -------------------------------------------------------------------------

    colorFor(state) {
        return this.stateColor[state] || "#6c757d";
    }

    iconFor(state) {
        return this.stateIcon[state] || "fa-question-circle";
    }

    actionLabel(row) {
        if (!row) {
            return "";
        }
        if (row.state === "1-draft") {
            return row.test_started ? "Continue" : "Start Testing";
        }
        if (row.state === "5-alloted" || row.state === "4-rejected") {
            return "Start Testing";
        }
        return "View";
    }

    dueClass(bucket) {
        return {
            overdue: "tdash-pill tdash-pill-red",
            due_today: "tdash-pill tdash-pill-orange",
            due_tomorrow: "tdash-pill tdash-pill-amber",
            later: "tdash-pill tdash-pill-grey",
        }[bucket] || "tdash-pill tdash-pill-grey";
    }

    stateChipStyle(state) {
        const c = this.colorFor(state);
        return `background:${c}1a;color:${c};border:1px solid ${c}40;`;
    }

    // -------------------------------------------------------------------------
    // drill-down actions
    // -------------------------------------------------------------------------

    async openList(mode, extra = {}) {
        const res = await jsonrpc("/technician_dashboard/list_domain", { mode, ...extra });
        return this.action.doAction({
            type: "ir.actions.act_window",
            name: res.name,
            res_model: res.res_model,
            domain: res.domain,
            views: res.views,
            context: res.context,
        });
    }

    async openWork(row) {
        if (!row) {
            return;
        }
        if (row.eln_id) {
            return this.action.doAction({
                type: "ir.actions.act_window",
                res_model: "lerm.eln",
                res_id: row.eln_id,
                views: [[false, "form"]],
                target: "current",
            });
        }
        return this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "lerm.srf.sample",
            res_id: row.id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openMatrix(rowKey, colKey) {
        return this.openList("stage_horizon", { stage: rowKey, horizon: colKey });
    }

    onKpiClick(key) {
        return this.openList(key);
    }

    // -------------------------------------------------------------------------
    // my samples filtering
    // -------------------------------------------------------------------------

    get kpiCards() {
        const kpi = this.dash.data ? this.dash.data.kpi : {};
        return this.kpiDefs.map((def) => ({
            key: def.key,
            label: def.label,
            count: kpi[def.key] || 0,
            color: def.color,
        }));
    }

    get dayBuckets() {
        const d = this.dash.data ? this.dash.data.day : {};
        return [
            { key: "overdue", label: "Overdue", icon: "fa-circle", color: "#ef4444", count: d.overdue || 0 },
            { key: "due_today", label: "Due Today", icon: "fa-circle", color: "#f59e0b", count: d.due_today || 0 },
            { key: "due_tomorrow", label: "Due Tomorrow", icon: "fa-circle", color: "#eab308", count: d.due_tomorrow || 0 },
        ];
    }

    get progressStyle() {
        const pct = this.dash.data ? this.dash.data.day.progress_pct || 0 : 0;
        return `background: conic-gradient(#22c55e ${pct * 3.6}deg, #e5e7eb 0deg);`;
    }

    get progressPct() {
        return this.dash.data ? this.dash.data.day.progress_pct || 0 : 0;
    }

    get doneCount() {
        return this.dash.data ? this.dash.data.day.done || 0 : 0;
    }

    get remainingCount() {
        return this.dash.data ? this.dash.data.day.remaining || 0 : 0;
    }

    get ringTotal() {
        return this.dash.data ? this.dash.data.day.ring_total || 0 : 0;
    }

    get nextAction() {
        return this.dash.data ? this.dash.data.next_action : false;
    }

    get needsAction() {
        return this.dash.data ? this.dash.data.needs_action : [];
    }

    get waitingRows() {
        return this.dash.data ? this.dash.data.waiting : [];
    }

    // ---- workload matrix ----
    get matrixColumns() {
        return this.dash.data && this.dash.data.matrix
            ? this.dash.data.matrix.columns
            : [];
    }

    get matrixActiveRows() {
        return this.dash.data && this.dash.data.matrix
            ? this.dash.data.matrix.rows
            : [];
    }

    get matrixCompleted() {
        return this.dash.data && this.dash.data.matrix
            ? this.dash.data.matrix.completed
            : { counts: {} };
    }

    matrixVal(row, colKey) {
        return (row.counts || {})[colKey] || 0;
    }

    matrixColor(rowKey) {
        return {
            allotted: "#3b82f6",
            testing: "#6366f1",
            verification: "#d97706",
            approval: "#dc2626",
            approved: "#22c55e",
        }[rowKey] || "#6b7280";
    }

    get sampleTypeOptions() {
        return this.dash.data ? this.dash.data.samples.types : [];
    }

    get sampleTabs() {
        const c = this.dash.data ? this.dash.data.samples.counts : {};
        return [
            { key: "all", label: "All", count: c.all || 0 },
            { key: "todo", label: "To Do", count: c.todo || 0 },
            { key: "in_progress", label: "In Progress", count: c.in_progress || 0 },
            { key: "waiting", label: "Waiting", count: c.waiting || 0 },
            { key: "completed", label: "Completed", count: c.completed || 0 },
        ];
    }

    get filteredSamples() {
        if (!this.dash.data) {
            return [];
        }
        const rows = this.dash.data.samples.rows || [];
        const q = (this.dash.search || "").trim().toLowerCase();

        return rows.filter((row) => {
            if (!this.matchTab(row, this.dash.sampleTab)) {
                return false;
            }
            if (this.dash.dueFilter !== "all" && row.due_bucket !== this.dash.dueFilter) {
                return false;
            }
            if (this.dash.typeFilter !== "all" && row.test_type !== this.dash.typeFilter) {
                return false;
            }
            if (q) {
                const hay = [row.ref, row.sample_no, row.ulr_no, row.customer, row.material,
                             row.test_type, row.discipline].join(" ").toLowerCase();
                if (!hay.includes(q)) {
                    return false;
                }
            }
            return true;
        });
    }

    setTab(tab) {
        this.dash.sampleTab = tab;
    }

    get workTabs() {
        const c = this.dash.data ? this.dash.data.samples.counts : {};
        const needs = (c.todo || 0) + (c.in_progress || 0);
        return [
            { key: "needs_action", label: "Needs My Action", count: needs },
            { key: "waiting", label: "Waiting on Others", count: c.waiting || 0 },
            { key: "samples", label: "My Samples", count: c.all || 0 },
        ];
    }

    get viewAllMode() {
        return {
            needs_action: "needs_action",
            waiting: "waiting",
            samples: "all",
        }[this.dash.workTab] || "all";
    }

    setWorkTab(tab) {
        this.dash.workTab = tab;
    }
}

actionRegistry.add("technician_dashboard", TechnicianDashboard);
