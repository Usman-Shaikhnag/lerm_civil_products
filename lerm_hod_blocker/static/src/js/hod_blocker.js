/** @odoo-module */

import { onWillUnmount } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { WebClient } from "@web/webclient/webclient";
import { HodBlockDialog } from "./hod_block_dialog";

const HOUR_MS = 3600 * 1000;
const RETRY_MS = 60 * 1000;

patch(WebClient.prototype, {
    setup() {
        super.setup();
        this._hodBlockTimer = null;
        this._hodBlockDialogOpen = false;
        this._hodBlockStart = () => this._scheduleHodBlockCheck(0);
        // The RPC session is not ready during setup(); start the first check
        // once the web client reports it is ready.
        this.env.bus.addEventListener(
            "WEB_CLIENT_READY",
            this._hodBlockStart,
            { once: true }
        );
        onWillUnmount(() => {
            clearTimeout(this._hodBlockTimer);
            this.env.bus.removeEventListener(
                "WEB_CLIENT_READY",
                this._hodBlockStart
            );
        });
    },

    _hodBlockIntervalMs(status) {
        const hours = Number(status.interval_hours) || 2;
        return Math.max(1, hours) * HOUR_MS;
    },

    _scheduleHodBlockCheck(delayMs) {
        clearTimeout(this._hodBlockTimer);
        this._hodBlockTimer = setTimeout(() => this._runHodBlockCheck(), delayMs);
    },

    async _runHodBlockCheck() {
        if (this._hodBlockDialogOpen) {
            return;
        }
        let status;
        try {
            status = await this.env.services.orm.call(
                "lerm.hod.block",
                "check_hod_block",
                []
            );
        } catch (e) {
            this._scheduleHodBlockCheck(RETRY_MS);
            return;
        }
        if (!status.enabled) {
            this._scheduleHodBlockCheck(this._hodBlockIntervalMs(status));
            return;
        }
        if (status.pending_count > 0) {
            this._showHodBlockDialog(status);
            return;
        }
        this._scheduleHodBlockCheck(this._hodBlockIntervalMs(status));
    },

    _showHodBlockDialog(status) {
        this._hodBlockDialogOpen = true;
        const wasBlocked = status.blocked;
        this.env.services.dialog.add(
            HodBlockDialog,
            {
                title: wasBlocked
                    ? "Pending Sample Allotment Required"
                    : "New Samples Awaiting Allotment",
                status,
            },
            {
                onClose: () => {
                    this._hodBlockDialogOpen = false;
                    // A hard block must not be bypassable (X / Esc close), so
                    // re-check immediately and re-open while it persists.
                    this._scheduleHodBlockCheck(
                        wasBlocked ? 0 : this._hodBlockIntervalMs(status)
                    );
                },
            }
        );
    },
});
