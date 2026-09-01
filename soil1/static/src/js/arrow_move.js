/** @odoo-module **/

import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";

console.log("🔥 Arrow JS Loaded");

patch(ListRenderer.prototype, {

    setup() {
        super.setup();
        document.addEventListener("keydown", (ev) => {

            if (ev.key !== "ArrowUp" && ev.key !== "ArrowDown") return;

            const list = this.props.list;
            if (!list || !list.records.length) return;

            if (list.model.config.resModel !== "consolidation.both.cycle.line") return;

            const active = document.activeElement;
            const row = active.closest(".o_data_row");

            if (!row) return;

            const rows = Array.from(document.querySelectorAll(".o_data_row"));
            const index = rows.indexOf(row);

            let targetIndex = ev.key === "ArrowUp" ? index - 1 : index + 1;

            if (targetIndex < 0 || targetIndex >= rows.length) return;

            const record = list.records[index];
            const target = list.records[targetIndex];

            // swap
            let temp = record.data.sequence;
            record.data.sequence = target.data.sequence;
            target.data.sequence = temp;

            list.model.notify();

            setTimeout(() => {
                rows[targetIndex].querySelector("input")?.focus();
            }, 50);

        });
    },
});