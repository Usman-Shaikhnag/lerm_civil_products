/** @odoo-module */

import { onWillUnmount } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { WebClient } from "@web/webclient/webclient";
import { TechnicianBlockDialog } from "./technician_block_dialog";

const MIN_DELAY_MS = 1000;
const RETRY_MS = 60 * 1000;
const IDLE_MS = 15 * 60 * 1000;

patch(WebClient.prototype, {
    setup() {
        super.setup();
        this._technicianBlockTimer = null;
        this._technicianBlockDialogOpen = false;
        this._technicianBlockOpenIntent = false;
        this._technicianBlockStart = () => this._scheduleTechnicianBlockCheck(0);
        this.env.bus.addEventListener(
            "WEB_CLIENT_READY",
            this._technicianBlockStart,
            { once: true }
        );
        onWillUnmount(() => {
            clearTimeout(this._technicianBlockTimer);
            this.env.bus.removeEventListener(
                "WEB_CLIENT_READY",
                this._technicianBlockStart
            );
        });
    },

    _scheduleTechnicianBlockCheck(delayMs) {
        clearTimeout(this._technicianBlockTimer);
        this._technicianBlockTimer = setTimeout(
            () => this._runTechnicianBlockCheck(),
            delayMs
        );
    },

    async _runTechnicianBlockCheck() {
        if (this._technicianBlockDialogOpen) {
            return;
        }
        let status;
        try {
            status = await this.env.services.orm.call(
                "lerm.technician.blocker",
                "check",
                []
            );
        } catch (e) {
            this._scheduleTechnicianBlockCheck(RETRY_MS);
            return;
        }
        if (!status.eligible) {
            // Not a technician: never show any popup and stop polling.
            return;
        }
        if (!status.active) {
            // No feature enabled for technicians: back off until re-enabled.
            this._scheduleTechnicianBlockCheck(IDLE_MS);
            return;
        }

        // Priority: blocking Overdue > due-date digest > new-work digest.
        if (status.overdue_blocked) {
            this._showTechnicianBlockDialog({
                variant: "overdue",
                title: "Work Overdue - Action Required",
                status,
                rows: status.overdue || [],
            }, /* blocking */ true);
            return;
        }
        if (status.due_pending_count) {
            this._showTechnicianBlockDialog({
                variant: "due",
                title: "Report Due Reminder",
                status,
                rows: status.due_samples || [],
                digestIds: status.due_digest_ids || [],
            });
            return;
        }
        if (status.enabled && status.pending_count) {
            this._showTechnicianBlockDialog({
                variant: "new_work",
                title: "New Work Assigned",
                status,
                rows: status.samples || [],
                digestIds: status.digest_ids || [],
            });
            return;
        }

        const seconds = Number(status.next_check_seconds) || 3600;
        this._scheduleTechnicianBlockCheck(
            Math.max(MIN_DELAY_MS, seconds * 1000)
        );
    },

    _showTechnicianBlockDialog(props, blocking = false) {
        this._technicianBlockDialogOpen = true;
        this._technicianBlockOpenIntent = false;
        const overdueProps = blocking
            ? {
                  ...props,
                  onOverdueOpen: () => {
                      // User is opening the job to resolve it: allow a grace
                      // window; the block returns if it is still overdue.
                      this._technicianBlockOpenIntent = true;
                  },
              }
            : props;
        this.env.services.dialog.add(
            TechnicianBlockDialog,
            overdueProps,
            {
                onClose: () => {
                    this._technicianBlockDialogOpen = false;
                    if (blocking) {
                        if (this._technicianBlockOpenIntent) {
                            // They went to work on the job; re-check shortly so
                            // the block returns if the work is still overdue.
                            this._technicianBlockOpenIntent = false;
                            this._scheduleTechnicianBlockCheck(RETRY_MS);
                        } else {
                            // Dismissed without opening (X/Esc): the block is
                            // mandatory and re-opens immediately.
                            this._scheduleTechnicianBlockCheck(MIN_DELAY_MS);
                        }
                        return;
                    }
                    this._markDigestsSeen(props);
                    this._runTechnicianBlockCheck();
                },
            }
        );
    },

    _markDigestsSeen(props) {
        const digestIds = props.digestIds || [];
        if (!digestIds.length) {
            return;
        }
        this.env.services.orm.call(
            "lerm.technician.blocker",
            "mark_seen",
            [digestIds]
        ).catch(() => {});
    },
});
