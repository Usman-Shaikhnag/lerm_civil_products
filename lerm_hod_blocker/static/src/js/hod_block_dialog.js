/** @odoo-module */

import { useState } from "@odoo/owl";
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class HodBlockDialog extends Component {
    static template = "lerm_hod_blocker.HodBlockDialog";
    static components = { Dialog };
    static props = {
        close: Function,
        title: { type: String, optional: true },
        status: Object,
    };

    setup() {
        this.allotting = false;
        this.status = useState(this.props.status);
    }

    async allotSample(sampleId) {
        if (this.allotting) {
            return;
        }
        this.allotting = true;
        try {
            const action = await this.env.services.orm.call(
                "lerm.hod.block",
                "get_sample_allotment_action",
                [[sampleId]]
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
            this.allotting = false;
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
        } catch (e) {
            // Ignore transient errors; the periodic check will catch up.
        }
    }
}
