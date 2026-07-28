/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { FormRenderer } from "@web/views/form/form_renderer";
import { useService } from "@web/core/utils/hooks";
import { onMounted, onPatched } from "@odoo/owl";

/**
 * Global patch: automatically makes any form with `eln_state` field
 * readonly (visually locked) when eln_state is not '1-draft'.
 * Users in the "Lerm Admin" group bypass this lock.
 */
patch(FormRenderer.prototype, {
    setup() {
        super.setup(...arguments);
        this.userService = useService("user");
        this._isAdmin = false;
        this._adminChecked = false;

        // Check admin group once on setup
        this.userService.hasGroup("lerm_civil.kes_admin_access_group").then((result) => {
            this._isAdmin = result;
            this._adminChecked = true;
            this._applyElnReadonly();
        });

        onMounted(() => this._applyElnReadonly());
        onPatched(() => this._applyElnReadonly());
    },

    _applyElnReadonly() {
        const record = this.props.record;
        if (!record || !record.data) return;
        if (!("eln_state" in record.data)) return;

        const formEl = this.__owl__.bdom?.el?.closest?.(".o_form_view")
            || document.querySelector(".o_form_view");
        if (!formEl) return;

        // Admin users can always edit
        if (this._isAdmin) {
            formEl.classList.remove("eln-form-locked");
            return;
        }

        const elnState = record.data.eln_state;
        const shouldLock =
            elnState &&
            !["1-draft", "4-rejected"].includes(elnState);

        if (shouldLock) {
            formEl.classList.add("eln-form-locked");
        } else {
            formEl.classList.remove("eln-form-locked");
        }
    }
});