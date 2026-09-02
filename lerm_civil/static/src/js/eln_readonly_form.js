/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { FormRenderer } from "@web/views/form/form_renderer";
import { useService } from "@web/core/utils/hooks";
import { onMounted, onPatched } from "@odoo/owl";

/**
 * Global patch: automatically makes any form with `eln_state` field
 * readonly (visually locked) when eln_state is not '1-draft'.
 * Users in either the "Lerm Admin" group or the "Datasheet Edit"
 * group bypass this lock.
 */
patch(FormRenderer.prototype, {
    setup() {
        super.setup(...arguments);

        this.userService = useService("user");
        this._canEditLockedForms = false;
        this._groupsChecked = false;

        // Check both groups once on setup
        Promise.all([
            this.userService.hasGroup("lerm_civil.kes_admin_access_group"),
            this.userService.hasGroup("lerm_civil.lerm_datasheet_edit_group"),
        ]).then(([isAdmin, isDatasheetEditor]) => {
            this._canEditLockedForms = isAdmin || isDatasheetEditor;
            this._groupsChecked = true;
            this._applyElnReadonly();
        });

        onMounted(() => this._applyElnReadonly());
        onPatched(() => this._applyElnReadonly());
    },

    _applyElnReadonly() {
        const record = this.props.record;
        if (!record || !record.data) {
            return;
        }

        // Apply only on forms having eln_state
        if (!("eln_state" in record.data)) {
            return;
        }

        const formEl =
            this.__owl__.bdom?.el?.closest?.(".o_form_view") ||
            document.querySelector(".o_form_view");

        if (!formEl) {
            return;
        }

        // Admins and Datasheet Edit users can always edit
        if (this._canEditLockedForms) {
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
    },
});