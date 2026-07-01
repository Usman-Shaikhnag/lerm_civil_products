/** @odoo-module **/
import { Component, onMounted, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { jsonrpc } from "@web/core/network/rpc_service";

export class SalespersonFilter extends Component {
    static props = ["*"];
    static template = "customer_ageing_dashboard.SalespersonFilter";

    setup() {
        this.state = useState({
            salespersons: [],
            selected: this._loadSelection() || [],
        });
        onWillStart(async () => {
            try {
                const data = await jsonrpc("/customer_ageing/salespersons", {});
                this.state.salespersons = data;
                if (this.state.selected.length === 0) {
                    this.state.selected = data.map((s) => s.id);
                }
            } catch (e) {
                console.error("SalespersonFilter fetch error", e);
            }
        });
        onMounted(() => this._emit());
    }

    _loadSelection() {
        try {
            const saved = localStorage.getItem("customer_ageing_dashboard_sp");
            return saved ? JSON.parse(saved) : [];
        } catch (e) {
            return [];
        }
    }

    _save() {
        try {
            localStorage.setItem("customer_ageing_dashboard_sp", JSON.stringify(this.state.selected));
        } catch (e) {}
    }

    _emit() {
        if (this.props.onChange) {
            this.props.onChange(this.state.selected);
        }
    }

    get allSelected() {
        return this.state.salespersons.length > 0 && this.state.selected.length === this.state.salespersons.length;
    }

    _onSelectAll() {
        this.state.selected = this.allSelected ? [] : this.state.salespersons.map((s) => s.id);
        this._save();
        this._emit();
    }

    _onToggle(id) {
        const idx = this.state.selected.indexOf(id);
        if (idx >= 0) {
            this.state.selected.splice(idx, 1);
        } else {
            this.state.selected.push(id);
        }
        this._save();
        this._emit();
    }

    _onToggleClick(ev) {
        const id = ev.currentTarget.dataset.spId;
        if (id === undefined) return;
        this._onToggle(id === "unassigned" ? "unassigned" : parseInt(id, 10));
    }
}

registry.category("components").add("SalespersonFilter", SalespersonFilter);
