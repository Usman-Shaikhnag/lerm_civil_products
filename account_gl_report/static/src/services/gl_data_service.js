/** @odoo-module **/
import { registry } from "@web/core/registry";

export const glDataService = {
    dependencies: ["rpc"],
    start(env, { rpc }) {
        return {
            getData(params) {
                return rpc("/gl_report/get_data", params);
            },
            getLineDetails(lineId) {
                return rpc("/gl_report/get_line_details", { line_id: lineId });
            },
            getAttachments(moveId) {
                return rpc("/gl_report/get_attachments", { move_id: moveId });
            },
            searchAccounts(term) {
                return rpc("/gl_report/search_accounts", { term });
            },
            searchPartners(term) {
                return rpc("/gl_report/search_partners", { term });
            },
            searchAnalytic(term) {
                return rpc("/gl_report/search_analytic", { term });
            },
            getJournals() {
                return rpc("/gl_report/get_journals", {});
            },
            savePreset(name, paramsJson) {
                return rpc("/gl_report/save_preset", { name, params_json: paramsJson });
            },
            getPresets() {
                return rpc("/gl_report/get_presets", {});
            },
            deletePreset(presetId) {
                return rpc("/gl_report/delete_preset", { preset_id: presetId });
            },
            exportData(params, format) {
                return rpc("/gl_report/export", { params, export_format: format });
            },
        };
    },
};

registry.category("services").add("gl_report.data", glDataService);
