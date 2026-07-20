/** @odoo-module **/

import { Component, onWillStart, onMounted, onPatched, useState, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { Layout } from "@web/search/layout";
import { useService } from "@web/core/utils/hooks";
import { browser } from "@web/core/browser/browser";

import { FilterToolbar } from "../components/FilterToolbar/filter_toolbar";
import { SummaryCards } from "../components/SummaryCards/summary_cards";
import { LedgerTable } from "../components/LedgerTable/ledger_table";
import { GroupHeader } from "../components/GroupHeader/group_header";
import { ColumnChooser } from "../components/ColumnChooser/column_chooser";
import { ExportDialog } from "../components/ExportDialog/export_dialog";
import { EmptyState } from "../components/EmptyState/empty_state";
import { MobileFilters } from "../components/MobileFilters/mobile_filters";

const DEFAULT_FILTERS = {
    account_id: null,
    date_filter: "this_month",
    date_from: null,
    date_to: null,
    journal_ids: [],
    partner_id: null,
    analytic_account_id: null,
    target_move: "all",
    currency_id: null,
    search_term: "",
    group_by: "none",
    show_initial_balance: true,
    sort_by: "date",
    sort_order: "asc",
    offset: 0,
    limit: 50,
};

const ALL_COLUMNS = [
    { id: "date", label: "Date", visible: true, sortable: true, width: 110 },
    { id: "journal", label: "Journal", visible: true, sortable: true, width: 80 },
    { id: "move", label: "Move", visible: true, sortable: true, width: 120 },
    { id: "partner", label: "Partner", visible: true, sortable: true, width: 150 },
    { id: "label", label: "Label", visible: true, sortable: true, width: 200 },
    { id: "ref", label: "Reference", visible: true, sortable: true, width: 120 },
    { id: "debit", label: "Debit", visible: true, sortable: true, width: 110, align: "right" },
    { id: "credit", label: "Credit", visible: true, sortable: true, width: 110, align: "right" },
    { id: "balance", label: "Balance", visible: true, sortable: true, width: 120, align: "right" },
    { id: "analytic", label: "Analytic", visible: true, sortable: false, width: 130 },
    { id: "taxes", label: "Taxes", visible: false, sortable: false, width: 100 },
    { id: "user", label: "User", visible: false, sortable: false, width: 120 },
    { id: "state", label: "Status", visible: true, sortable: true, width: 80 },
];

class GLReport extends Component {
    static template = "gl_report.GLReport";
    static components = {
        Layout,
        FilterToolbar,
        SummaryCards,
        LedgerTable,
        GroupHeader,
        ColumnChooser,
        ExportDialog,
        EmptyState,
        MobileFilters,
    };

    setup() {
        this.glData = useService("gl_report.data");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            filters: { ...DEFAULT_FILTERS },
            loading: false,
            exporting: false,
            data: null,
            error: null,
            columns: this._loadColumnState(),
            expandedRows: {},
            columnChooserOpen: false,
            exportDialogOpen: false,
            mobileFiltersOpen: false,
            activePreset: null,
            presets: [],
            totalRecords: 0,
            currentPage: 1,
        });

        this._restoreLastFilters();

        onWillStart(async () => {
            await this._loadPresets();
        });

        onMounted(() => {
            if (this.state.filters.account_id) {
                this._loadData();
            }
        });
    }

    async _loadData() {
        if (!this.state.filters.account_id) return;
        this.state.loading = true;
        this.state.error = null;
        try {
            const params = { ...this.state.filters };
            const result = await this.glData.getData(params);
            this.state.data = result;
            this.state.totalRecords = result.total_records || 0;
            this._saveLastFilters();
        } catch (err) {
            this.state.error = err.message || err;
            this.notification.add(this.state.error, { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    applyFilters(filters) {
        Object.assign(this.state.filters, filters, { offset: 0 });
        this.state.currentPage = 1;
        this._loadData();
    }

    resetFilters() {
        Object.assign(this.state.filters, DEFAULT_FILTERS);
        this.state.data = null;
        this.state.totalRecords = 0;
        this.state.currentPage = 1;
        browser.localStorage.removeItem("gl_report_last_filters");
    }

    onPageChange(page) {
        const offset = (page - 1) * this.state.filters.limit;
        this.state.filters.offset = offset;
        this.state.currentPage = page;
        this._loadData();
    }

    onPageSizeChange(size) {
        this.state.filters.limit = size;
        this.state.filters.offset = 0;
        this.state.currentPage = 1;
        this._loadData();
    }

    onSort(field) {
        const { sort_by, sort_order } = this.state.filters;
        if (sort_by === field) {
            this.state.filters.sort_order = sort_order === "asc" ? "desc" : "asc";
        } else {
            this.state.filters.sort_by = field;
            this.state.filters.sort_order = "asc";
        }
        this.state.filters.offset = 0;
        this.state.currentPage = 1;
        this._loadData();
    }

    onGroupByChange(groupBy) {
        this.state.filters.group_by = groupBy;
        this.state.filters.offset = 0;
        this.state.currentPage = 1;
        this._loadData();
    }

    onSearch(term) {
        this.state.filters.search_term = term;
        this.state.filters.offset = 0;
        this.state.currentPage = 1;
        this._loadData();
    }

    toggleRowExpand(lineId) {
        if (this.state.expandedRows[lineId]) {
            const newExpanded = { ...this.state.expandedRows };
            delete newExpanded[lineId];
            this.state.expandedRows = newExpanded;
        } else {
            this.state.expandedRows = { ...this.state.expandedRows, [lineId]: true };
        }
    }

    toggleColumnChooser() {
        this.state.columnChooserOpen = !this.state.columnChooserOpen;
    }

    toggleExportDialog() {
        this.state.exportDialogOpen = !this.state.exportDialogOpen;
    }

    toggleMobileFilters() {
        this.state.mobileFiltersOpen = !this.state.mobileFiltersOpen;
    }

    onColumnToggle(colId) {
        this.state.columns = this.state.columns.map(col =>
            col.id === colId ? { ...col, visible: !col.visible } : col
        );
        this._saveColumnState();
    }

    onColumnResize(colId, newWidth) {
        this.state.columns = this.state.columns.map(col =>
            col.id === colId ? { ...col, width: Math.max(60, newWidth) } : col
        );
    }

    async savePreset(name) {
        try {
            await this.glData.savePreset(name, JSON.stringify(this.state.filters));
            this.notification.add(`Preset "${name}" saved`, { type: "success" });
            await this._loadPresets();
        } catch (err) {
            this.notification.add("Failed to save preset", { type: "danger" });
        }
    }

    async loadPreset(preset) {
        try {
            const params = JSON.parse(preset.params);
            Object.assign(this.state.filters, params);
            this.state.activePreset = preset;
            this.state.currentPage = 1;
            await this._loadData();
        } catch (err) {
            this.notification.add("Failed to load preset", { type: "danger" });
        }
    }

    async deletePreset(presetId) {
        try {
            await this.glData.deletePreset(presetId);
            this.state.presets = this.state.presets.filter(p => p.id !== presetId);
            this.notification.add("Preset deleted", { type: "info" });
        } catch (err) {
            this.notification.add("Failed to delete preset", { type: "danger" });
        }
    }

    async exportReport(format) {
        this.state.exporting = true;
        try {
            const result = await this.glData.exportData(this.state.filters, format);
            if (result.url) {
                window.open(result.url, "_blank");
            }
            this.notification.add("Export started", { type: "success" });
        } catch (err) {
            this.notification.add("Export failed", { type: "danger" });
        } finally {
            this.state.exporting = false;
            this.state.exportDialogOpen = false;
        }
    }

    openJournalEntry(moveId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "account.move",
            res_id: moveId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openPartner(partnerId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "res.partner",
            res_id: partnerId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    get activeFilters() {
        const chips = [];
        const f = this.state.filters;
        if (f.account_id) chips.push({ id: "account", label: `Account: ${f.account_id_display || f.account_id}`, onRemove: () => { f.account_id = null; this._loadData(); } });
        if (f.date_from || f.date_to) chips.push({ id: "date", label: `Period: ${f.date_from || "..."} - ${f.date_to || "..."}`, onRemove: () => { f.date_from = null; f.date_to = null; this._loadData(); } });
        if (f.journal_ids?.length) chips.push({ id: "journal", label: `${f.journal_ids.length} Journal(s)`, onRemove: () => { f.journal_ids = []; this._loadData(); } });
        if (f.partner_id) chips.push({ id: "partner", label: `Partner: ${f.partner_id_display || f.partner_id}`, onRemove: () => { f.partner_id = null; this._loadData(); } });
        if (f.analytic_account_id) chips.push({ id: "analytic", label: `Analytic: ${f.analytic_account_id_display || f.analytic_account_id}`, onRemove: () => { f.analytic_account_id = null; this._loadData(); } });
        if (f.search_term) chips.push({ id: "search", label: `Search: "${f.search_term}"`, onRemove: () => { f.search_term = ""; this._loadData(); } });
        return chips;
    }

    async _loadPresets() {
        try {
            const result = await this.glData.getPresets();
            this.state.presets = result.presets || [];
        } catch (err) {
            // silent
        }
    }

    _saveLastFilters() {
        try {
            const toSave = { ...this.state.filters };
            browser.localStorage.setItem("gl_report_last_filters", JSON.stringify(toSave));
        } catch (err) {
            // silent
        }
    }

    _restoreLastFilters() {
        try {
            const saved = browser.localStorage.getItem("gl_report_last_filters");
            if (saved) {
                const parsed = JSON.parse(saved);
                Object.assign(this.state.filters, parsed);
            }
        } catch (err) {
            // silent
        }
    }

    _saveColumnState() {
        try {
            browser.localStorage.setItem("gl_report_columns", JSON.stringify(this.state.columns));
        } catch (err) {
            // silent
        }
    }

    _loadColumnState() {
        try {
            const saved = browser.localStorage.getItem("gl_report_columns");
            if (saved) {
                const parsed = JSON.parse(saved);
                if (parsed.length === ALL_COLUMNS.length) return parsed;
            }
        } catch (err) {
            // silent
        }
        return ALL_COLUMNS.map(c => ({ ...c }));
    }

    get visibleColumns() {
        return this.state.columns.filter(c => c.visible);
    }

    get totalPages() {
        return Math.ceil(this.state.totalRecords / this.state.filters.limit) || 1;
    }

    get companyName() {
        return this.env.services.company?.name || "";
    }

    get currentUser() {
        return this.env.services.user?.name || "";
    }

    get generatedAt() {
        return new Date().toLocaleString();
    }

    get companyCurrency() {
        return this.env.services.company?.currency_id || "";
    }
}

registry.category("actions").add("account_gl_report.open", GLReport);
