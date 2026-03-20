/** @odoo-module */
import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";

const actionRegistry = registry.category("actions");

class ProductDashboard extends Component {
  setup() {
    this.dashboard_state = useState({
      product_data: [],
    });

    this.filter_state = useState({
      start_date: this._getDateXDaysAgo(30),
      end_date: this._today(),
      activeDiscipline: "ALL",
      activeDays: 30,
      searchQuery: "",
      searchType: "all", // Options: all, product, srf, ulr, report
      isLoading: true,

      // Pagination State
      currentPage: 1,
      pageSize: 10,
      totalProducts: 0,
    });

    this.action = useService("action");
    this.rpc = useService("rpc");

    onWillStart(async () => {
      await this.fetchData();
    });
  }

  get totalPages() {
    const total = Number(this.filter_state.totalProducts) || 0;
    const size = Number(this.filter_state.pageSize) || 1;
    if (total === 0) return 1;
    return Math.ceil(total / size);
  }

  async fetchData() {
    this.filter_state.isLoading = true;
    const {
      start_date,
      end_date,
      activeDiscipline,
      searchQuery,
      searchType,
      currentPage,
      pageSize,
    } = this.filter_state;

    try {
      const result = await jsonrpc("/lerm/product/overview/data", {
        start_date,
        end_date,
        discipline: activeDiscipline,
        search_query: searchQuery,
        search_type: searchType,
        page_number: currentPage,
        page_size: pageSize,
      });

      this.dashboard_state.product_data = result.products || [];
      this.filter_state.totalProducts = Number(result.total_products) || 0;
    } catch (error) {
      console.error("Failed to fetch product data:", error);
    } finally {
      this.filter_state.isLoading = false;
    }
  }

  _today() {
    return new Date().toISOString().split("T")[0];
  }

  _getDateXDaysAgo(days) {
    const d = new Date();
    d.setDate(d.getDate() - days);
    return d.toISOString().split("T")[0];
  }

  _onDateInputChange(ev) {
    const field = ev.target.dataset.field;
    this.filter_state[field] = ev.target.value;
  }

  async _onDateFilter(ev) {
    const days = parseInt(ev.target.dataset.days);
    this.filter_state.start_date = this._getDateXDaysAgo(days);
    this.filter_state.end_date = this._today();
    this.filter_state.activeDays = days;
    this.filter_state.currentPage = 1;
    await this.fetchData();
  }

  async _onCustomDate() {
    if (this.filter_state.start_date && this.filter_state.end_date) {
      this.filter_state.activeDays = false;
      this.filter_state.currentPage = 1;
      await this.fetchData();
    }
  }

  async _onDisciplineFilter(ev) {
    const discipline = ev.currentTarget.dataset.discipline;
    this.filter_state.activeDiscipline = discipline;
    this.filter_state.currentPage = 1;
    await this.fetchData();
  }

  async _onSearchProduct(ev) {
    this.filter_state.searchQuery = ev.target.value.trim();
    this.filter_state.currentPage = 1;
    await this.fetchData();
  }

  async _onSearchTypeChange(ev) {
    this.filter_state.searchType = ev.target.value;
    this.filter_state.currentPage = 1;
    await this.fetchData();
  }

  async _onPageSizeChange(ev) {
    this.filter_state.pageSize = parseInt(ev.target.value, 10);
    this.filter_state.currentPage = 1;
    await this.fetchData();
  }

  async _onPageChange(change) {
    const newPage = this.filter_state.currentPage + change;
    if (newPage > 0 && newPage <= this.totalPages) {
      this.filter_state.currentPage = newPage;
      await this.fetchData();
    }
  }

  async _onProductCardClick(productId, productName) {
    const { start_date, end_date, activeDiscipline, searchQuery, searchType } = this.filter_state;

    const domain = [
      ["material_id", "=", productId],
      ["sample_received_date", ">=", start_date],
      ["sample_received_date", "<=", end_date],
      ...(activeDiscipline !== "ALL"
        ? [["discipline_id.discipline", "=", activeDiscipline]]
        : []),
    ];

    if (searchQuery) {
      const search_domain = [];
      if (searchType === 'all' || searchType === 'product') {
        search_domain.push(["material_id.name", "ilike", `%${searchQuery}%`]);
      }
      if (searchType === 'all' || searchType === 'srf') {
        search_domain.push(["srf_id", "ilike", `%${searchQuery}%`]);
      }
      if (searchType === 'all' || searchType === 'ulr') {
        search_domain.push(["ulr_no", "ilike", `%${searchQuery}%`]);
      }
      if (searchType === 'all' || searchType === 'report') {
        search_domain.push(["kes_no", "ilike", `%${searchQuery}%`]);
      }

      if (search_domain.length > 1) {
        const final_domain = [];
        for (let i = 0; i < search_domain.length - 1; i++) {
          final_domain.push('|');
        }
        domain.push(...final_domain.concat(search_domain));
      } else if (search_domain.length === 1) {
        domain.push(search_domain[0]);
      }
    }

    const action = {
      type: "ir.actions.act_window",
      name: `Samples for Product: ${productName}`,
      res_model: "lerm.srf.sample",
      views: [[false, "list"], [false, "form"]],
      domain: domain,
      context: { group_by: ["state"] },
    };

    return this.action.doAction(action);
  }
}

ProductDashboard.template = "lerm_civil_dashboard.ProductDashboard";
actionRegistry.add("product_dashboard", ProductDashboard);
