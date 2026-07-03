/** @odoo-module **/
import { Component, useState } from "@odoo/owl";

export class LedgerTable extends Component {
    static template = "gl_report.LedgerTable";

    setup() {
        this.state = useState({
            resizing: null,
        });
    }

    onSortClick(colId) {
        if (this.props.columns.find(c => c.id === colId)?.sortable) {
            this.props.onSort(colId);
        }
    }

    startResize(ev, colId) {
        ev.preventDefault();
        const startX = ev.clientX;
        const col = this.props.columns.find(c => c.id === colId);
        const startWidth = col?.width || 100;

        const onMove = (moveEv) => {
            const diff = moveEv.clientX - startX;
            const newWidth = Math.max(60, startWidth + diff);
            this.props.onColumnResize(colId, newWidth);
        };

        const onUp = () => {
            document.removeEventListener("mousemove", onMove);
            document.removeEventListener("mouseup", onUp);
        };

        document.addEventListener("mousemove", onMove);
        document.addEventListener("mouseup", onUp);
    }

    formatCurrency(val) {
        if (val == null) return "0.00";
        const num = typeof val === "number" ? val : parseFloat(val);
        return num.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }

    balanceClass(val) {
        if (val > 0) return "o_gl_balance_positive";
        if (val < 0) return "o_gl_balance_negative";
        return "o_gl_balance_zero";
    }

    formatDate(d) {
        if (!d) return "";
        const dt = typeof d === "string" ? new Date(d) : d;
        return dt.toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });
    }

    getPageNumbers() {
        const total = this.props.totalPages;
        const current = this.props.currentPage;
        const pages = [];

        if (total <= 7) {
            for (let i = 1; i <= total; i++) pages.push(i);
        } else {
            pages.push(1);
            if (current > 3) pages.push("...");
            for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) {
                pages.push(i);
            }
            if (current < total - 2) pages.push("...");
            pages.push(total);
        }
        return pages;
    }

    get sortField() {
        return this.props.filters?.sort_by || "date";
    }

    get sortOrder() {
        return this.props.filters?.sort_order || "asc";
    }

    isGrouped() {
        return this.props.filters?.group_by && this.props.filters.group_by !== "none";
    }
}

LedgerTable.props = [
    "data", "columns", "allColumns", "expandedRows",
    "filters", "totalRecords", "currentPage", "totalPages",
    "onSort", "onPageChange", "onPageSizeChange",
    "onToggleRow", "onColumnResize",
    "onOpenMove", "onOpenPartner",
];
