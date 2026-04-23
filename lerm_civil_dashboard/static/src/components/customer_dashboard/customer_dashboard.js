/** @odoo-module */
import { registry } from "@web/core/registry";
import { Component, onWillStart, useState, useRef, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";

const actionRegistry = registry.category("actions");
class CustomerDashboard extends Component {
  setup() {
    this.dashboard_state = useState({
      customer_data: [],
      aging_data: {},
      overdue_data: {},
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
      isLoading: true,

      // NEW: Pagination State
      currentPage: 1,
      pageSize: 10, // Default page size
      totalCustomers: 0,
    });

    this.action = useService("action");
    this.rpc = useService("rpc");

    this.styleMap = {
      "1-allotment_pending": { icon: "fa-hourglass-o", color: "#fd7e14", label: "Assignment Pending" },
      "7-partially-alloted": { icon: "fa-adjust", color: "#8b5cf6", label: "Partially Alloted" },
      "2-alloted": { icon: "fa-play-circle", color: "#0066ff", label: "Alloted" },
      "7-calculated": { icon: "fa-calculator", color: "#6366f1", label: "Calculated" },
      "3-pending_verification": { icon: "fa-hourglass-half", color: "#d97706", label: "Pending Verification" },
      "5-pending_approval": { icon: "fa-clock-o", color: "#dc2626", label: "Pending Approval" },
      "4-in_report": { icon: "fa-file-text-o", color: "#16a34a", label: "In Report" },
      "6-cancelled": { icon: "fa-times-circle", color: "#9ca3af", label: "Cancelled" },
    };

    onWillStart(async () => {
      const filterOptions = await jsonrpc("/dashboard/get_filter_options", {});
      this.dashboard_state.labs = filterOptions.labs || [];
      this.dashboard_state.companies = filterOptions.companies || [];
      await this.fetchData();
    });
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

    const data = this.dashboard_state.aging_data || {};
    return buckets.map((b) => {
      const bucketData = data[b.key] || { total: 0, states: {} };
      const states = Object.entries(bucketData.states).map(([stateKey, stateData]) => {
        const style = this.styleMap[stateKey] || { icon: "fa-question-circle", color: "#6c757d", label: stateKey };
        return {
          key: stateKey,
          label: style.label,
          icon: style.icon,
          color: style.color,
          count: stateData.count,
          breakdown: stateData.breakdown || [],
        };
      });

      return {
        ...b,
        count: bucketData.total,
        states: states,
        mode: 'upcoming'
      };
    });
  }

  get overdueKpiData() {
    const buckets = [
      { key: "0-7", label: "0-7 Days", color: "#10b981", icon: "fa-clock-o" },
      { key: "8-15", label: "8-15 Days", color: "#f59e0b", icon: "fa-calendar-minus-o" },
      { key: "16-30", label: "16-30 Days", color: "#ef4444", icon: "fa-calendar-plus-o" },
      { key: "31-45", label: "31-45 Days", color: "#b91c1c", icon: "fa-hourglass-end" },
      { key: "46-60", label: "46-60 Days", color: "#7f1d1d", icon: "fa-warning" },
      { key: "60+", label: "60+ Days", color: "#450a0a", icon: "fa-history" },
    ];

    const data = this.dashboard_state.overdue_data || {};
    return buckets.map((b) => {
      const bucketData = data[b.key] || { total: 0, states: {} };
      const states = Object.entries(bucketData.states).map(([stateKey, stateData]) => {
        const style = this.styleMap[stateKey] || { icon: "fa-question-circle", color: "#6c757d", label: stateKey };
        return {
          key: stateKey,
          label: style.label,
          icon: style.icon,
          color: style.color,
          count: stateData.count,
          breakdown: stateData.breakdown || [],
        };
      });

      return {
        ...b,
        count: bucketData.total,
        states: states,
        mode: 'overdue'
      };
    });
  }

  get filteredLabs() {
    if (this.filter_state.activeCompany === "ALL") {
      return this.dashboard_state.labs;
    }
    return this.dashboard_state.labs.filter(
      (l) => l.company_id === parseInt(this.filter_state.activeCompany)
    );
  }

  // NEW: Computed property for total pages
  get totalPages() {
    // Ensure both values are treated as numbers and safely default if missing/zero
    const total = Number(this.filter_state.totalCustomers) || 0;
    // Default page size to 1 to prevent division by zero
    const size = Number(this.filter_state.pageSize) || 1;

    if (total === 0) {
      return 1; // If there are no results, we show page 1 of 1
    }

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
      currentPage,
      pageSize,
    } = this.filter_state;

    try {
      const result = await jsonrpc("/lerm/customer/overview/data", {
        start_date,
        end_date,
        discipline: activeDiscipline,
        lab_id: activeLab,
        company_id: activeCompany,
        search_query: searchQuery,

        // NEW: Send Pagination params
        page_number: currentPage,
        page_size: pageSize,
      });

      // Update state with paginated data and total count from the backend
      this.dashboard_state.customer_data = result.customers || [];
      this.dashboard_state.aging_data = result.aging_data || {};
      this.dashboard_state.overdue_data = result.overdue_data || {};
      this.filter_state.totalCustomers = Number(result.total_customers) || 0;
    } catch (error) {
      console.error("Failed to fetch customer data:", error);
    } finally {
      this.filter_state.isLoading = false;
    }
  }

  // --- Date Utility Methods ---

  _today() {
    return new Date().toISOString().split("T")[0];
  }

  _getDateXDaysAgo(days) {
    const d = new Date();
    d.setDate(d.getDate() - days);
    return d.toISOString().split("T")[0];
  }

  // --- Filter Handlers (Copied/Modified from MainDashboard) ---

  _onDateInputChange(ev) {
    const field = ev.target.dataset.field; // 'start_date' or 'end_date'
    this.filter_state[field] = ev.target.value;
  }

  async _onDateFilter(ev) {
    const days = parseInt(ev.target.dataset.days);
    this.filter_state.start_date = this._getDateXDaysAgo(days);
    this.filter_state.end_date = this._today();
    this.filter_state.activeDays = days;
    this.filter_state.currentPage = 1; // Reset page
    await this.fetchData();
  }

  async _onCustomDate() {
    const start = this.filter_state.start_date;
    const end = this.filter_state.end_date;
    if (start && end) {
      this.filter_state.activeDays = false;
      this.filter_state.currentPage = 1; // Reset page
      await this.fetchData();
    } else {
      console.warn(
        "Custom date filter requires both start and end dates to be set."
      );
    }
  }

  async _onDisciplineFilter(ev) {
    const discipline = ev.currentTarget.dataset.discipline;
    this.filter_state.activeDiscipline = discipline;
    this.filter_state.currentPage = 1; // Reset page
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

  async onAgingClick(bucketKey, stateKey = null, techId = null, mode = 'upcoming') {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

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

    let dMinStr = null;
    let dMaxStr = null;

    if (mode === 'upcoming') {
      const dMin = new Date(today);
      dMin.setDate(today.getDate() + minDays);
      dMinStr = toDateStr(dMin);

      if (maxDays !== null) {
        const dMax = new Date(today);
        dMax.setDate(today.getDate() + maxDays);
        dMaxStr = toDateStr(dMax);
      }
    } else {
      // Overdue mode
      const effectiveMin = Math.max(1, minDays);
      const dMax = new Date(today);
      dMax.setDate(today.getDate() - effectiveMin);
      dMaxStr = toDateStr(dMax);

      if (maxDays !== null) {
        const dMin = new Date(today);
        dMin.setDate(today.getDate() - maxDays);
        dMinStr = toDateStr(dMin);
      }
    }

    const domain = [
      [
        "state",
        "in",
        [
          "1-allotment_pending",
          "2-alloted",
          "7-calculated",
          "3-pending_verification",
          "5-pending_approval",
        ],
      ],
      ["report_due_date", "!=", false],
    ];

    if (dMinStr) {
      domain.push(["report_due_date", ">=", dMinStr]);
    }
    if (dMaxStr) {
      domain.push(["report_due_date", "<=", dMaxStr]);
    }

    if (stateKey) {
      domain.push(["state", "=", stateKey]);
    }

    if (techId) {
      domain.push(
        "|",
        "|",
        "|",
        ["technicians", "in", [techId]],
        ["eln_id.technician", "=", techId],
        ["eln_id.technician_ids", "in", [techId]],
        ["eln_id.parameters_result.technician", "=", techId]
      );
    }

    // Apply dashboard-wide filters
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
        domain.push(["customer_id.name", "ilike", this.filter_state.searchQuery]);
    }

    const action = {
      type: "ir.actions.act_window",
      name: `${mode === 'upcoming' ? 'Upcoming Due' : 'Overdue'}: ${bucketKey} Days`,
      res_model: "lerm.srf.sample",
      views: [[false, "list"], [false, "form"]],
      domain: domain,
      context: { group_by: ["state", "material_id"] },
    };

    return this.action.doAction(action);
  }

  // Uses both change and keyup to provide a fluid search experience
  async _onSearchCustomer(ev) {
    this.filter_state.searchQuery = ev.target.value.trim();
    this.filter_state.currentPage = 1; // Reset page
    await this.fetchData();
  }

  async _onPageSizeChange(ev) {
    // Ensure value is parsed as an integer
    this.filter_state.pageSize = parseInt(ev.target.value, 10);
    this.filter_state.currentPage = 1; // Always go to page 1 when size changes
    await this.fetchData();
  }

  async _onPageChange(change) {
    const newPage = this.filter_state.currentPage + change;
    if (newPage > 0 && newPage <= this.totalPages) {
      this.filter_state.currentPage = newPage;
      await this.fetchData();
    }
  }

  // --- Customer Card Click Handler ---

  // --- Customer Card Click Handler ---

  async _onCustomerDetailsClick(customerId, customerName, stateName = null, productId = null) {
    const domain = [
      ["sample_received_date", ">=", this.filter_state.start_date],
      ["sample_received_date", "<=", this.filter_state.end_date],

      // Conditionally add the discipline filter
      ...(this.filter_state.activeDiscipline !== "ALL"
        ? [
            [
              "discipline_id.discipline",
              "=",
              this.filter_state.activeDiscipline,
            ],
          ]
        : []),
    ];

    if (customerId === 0) {
      domain.push(["customer_id", "=", false]);
    } else {
      domain.push(["customer_id", "=", customerId]);
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

    if (productId !== null) {
      if (productId === 0) {
        domain.push(["material_id", "=", false]);
      } else {
        domain.push(["material_id", "=", productId]);
      }
    }

    let actionName = `Samples for Customer: ${customerName}`;
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
      views: [
        [false, "list"],
        [false, "form"],
      ],
      domain: domain,
      context: {
        group_by: stateName ? ["material_id"] : ["state"],
      },
    };

    return this.action.doAction(action);
  }

  async _onCustomerCardClick(customerId, customerName) {
      return this._onCustomerDetailsClick(customerId, customerName);
  }
}
CustomerDashboard.template = "lerm_civil_dashboard.CustomerDashboard";
actionRegistry.add("customer_dashboard", CustomerDashboard);
