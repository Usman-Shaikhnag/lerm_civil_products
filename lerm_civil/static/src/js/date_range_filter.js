/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { useState } from "@odoo/owl";
import { Domain } from "@web/core/domain";

/**
 * DateRangeFilter — inline OWL widget for the Sample list view (lerm.srf.sample).
 *
 * Features:
 *  • Direct date inputs (From / To) for Created Date and Received Date
 *  • Quick preset buttons: Today, This Week, This Month
 *  • Auto-applies via searchModel.createNewFilters() & deactivateGroup()
 *  • Clean badge indicator and one-click clear
 */

// ── Date Helpers ─────────────────────────────────────────────────────
function fmt(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
}

function startOfWeek(d) {
    const dt = new Date(d);
    const day = dt.getDay(); // 0=Sun, 1=Mon...
    const diff = (day === 0 ? -6 : 1) - day;
    dt.setDate(dt.getDate() + diff);
    return dt;
}

function endOfWeek(d) {
    const dt = startOfWeek(d);
    dt.setDate(dt.getDate() + 6);
    return dt;
}

function startOfMonth(d) {
    return new Date(d.getFullYear(), d.getMonth(), 1);
}

function endOfMonth(d) {
    return new Date(d.getFullYear(), d.getMonth() + 1, 0);
}

function presetDates(preset) {
    const today = new Date();
    switch (preset) {
        case "today":
            return [fmt(today), fmt(today)];
        case "week":
            return [fmt(startOfWeek(today)), fmt(endOfWeek(today))];
        case "month":
            return [fmt(startOfMonth(today)), fmt(endOfMonth(today))];
        default:
            return ["", ""];
    }
}

// =====================================================================
//  Patch ListController
// =====================================================================
patch(ListController.prototype, {
    setup() {
        super.setup(...arguments);

        this.dateFilter = useState({
            createFrom: "",
            createTo: "",
            createPreset: "", // "today" | "week" | "month" | ""
            receivedFrom: "",
            receivedTo: "",
            receivedPreset: "",
            expanded: false,
        });

        // Store active group IDs injected into searchModel
        this._customFilterGroupIds = [];
    },

    get isTargetModel() {
        return (this.props.resModel || this.model?.root?.resModel) === "lerm.srf.sample";
    },

    get hasActiveFilter() {
        return Boolean(
            this.dateFilter.createFrom ||
            this.dateFilter.createTo ||
            this.dateFilter.receivedFrom ||
            this.dateFilter.receivedTo
        );
    },

    _buildFacetLabel() {
        const parts = [];
        const { createFrom, createTo, createPreset, receivedFrom, receivedTo, receivedPreset } = this.dateFilter;

        if (createPreset) {
            const labels = { today: "Created Today", week: "Created This Week", month: "Created This Month" };
            parts.push(labels[createPreset]);
        } else if (createFrom || createTo) {
            parts.push(`Created: ${createFrom || "…"} → ${createTo || "…"}`);
        }

        if (receivedPreset) {
            const labels = { today: "Received Today", week: "Received This Week", month: "Received This Month" };
            parts.push(labels[receivedPreset]);
        } else if (receivedFrom || receivedTo) {
            parts.push(`Received: ${receivedFrom || "…"} → ${receivedTo || "…"}`);
        }

        return parts.join(" | ") || "Date Filter";
    },

    // ── UI Handlers ──────────────────────────────────────────────────
    onToggleDateFilter() {
        this.dateFilter.expanded = !this.dateFilter.expanded;
    },

    onCreatePreset(preset) {
        const [from, to] = presetDates(preset);
        this.dateFilter.createFrom = from;
        this.dateFilter.createTo = to;
        this.dateFilter.createPreset = preset;
        this._applyDateFilters();
    },

    onReceivedPreset(preset) {
        const [from, to] = presetDates(preset);
        this.dateFilter.receivedFrom = from;
        this.dateFilter.receivedTo = to;
        this.dateFilter.receivedPreset = preset;
        this._applyDateFilters();
    },

    onCreateFromChange(ev) {
        this.dateFilter.createFrom = ev.target.value;
        this.dateFilter.createPreset = "";
        this._applyDateFilters();
    },

    onCreateToChange(ev) {
        this.dateFilter.createTo = ev.target.value;
        this.dateFilter.createPreset = "";
        this._applyDateFilters();
    },

    onReceivedFromChange(ev) {
        this.dateFilter.receivedFrom = ev.target.value;
        this.dateFilter.receivedPreset = "";
        this._applyDateFilters();
    },

    onReceivedToChange(ev) {
        this.dateFilter.receivedTo = ev.target.value;
        this.dateFilter.receivedPreset = "";
        this._applyDateFilters();
    },

    onClearDateFilters() {
        Object.assign(this.dateFilter, {
            createFrom: "",
            createTo: "",
            createPreset: "",
            receivedFrom: "",
            receivedTo: "",
            receivedPreset: "",
        });
        this._applyDateFilters();
    },

    // ── Apply Domain via SearchModel ─────────────────────────────────
    _applyDateFilters() {
        const sm = this.env.searchModel;
        if (!sm) {
            return;
        }

        // Suspend notifications during cleanup and addition
        sm.blockNotification = true;

        // 1. Remove previous injected filters
        if (this._customFilterGroupIds && this._customFilterGroupIds.length) {
            for (const gid of this._customFilterGroupIds) {
                try {
                    sm.deactivateGroup(gid);
                } catch (_e) {
                    // Group might already have been dismissed
                }
            }
            this._customFilterGroupIds = [];
        }

        // 2. Prepare filter objects
        const prefilters = [];

        // Created Date (Datetime field)
        const createDomain = [];
        if (this.dateFilter.createFrom) {
            createDomain.push(["create_date", ">=", this.dateFilter.createFrom + " 00:00:00"]);
        }
        if (this.dateFilter.createTo) {
            createDomain.push(["create_date", "<=", this.dateFilter.createTo + " 23:59:59"]);
        }
        if (createDomain.length) {
            let label = "";
            if (this.dateFilter.createPreset) {
                const map = { today: "Created Today", week: "Created This Week", month: "Created This Month" };
                label = map[this.dateFilter.createPreset] || "Created Date";
            } else {
                label = `Created: ${this.dateFilter.createFrom || "…"} → ${this.dateFilter.createTo || "…"}`;
            }
            prefilters.push({
                description: label,
                domain: new Domain(createDomain).toString(),
                type: "filter",
            });
        }

        // Received Date (Date field)
        const receivedDomain = [];
        if (this.dateFilter.receivedFrom) {
            receivedDomain.push(["sample_received_date", ">=", this.dateFilter.receivedFrom]);
        }
        if (this.dateFilter.receivedTo) {
            receivedDomain.push(["sample_received_date", "<=", this.dateFilter.receivedTo]);
        }
        if (receivedDomain.length) {
            let label = "";
            if (this.dateFilter.receivedPreset) {
                const map = { today: "Received Today", week: "Received This Week", month: "Received This Month" };
                label = map[this.dateFilter.receivedPreset] || "Received Date";
            } else {
                label = `Received: ${this.dateFilter.receivedFrom || "…"} → ${this.dateFilter.receivedTo || "…"}`;
            }
            prefilters.push({
                description: label,
                domain: new Domain(receivedDomain).toString(),
                type: "filter",
            });
        }

        // 3. Inject new filters
        if (prefilters.length) {
            for (const pf of prefilters) {
                sm.createNewFilters([pf]);
                if (pf.groupId) {
                    this._customFilterGroupIds.push(pf.groupId);
                }
            }
        }

        // Unblock and notify view once
        sm.blockNotification = false;
        sm._notify();
    },
});
