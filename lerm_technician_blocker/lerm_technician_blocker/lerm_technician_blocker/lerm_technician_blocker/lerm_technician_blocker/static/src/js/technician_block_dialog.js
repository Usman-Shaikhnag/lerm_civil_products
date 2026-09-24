/** @odoo-module */

import { useState } from "@odoo/owl";
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class TechnicianBlockDialog extends Component {
    static template = "lerm_technician_blocker.TechnicianBlockDialog";
    static components = { Dialog };
    static props = {
        close: Function,
        title: { type: String, optional: true },
        variant: String, // 'new_work' | 'due' | 'overdue'
        status: Object,
        rows: Array,
        digestIds: { type: Array, optional: true },
    };

    setup() {
        this.opening = false;
        this.rows = useState(this.props.rows);
    }

    get isBlocking() {
        return this.props.variant === "overdue";
    }

    _markSeen() {
        const digestIds = this.props.digestIds || [];
        if (digestIds.length) {
            this.env.services.orm.call(
                "lerm.technician.blocker",
                "mark_seen",
                [digestIds]
            ).catch(() => {});
        }
    }

    async openSample(sampleId) {
        if (this.opening) {
            return;
        }
        this.opening = true;
        try {
            this._markSeen();
            this.props.close();
            const action = await this.env.services.orm.call(
                "lerm.technician.blocker",
                "get_sample_action",
                [sampleId]
            );
            if (action) {
                await this.env.services.action.doAction(action);
            }
        } catch (e) {
            this.opening = false;
        }
    }

    close() {
        this._markSeen();
        this.props.close();
    }
}
