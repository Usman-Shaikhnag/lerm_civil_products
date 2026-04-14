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
      aging_data: {},
      labs: [],
      companies: [],
    });

    this.filter_state = useState({
      start_date: this._getDateXDaysAgo(30),
      end_date: this._today(),
      activeDiscipline: "ALL",
      activeLab: "ALL",
      activeCompany: "ALL",
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
      const filterOptions = await jsonrpc("/dashboard/get_filter_options", {});
      this.dashboard_state.labs = filterOptions.labs || [];
      this.dashboard_state.companies = filterOptions.companies || [];
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
      activeLab,
      activeCompany,
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
        lab_id: activeLab,
        company_id: activeCompany,
        search_query: searchQuery,
        search_type: searchType,
        page_number: currentPage,
        page_size: pageSize,
      });

      this.dashboard_state.product_data = result.products || [];
      this.dashboard_state.aging_data = result.aging_data || {};
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

  get filteredLabs() {
    if (this.filter_state.activeCompany === "ALL") {
      return this.dashboard_state.labs;
    }
    const companyId = parseInt(this.filter_state.activeCompany);
    return this.dashboard_state.labs.filter(
        (lab) => lab.company_id === companyId,
    );
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

  async _onLabFilter(ev) {
    this.filter_state.activeLab = ev.target.value;
    this.filter_state.currentPage = 1;
    await this.fetchData();
  }

  async _onCompanyFilter(ev) {
    this.filter_state.activeCompany = ev.target.value;
    this.filter_state.activeLab = "ALL"; // Reset lab when company changes
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

  get filteredLabs() {
    if (this.filter_state.activeCompany === "ALL") {
      return this.dashboard_state.labs;
    }
    return this.dashboard_state.labs.filter(
      (l) => l.company_id === parseInt(this.filter_state.activeCompany)
    );
  }

  async _onLabFilter(ev) {
    this.filter_state.activeLab = ev.target.value;
    this.filter_state.currentPage = 1;
    await this.fetchData();
  }

  async _onCompanyFilter(ev) {
    this.filter_state.activeCompany = ev.target.value;
    this.filter_state.activeLab = "ALL";
    this.filter_state.currentPage = 1;
    await this.fetchData();
  }

  get styleMap() {
    return {
      "1-allotment_pending": { icon: "fa-hourglass-o", color: "#fd7e14", label: "Assignment Pending" },
      "7-partially-alloted": { icon: "fa-adjust", color: "#8b5cf6", label: "Partially Alloted" },
      "2-alloted": { icon: "fa-play-circle", color: "#0066ff", label: "Alloted" },
      "7-calculated": { icon: "fa-calculator", color: "#6366f1", label: "Calculated" },
      "3-pending_verification": { icon: "fa-hourglass-half", color: "#d97706", label: "Pending Verification" },
      "5-pending_approval": { icon: "fa-clock-o", color: "#dc2626", label: "Pending Approval" },
      "4-in_report": { icon: "fa-file-text-o", color: "#16a34a", label: "In Report" },
      "6-cancelled": { icon: "fa-times-circle", color: "#9ca3af", label: "Cancelled" },
    };
  }

  get agingKpiData() {
    const buckets = [
      { key: "0-7", label: "0-7 Days", color: "#10b981", icon: "fa-clock-o" },
      { key: "8-15", label: "8-15 Days", color: "#f59e0b", icon: "fa-calendar-minus-o" },
      { key: "16-30", label: "16-30 Days", color: "#ef4444", icon: "fa-calendar-plus-o" },
      { key: "31-45", label: "31-45 Days", color: "#b91c1c", icon: "fa-hourglass-end" },
      { key: "46-60", label: "46-60 Days", color: "#7f1d1d", icon: "fa-warning" },
      { key: "60+", label: "60+ Days", color: "#450a0a", icon: "fa-history" },
    ];

    if (!this.dashboard_state.aging_data) return [];

    return buckets.map(bucket => {
      const bucketData = this.dashboard_state.aging_data[bucket.key] || { total: 0, states: {} };
      return {
        key: bucket.key,
        label: bucket.label,
        count: bucketData.total,
        states: Object.entries(bucketData.states).map(([stateKey, stateData]) => {
          const style = this.styleMap[stateKey] || { icon: "fa-question-circle", color: "#6c757d", label: stateKey };
          return {
            key: stateKey,
            label: style.label,
            count: stateData.count,
            breakdown: stateData.breakdown || [],
            icon: style.icon,
            color: style.color
          };
        }),
        color: bucket.color,
        icon: bucket.icon
      };
    });
  }

  async onAgingClick(bucketKey, stateKey = null, productId = null) {
    const today = new Date();
    let minDays, maxDays;
    if (bucketKey === "60+") {
        minDays = 61;
        maxDays = null;
    } else {
        [minDays, maxDays] = bucketKey.split("-").map(Number);
    }
    
    const pad = (n) => n.toString().padStart(2, "0");
    const toDateStr = (d) =>
      `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

    // Create new date objects for boundaries
    const dMax = new Date(today);
    dMax.setDate(today.getDate() - minDays);
    const dMaxStr = `${toDateStr(dMax)} 23:59:59`;
    
    let dMinStr = null;
    if (maxDays !== null) {
        const dMin = new Date(today);
        dMin.setDate(today.getDate() - maxDays);
        dMinStr = `${toDateStr(dMin)} 00:00:00`;
    }

    const domain = [
        ["state", "in", ["2-alloted", "7-calculated", "3-pending_verification", "5-pending_approval"]],
        ["eln_id", "!=", false],
        ["eln_id.create_date", "<=", dMaxStr],
    ];

    if (dMinStr) {
        domain.push(["eln_id.create_date", ">=", dMinStr]);
    }

    if (stateKey) {
        domain.push(["state", "=", stateKey]);
    }

    if (productId) {
        domain.push(["material_id", "=", productId]);
    }

    if (this.filter_state.activeDiscipline !== "ALL") {
        domain.push(["discipline_id.discipline", "=", this.filter_state.activeDiscipline]);
    }
    
    if (this.filter_state.activeLab !== "ALL") {
        domain.push(["lab_location", "=", parseInt(this.filter_state.activeLab)]);
    }
    
    if (this.filter_state.activeCompany !== "ALL") {
        domain.push(["lab_location.company_id", "=", parseInt(this.filter_state.activeCompany)]);
    }

    if (this.filter_state.searchQuery) {
        if (this.filter_state.searchType === 'all' || this.filter_state.searchType === 'product') {
            domain.push(["material_id.name", "ilike", `%${this.filter_state.searchQuery}%`]);
        } else if (this.filter_state.searchType === 'srf') {
            domain.push(["srf_id.srf_id", "ilike", `%${this.filter_state.searchQuery}%`]);
        } else if (this.filter_state.searchType === 'ulr') {
            domain.push(["ulr_no", "ilike", `%${this.filter_state.searchQuery}%`]);
        } else if (this.filter_state.searchType === 'report') {
            domain.push(["kes_no", "ilike", `%${this.filter_state.searchQuery}%`]);
        }
    }

    const action = {
        type: "ir.actions.act_window",
        name: `Samples - Aging ${bucketKey}`,
        res_model: "lerm.srf.sample",
        views: [[false, "list"], [false, "form"]],
        domain: domain,
        context: { group_by: ["state", "sample_received_date:day"] },
    };

    return this.action.doAction(action);
  }

  async _onPageChange(change) {
    const newPage = this.filter_state.currentPage + change;
    if (newPage > 0 && newPage <= this.totalPages) {
      this.filter_state.currentPage = newPage;
      await this.fetchData();
    }
  }

  async _onProductDetailsClick(productId, productName, stateName = null) {
    const { start_date, end_date, activeDiscipline, activeLab, activeCompany, searchQuery, searchType } = this.filter_state;

    const domain = [
      ["sample_received_date", ">=", start_date],
      ["sample_received_date", "<=", end_date],
      ...(activeDiscipline !== "ALL"
        ? [["discipline_id.discipline", "=", activeDiscipline]]
        : []),
      ...(activeLab !== "ALL"
        ? [["lab_location", "=", parseInt(activeLab)]]
        : []),
      ...(activeCompany !== "ALL"
        ? [["lab_location.company_id", "=", parseInt(activeCompany)]]
        : []),
    ];

    if (productId === 0) {
      domain.push(["material_id", "=", false]);
    } else {
      domain.push(["material_id", "=", productId]);
    }

    if (stateName) {
      if (stateName === "invoiced") {
          domain.push(["invoice_status", "=", "2-invoiced"]);
      } else if (stateName === "uninvoiced") {
          domain.push(["invoice_status", "=", "1-uninvoiced"]);
      } else {
          domain.push(["state", "=", stateName]);
      }
    }

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

    let actionName = `Samples for Product: ${productName}`;
    if (stateName) {
      const stateLabelMap = {
        "2-alloted": "Alloted",
        "3-pending_verification": "Verification Pending",
        "5-pending_approval": "Approval Pending",
        "4-in_report": "In Report",
        "6-cancelled": "Cancelled",
        "invoiced": "Invoiced",
        "uninvoiced": "Uninvoiced",
        "1-allotment_pending": "Assignment Pending"
      };
      actionName = `${actionName} - ${stateLabelMap[stateName] || stateName}`;
    }

    const action = {
      type: "ir.actions.act_window",
      name: actionName,
      res_model: "lerm.srf.sample",
      views: [[false, "list"], [false, "form"]],
      domain: domain,
      context: { group_by: ["state"] },
    };

    return this.action.doAction(action);
  }

  async _onProductCardClick(productId, productName) {
      return this._onProductDetailsClick(productId, productName);
  }
}

ProductDashboard.template = "lerm_civil_dashboard.ProductDashboard";
actionRegistry.add("product_dashboard", ProductDashboard);
