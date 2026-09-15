/** @odoo-module */

import { useState } from "@odoo/owl";
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

const SRF_PALETTE = [
    "#e3f2fd",
    "#fce4ec",
    "#e8f5e9",
    "#fff3e0",
    "#f3e5f5",
    "#e0f7fa",
    "#fffde7",
    "#efebe9",
    "#f1f8e9",
    "#ede7f6",
];

export class HodBlockDialog extends Component {
    static template = "lerm_hod_blocker.HodBlockDialog";
    static components = { Dialog };
    static props = {
        close: Function,
        title: { type: String, optional: true },
        status: Object,
    };

    setup() {
        this.allotting = useState({ value: false });
        this.selected = useState({});
        this.status = useState(this.props.status);
    }

    get selectedIds() {
        return Object.keys(this.selected)
            .filter((id) => this.selected[id])
            .map(Number);
    }

    get selectedCount() {
        return this.selectedIds.length;
    }

    get allSelected() {
        const samples = this.status.samples || [];
        return samples.length > 0 && samples.every((s) => this.selected[s.id]);
    }

    get srfColorMap() {
        const map = {};
        let index = 0;
        for (const sample of this.status.samples || []) {
            const srf = sample.srf || "";
            if (srf && !(srf in map)) {
                map[srf] = SRF_PALETTE[index % SRF_PALETTE.length];
                index += 1;
            }
        }
        return map;
    }

    srfColor(srf) {
        return this.srfColorMap[srf] || "transparent";
    }

    isSelected(sampleId) {
        return Boolean(this.selected[sampleId]);
    }

    toggleSelect(sampleId) {
        this.selected[sampleId] = !this.selected[sampleId];
    }

    toggleSelectAll() {
        const selectAll = !this.allSelected;
        for (const sample of this.status.samples || []) {
            this.selected[sample.id] = selectAll;
        }
    }

    async allotSample(sampleId) {
        await this._openAllotmentWizard([sampleId]);
    }

    async allotSelected() {
        const ids = this.selectedIds;
        if (!ids.length) {
            return;
        }
        await this._openAllotmentWizard(ids);
    }

    async _openAllotmentWizard(sampleIds) {
        if (this.allotting.value) {
            return;
        }
        this.allotting.value = true;
        try {
            const action = await this.env.services.orm.call(
                "lerm.hod.block",
                "get_sample_allotment_action",
                [sampleIds]
            );
            // `doAction` resolves when the wizard opens; the onClose callback
            // runs when it is dismissed, which is when we re-evaluate the block.
            await this.env.services.action.doAction(action, {
                onClose: () => this._refreshAfterAllotment(),
            });
            await this._refreshAfterAllotment();
        } catch (e) {
            // Keep the dialog open on errors so the HOD can retry.
        } finally {
            this.allotting.value = false;
        }
    }

    async _refreshAfterAllotment() {
        try {
            const status = await this.env.services.orm.call(
                "lerm.hod.block",
                "check_hod_block",
                []
            );
            if (status.pending_count === 0) {
                this.props.close();
                return;
            }
            // Refresh the pending list / dismissibility after each allotment.
            this.status.blocked = status.blocked;
            this.status.pending_count = status.pending_count;
            this.status.samples = status.samples;
            // Drop selections for samples that are no longer pending.
            const pendingIds = new Set((status.samples || []).map((s) => s.id));
            for (const id of Object.keys(this.selected)) {
                if (!pendingIds.has(Number(id))) {
                    delete this.selected[id];
                }
            }
        } catch (e) {
            // Ignore transient errors; the periodic check will catch up.
        }
    }
}
