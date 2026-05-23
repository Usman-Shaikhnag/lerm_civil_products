/** @odoo-module **/

import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";

patch(ListRenderer.prototype, {

    setup() {
        super.setup();
    },

    onCellKeydown(ev) {
        super.onCellKeydown?.(ev);

        const allowed = [
            "ArrowUp",
            "ArrowDown",
            "ArrowLeft",
            "ArrowRight",
            "Enter",
        ];

        if (!allowed.includes(ev.key)) {
            return;
        }

        const currentInput = ev.target;

        const currentCell = currentInput.closest("td");
        const currentRow = currentInput.closest("tr");

        if (!currentCell || !currentRow) {
            return;
        }

        const rows = Array.from(
            currentRow.parentElement.querySelectorAll("tr")
        );

        const cells = Array.from(
            currentRow.querySelectorAll("td")
        );

        const rowIndex = rows.indexOf(currentRow);
        const colIndex = cells.indexOf(currentCell);

        let targetRow = rowIndex;
        let targetCol = colIndex;

        switch (ev.key) {

            case "ArrowUp":
                targetRow--;
                break;

            case "ArrowDown":
            case "Enter":
                targetRow++;
                break;

            case "ArrowLeft":
                targetCol--;
                break;

            case "ArrowRight":
                targetCol++;
                break;
        }

        const nextRow = rows[targetRow];

        if (!nextRow) {
            return;
        }

        const nextCells = Array.from(
            nextRow.querySelectorAll("td")
        );

        const nextCell = nextCells[targetCol];

        if (!nextCell) {
            return;
        }

        const nextInput = nextCell.querySelector(
            "input, textarea"
        );

        if (!nextInput) {
            return;
        }

        ev.preventDefault();

        nextInput.focus();

        if (nextInput.select) {
            nextInput.select();
        }
    },
});