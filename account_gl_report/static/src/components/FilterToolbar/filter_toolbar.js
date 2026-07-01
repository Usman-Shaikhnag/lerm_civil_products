/** @odoo-module **/
import { Component, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class FilterToolbar extends Component {
    static template = "gl_report.FilterToolbar";

    setup() {
        this.glData = useService("gl_report.data");
        this.state = useState({
            accountSearchTerm: "",
            accountResults: [],
            accountOpen: false,
            journalOptions: [],
            journalsOpen: false,
            datePickerOpen: false,
            presetMenuOpen: false,
            savePresetName: "",
        });
        this.accountSelectRef = useRef("accountSelect");
        this.searchRef = useRef("globalSearch");
        this.searchTimeout = null;
    }

    async onAccountSearch(term) {
        this.state.accountSearchTerm = term;
        this.state.accountOpen = true;
        try {
            const results = await this.glData.searchAccounts(term);
            this.state.accountResults = results;
        } catch (e) {
            this.state.accountResults = [];
        }
    }

    selectAccount(account) {
        this.props.filters.account_id = account.id;
        this.props.filters.account_id_display = account.display_name;
        this.state.accountOpen = false;
        this.state.accountSearchTerm = account.display_name;
    }

    clearAccount() {
        this.props.filters.account_id = null;
        this.props.filters.account_id_display = "";
        this.state.accountSearchTerm = "";
    }

    async openJournals() {
        this.state.journalsOpen = true;
        if (!this.state.journalOptions.length) {
            try {
                this.state.journalOptions = await this.glData.getJournals();
            } catch (e) {
                this.state.journalOptions = [];
            }
        }
    }

    toggleJournal(journalId) {
        const ids = this.props.filters.journal_ids || [];
        const idx = ids.indexOf(journalId);
        if (idx >= 0) {
            ids.splice(idx, 1);
        } else {
            ids.push(journalId);
        }
        this.props.filters.journal_ids = [...ids];
    }

    setDateRange(filter) {
        this.props.filters.date_filter = filter;
        this.state.datePickerOpen = false;
    }

    setCustomDate(from, to) {
        this.props.filters.date_from = from;
        this.props.filters.date_to = to;
        this.props.filters.date_filter = "custom";
        this.state.datePickerOpen = false;
    }

    onGlobalSearch(ev) {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.props.onSearch(ev.target.value);
        }, 300);
    }

    onGroupByChange(ev) {
        this.props.onGroupBy(ev.target.value);
    }

    apply() {
        this.props.onApply({ ...this.props.filters });
    }

    reset() {
        this.props.onReset();
    }

    savePreset() {
        if (this.state.savePresetName.trim()) {
            this.props.onSavePreset(this.state.savePresetName.trim());
            this.state.savePresetName = "";
            this.state.presetMenuOpen = false;
        }
    }

    get dateFilterLabel() {
        const labels = {
            today: "Today", yesterday: "Yesterday",
            this_week: "This Week", last_week: "Last Week",
            this_month: "This Month", last_month: "Last Month",
            quarter: "Quarter", fiscal_year: "Fiscal Year",
            custom: "Custom Range",
        };
        return labels[this.props.filters.date_filter] || "Select Range";
    }

    get dateRangeDisplay() {
        const f = this.props.filters;
        if (f.date_from && f.date_to) {
            return `${f.date_from} – ${f.date_to}`;
        }
        return this.dateFilterLabel;
    }
}

FilterToolbar.props = [
    "filters", "presets", "activePreset", "activeFilters",
    "onApply", "onReset", "onSearch", "onGroupBy",
    "onSavePreset", "onLoadPreset", "onDeletePreset",
];
