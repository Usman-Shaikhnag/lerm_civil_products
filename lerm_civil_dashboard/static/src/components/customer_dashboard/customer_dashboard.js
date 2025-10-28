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
    });

    this.filter_state = useState({
      start_date: this._getDateXDaysAgo(30),
      end_date: this._today(),
      activeDiscipline: "ALL",
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

    onWillStart(async () => {
      await this.fetchData();
    });
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
      searchQuery,
      currentPage,
      pageSize,
    } = this.filter_state;

    try {
      const result = await this.rpc("/lerm/customer/overview/data", {
        start_date,
        end_date,
        discipline: activeDiscipline,
        search_query: searchQuery,

        // NEW: Send Pagination params
        page_number: currentPage,
        page_size: pageSize,
      });

      // Update state with paginated data and total count from the backend
      this.dashboard_state.customer_data = result.customers || [];
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

  // --- NEW: Search Handler ---

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

  async _onCustomerCardClick(customerId, customerName) {
    const domain = [
      ["customer_id", "=", customerId],
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

    const action = {
      type: "ir.actions.act_window",
      name: `Samples for Customer: ${customerName}`,
      res_model: "lerm.srf.sample",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      domain: domain,
      context: {
        group_by: ["state"],
      },
    };

    return this.action.doAction(action);
  }
}
CustomerDashboard.template = "lerm_civil_dashboard.CustomerDashboard";
actionRegistry.add("customer_dashboard", CustomerDashboard);
