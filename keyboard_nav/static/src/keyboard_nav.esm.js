/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormRenderer } from "@web/views/form/form_renderer";
import { ListRenderer } from "@web/views/list/list_renderer";
import { onMounted, onPatched, onWillUnmount, useRef } from "@odoo/owl";

const FOCUSABLE_SELECTOR = [
    'input:not([type="hidden"]):not([disabled])',
    "select:not([disabled])",
    "textarea:not([disabled])",
    '[contenteditable]:not([disabled])',
].join(", ");

patch(FormRenderer.prototype, {
    setup() {
        super.setup();
        this._navFields = [];
        this._navActiveIdx = -1;
        this._navRootRef = useRef("compiled_view_root");
        this._onNavKeydown = this._onNavKeydown.bind(this);
        onMounted(() => {
            this._navIndexFields();
            document.addEventListener("keydown", this._onNavKeydown);
        });
        onPatched(() => {
            this._navIndexFields();
        });
        onWillUnmount(() => {
            document.removeEventListener("keydown", this._onNavKeydown);
        });
    },

    _navIndexFields() {
        this._navFields = [];
        const root = this._navRootRef.el;
        if (!root) return;
        const containers = root.querySelectorAll(".o_field_widget");
        for (const el of containers) {
            if (this._navIsFieldHidden(el)) continue;
            const focusEl = this._navGetFocusable(el);
            if (!focusEl) continue;
            this._navFields.push({ el, focusEl });
        }
    },

    _navIsFieldHidden(el) {
        if (el.classList.contains("o_invisible_modifier")) return true;
        if (el.classList.contains("o_readonly_modifier")) return true;
        if (el.classList.contains("d-none")) return true;
        if (el.closest(".o_invisible_modifier")) return true;
        const style = getComputedStyle(el);
        if (style.display === "none" || style.visibility === "hidden") return true;
        return false;
    },

    _navGetFocusable(container) {
        let focusEl = container.querySelector(FOCUSABLE_SELECTOR);
        if (!focusEl) {
            focusEl = container.querySelector('[tabindex]:not([tabindex="-1"])');
        }
        return focusEl;
    },

    _onNavKeydown(ev) {
        if (ev.target.closest(".o_field_x2many")) return;
        if (ev.target.closest(".o_dialog")) return;
        if (ev.target.closest("[contenteditable]")) return;
        if (ev.target.closest(".o_m2o_dropdown") || ev.target.closest(".ui-autocomplete")) return;

        const key = ev.key;
        const dirs = { ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right" };
        const direction = dirs[key];
        if (!direction) return;

        const tag = ev.target.tagName;
        const isTextInput = tag === "INPUT" && !["checkbox", "radio", "button", "submit", "range"].includes(ev.target.type);
        const isTextArea = tag === "TEXTAREA";
        if ((isTextInput || isTextArea) && (direction === "left" || direction === "right")) {
            const { selectionStart, selectionEnd, value } = ev.target;
            if (selectionStart !== selectionEnd || (direction === "left" && selectionStart > 0) || (direction === "right" && selectionStart < value.length)) {
                return;
            }
        }

        ev.preventDefault();
        this._navMoveTo(direction);
    },

    _navGetCurrentIndex() {
        const active = document.activeElement;
        if (!active) return -1;
        for (let i = 0; i < this._navFields.length; i++) {
            const entry = this._navFields[i];
            if (entry.el.contains(active) || entry.focusEl === active) {
                return i;
            }
        }
        return -1;
    },

    _navMoveTo(direction) {
        this._navIndexFields();
        const currentIdx = this._navGetCurrentIndex();
        let targetIdx = currentIdx;

        switch (direction) {
            case "left":
                targetIdx = currentIdx > 0 ? currentIdx - 1 : -1;
                break;
            case "right":
                targetIdx = currentIdx < this._navFields.length - 1 ? currentIdx + 1 : -1;
                break;
            case "up":
            case "down":
                targetIdx = this._navFindVerticalTarget(currentIdx, direction);
                break;
        }

        if (targetIdx >= 0 && targetIdx < this._navFields.length) {
            this._navFocusField(targetIdx);
        }
    },

    _navFindVerticalTarget(currentIdx, direction) {
        if (currentIdx < 0) return direction === "down" ? 0 : this._navFields.length - 1;

        const current = this._navFields[currentIdx];
        const currentRect = current.focusEl.getBoundingClientRect();
        const currentCenterX = currentRect.left + currentRect.width / 2;
        const currentCenterY = currentRect.top + currentRect.height / 2;

        let bestIdx = -1;
        let bestDist = Infinity;

        for (let i = 0; i < this._navFields.length; i++) {
            if (i === currentIdx) continue;
            const entry = this._navFields[i];
            const rect = entry.focusEl.getBoundingClientRect();
            const centerY = rect.top + rect.height / 2;

            const isBelow = direction === "down" && centerY > currentCenterY;
            const isAbove = direction === "up" && centerY < currentCenterY;
            if (!isBelow && !isAbove) continue;

            const centerX = rect.left + rect.width / 2;
            const xDist = Math.abs(centerX - currentCenterX);
            const yDist = direction === "down" ? centerY - currentCenterY : currentCenterY - centerY;
            const score = xDist + yDist * 3;

            if (score < bestDist) {
                bestDist = score;
                bestIdx = i;
            }
        }

        if (bestIdx === -1) {
            bestIdx = direction === "down" ? Math.min(currentIdx + 1, this._navFields.length - 1) : Math.max(currentIdx - 1, 0);
        }
        return bestIdx;
    },

    _navFocusField(idx) {
        this._navClearFocus();
        const entry = this._navFields[idx];
        if (!entry) return;

        this._navActivateNotebookPage(entry.el);

        const focusEl = entry.focusEl;
        focusEl.focus();
        focusEl.scrollIntoView({ block: "nearest", behavior: "smooth" });
        entry.el.classList.add("o_kbdnav_focus");
        this._navActiveIdx = idx;
    },

    _navClearFocus() {
        for (const entry of this._navFields) {
            entry.el.classList.remove("o_kbdnav_focus");
        }
        this._navActiveIdx = -1;
    },

    _navActivateNotebookPage(el) {
        const page = el.closest(".o_notebook_page");
        if (!page) return;
        if (page.classList.contains("active")) return;
        const notebook = page.closest(".o_notebook");
        if (!notebook) return;
        const tabLink = notebook.querySelector(`[data-target="${page.id}"]`) ||
                        notebook.querySelector(`a[href="#${page.id}"]`);
        if (tabLink) {
            tabLink.click();
        }
    },
});

patch(ListRenderer.prototype, {
    onCellKeydownEditMode(hotkey, cell, group, record) {
        const spreadsheetHotkeys = ["arrowup", "arrowdown", "arrowleft", "arrowright", "shift+enter"];
        if (spreadsheetHotkeys.includes(hotkey)) {
            const handled = this._onCellKeydownSpreadsheet(hotkey, cell, group, record);
            if (handled) {
                this.lastCreatingAction = false;
                this.tableRef.el.querySelector("tbody").classList.add("o_keyboard_navigation");
            }
            return handled;
        }
        return super.onCellKeydownEditMode(hotkey, cell, group, record);
    },

    _getColumnByCell(cell) {
        const colName = cell.getAttribute("name");
        if (!colName) return null;
        return this.state.columns.find((col) => col.name === colName) || null;
    },

    _onCellKeydownSpreadsheet(hotkey, cell, group, record) {
        const row = cell.parentElement;
        const list = this.props.list;

        switch (hotkey) {
            case "arrowleft": {
                const prev = this.findPreviousFocusableOnRow(row, cell);
                if (prev) { this.focus(prev); return true; }
                return false;
            }
            case "arrowright": {
                const next = this.findNextFocusableOnRow(row, cell);
                if (next) { this.focus(next); return true; }
                return false;
            }
            case "arrowdown": {
                const recIndex = list.records.indexOf(record);
                const nextRecord = list.records[recIndex + 1];
                if (nextRecord) {
                    const column = this._getColumnByCell(cell);
                    this.cellToFocus = { column, record: nextRecord, forward: true };
                    list.leaveEditMode({ validate: true }).then((canProceed) => {
                        if (canProceed) {
                            list.enterEditMode(nextRecord).then(() => {
                                this.focusCell(column, true);
                            });
                        }
                    });
                    return true;
                }
                if (this.canCreate) {
                    const column = this._getColumnByCell(cell);
                    this.add({ group });
                    const newRecord = list.records[list.records.length - 1];
                    if (newRecord) {
                        this.cellToFocus = { column, record: newRecord, forward: true };
                        list.leaveEditMode({ validate: true }).then((canProceed) => {
                            if (canProceed) {
                                list.enterEditMode(newRecord).then(() => {
                                    this.focusCell(column, true);
                                });
                            }
                        });
                    }
                    return true;
                }
                return false;
            }
            case "arrowup": {
                const recIndex = list.records.indexOf(record);
                const prevRecord = list.records[recIndex - 1];
                if (prevRecord) {
                    const column = this._getColumnByCell(cell);
                    this.cellToFocus = { column, record: prevRecord, forward: true };
                    list.leaveEditMode({ validate: true }).then((canProceed) => {
                        if (canProceed) {
                            list.enterEditMode(prevRecord).then(() => {
                                this.focusCell(column, true);
                            });
                        }
                    });
                    return true;
                }
                return false;
            }
            case "shift+enter": {
                const recIndex = list.records.indexOf(record);
                const prevRecord = list.records[recIndex - 1];
                if (prevRecord) {
                    const column = this._getColumnByCell(cell);
                    this.cellToFocus = { column, record: prevRecord, forward: true };
                    list.leaveEditMode({ validate: true }).then((canProceed) => {
                        if (canProceed) {
                            list.enterEditMode(prevRecord).then(() => {
                                this.focusCell(column, true);
                            });
                        }
                    });
                    return true;
                }
                return false;
            }
        }
        return false;
    },
});
