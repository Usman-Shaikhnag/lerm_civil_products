/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { jsonrpc } from "@web/core/network/rpc_service";
import { formatDate, formatDateTime, statusBadge, bindAll } from "../../utils";

export class DMSPropertiesPanel extends Component {
    static template = "document_management.DMSPropertiesPanel";

    static props = {
        file: Object,
        meta: Object,
        onClose: Function,
        onSave: Function,
    };

    setup() {
        const f = this.props.file;
        this.state = useState({
            draft: {
                name: f.name || "",
                document_type_id: f.documentTypeId || false,
                department_id: f.departmentId || false,
                project_id: f.projectId || false,
                customer_id: f.customerId || false,
                vendor_id: f.vendorId || false,
                employee_id: f.employeeId || false,
                document_date: f.documentDate || "",
                expiry_date: f.expiryDate || "",
                status: f.status || "draft",
                description: f.description || "",
                visibility: f.visibility || "private",
                tag_ids: f.tagIds || [],
                res_model: f.resModel || "",
                res_id: f.resId || false,
                related_record_name: f.relatedRecordName || "",
            },
            customValues: (f.customValues || []).map((cv) => ({
                field_id: cv.field_id,
                code: cv.code,
                name: cv.name,
                field_type: cv.field_type,
                value: cv.value,
            })),
            searchText: "",
            suggestions: [],
            searching: false,
        });
        bindAll(this, [
            "toggleTag",
            "save",
            "getCustomFieldDef",
            "selectionOptions",
            "fmtDateTime",
            "onModelChange",
            "onRecordSearch",
            "selectRecord",
            "clearReference",
        ]);
    }

    get modelOptions() {
        return this.props.meta.models || [];
    }

    onModelChange() {
        this.state.draft.res_id = false;
        this.state.draft.related_record_name = "";
        this.state.searchText = "";
        this.state.suggestions = [];
    }

    async onRecordSearch() {
        const model = this.state.draft.res_model;
        if (!model) {
            this.state.suggestions = [];
            return;
        }
        this.state.searching = true;
        try {
            const res = await jsonrpc("/dms/record_search", {
                model,
                term: this.state.searchText,
            });
            this.state.suggestions = res || [];
        } catch (e) {
            this.state.suggestions = [];
        } finally {
            this.state.searching = false;
        }
    }

    selectRecord(rec) {
        this.state.draft.res_id = rec.id;
        this.state.draft.related_record_name = rec.display_name;
        this.state.searchText = "";
        this.state.suggestions = [];
    }

    clearReference() {
        this.state.draft.res_id = false;
        this.state.draft.related_record_name = "";
        this.state.suggestions = [];
    }

    statusInfo(status) {
        return statusBadge(status);
    }

    get tagOptions() {
        return this.props.meta.tags || [];
    }

    get typeOptions() {
        return this.props.meta.types || [];
    }

    get deptOptions() {
        return this.props.meta.departments || [];
    }

    get projectOptions() {
        return this.props.meta.projects || [];
    }

    get customerOptions() {
        return this.props.meta.customers || [];
    }

    get vendorOptions() {
        return this.props.meta.vendors || [];
    }

    get employeeOptions() {
        return this.props.meta.employees || [];
    }

    get customValues() {
        return this.state.customValues;
    }

    getCustomFieldDef(fieldId) {
        return (this.props.meta.customFields || []).find((f) => f.id === fieldId) || null;
    }

    selectionOptions(cv) {
        const def = this.getCustomFieldDef(cv.field_id);
        return (def && def.selection_options) || [];
    }

    fmtDateTime(value) {
        return formatDateTime(value);
    }

    toggleTag(tagId) {
        const idx = this.state.draft.tag_ids.indexOf(tagId);
        if (idx >= 0) {
            this.state.draft.tag_ids.splice(idx, 1);
        } else {
            this.state.draft.tag_ids.push(tagId);
        }
    }

    save() {
        const customValues = this.state.customValues.map((cv) => ({
            field_id: cv.field_id,
            value: cv.value,
        }));
        const payload = {
            ...this.state.draft,
            id: this.props.file.id,
            custom_values: customValues,
        };
        if (!this.state.draft.res_model) {
            payload.res_model = false;
            payload.res_id = false;
        }
        this.props.onSave(payload);
        this.props.onClose();
    }
}
