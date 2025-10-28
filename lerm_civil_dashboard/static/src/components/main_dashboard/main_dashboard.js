/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, useState, useRef, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";

const actionRegistry = registry.category("actions");
const KpiBox = registry.category("components").get("KpiBox");
class MainDashboard extends Component {
  setup() {
    this.dashboard_state = useState({
      projects_count: 0,
      labels: [],
      counts: [],
      state_labels: [],
      state_counts: [],
      total_states: 0,
      state_data: [],

      technician_data: [],
    });
    this.filter_state = useState({
      // <-- NEW REACTIVE STATE OBJECT
      start_date: this._getDateXDaysAgo(30),
      end_date: this._today(),
      activeDiscipline: "ALL", // <-- CORRECTLY PLACED HERE
      isLoading: true, // <-- Also placed here
      activeDays: 30,
    });

    this.startDateRef = useRef("start_date");
    this.endDateRef = useRef("end_date");
    this.chartRef = useRef("chartCanvas");
    this.stateChartRef = useRef("stateChartCanvas");
    this.action = useService("action");
    this.rpc = useService("rpc"); // Ensure you have this if using jsonrpc/rpc

    this.chartInstance = null;
    this.stateChartInstance = null;

    this.timeChartType = "line";
    this.stateChartType = "bar";

    onWillStart(async () => {
      await this.fetchData(
        this.filter_state.start_date,
        this.filter_state.end_date,
        this.filter_state.activeDiscipline // <-- PASSING THE NEW PARAMETER
      );
    });

    onMounted(() => {
      this.renderTimeChart();
      this.renderStateChart();
    });
  }

  async fetchData(start_date, end_date, discipline) {
    const data_result = await jsonrpc("/dashboard/getdata", {
      start_date,
      end_date,
      discipline,
    });

    if (!data_result.error) {
      const stateLabelMap = {
        "1-allotment_pending": "Allotment Pending",
        "2-alloted": "Alloted",
        "3-pending_verification": "Pending Verification",
        "4-in_report": "In Report",
        "5-pending_approval": "Pending Approval",
      };

      this.dashboard_state.labels = data_result.labels;
      this.dashboard_state.counts = data_result.counts;
      this.dashboard_state.projects_count = data_result.total_count;
      // directly use state_data from backend
      this.dashboard_state.state_data = data_result.state_data;

      // build arrays for chart (labels + counts)
      this.dashboard_state.state_labels = data_result.state_data.map(
        (item) => item.state_label
      );
      this.dashboard_state.state_counts = data_result.state_data.map(
        (item) => item.count
      );
    }

    const tech_data_result = await jsonrpc("/lerm/overview/data", {
      start_date,
      end_date,
      discipline,
    });
    this.dashboard_state.technician_data = tech_data_result;
  }

  _onDateInputChange(ev) {
    const field = ev.target.dataset.field; // 'start_date' or 'end_date'
    this.filter_state[field] = ev.target.value;
    // console.log(`Updated ${field} to: ${ev.target.value}`); // Optional debug
  }
  // --- END NEW HANDLER ---

  async _onDateFilter(ev) {
    const days = parseInt(ev.target.dataset.days);

    // Update reactive filter state properties
    this.filter_state.start_date = this._getDateXDaysAgo(days);
    this.filter_state.end_date = this._today();
    this.filter_state.activeDays = days; // <-- UPDATED: Track the active day count

    // Fetch data using the updated values
    await this.fetchData(
      this.filter_state.start_date,
      this.filter_state.end_date,
      this.filter_state.activeDiscipline // Pass the current discipline filter
    );
    this.renderTimeChart();
    this.renderStateChart();
  }

  async _onCustomDate() {
    // Since the state is updated on every change (via _onDateInputChange),
    // we can now read the current values directly from the state.
    const start = this.filter_state.start_date;
    const end = this.filter_state.end_date;

    if (start && end) {
      // Update reactive filter state properties
      this.filter_state.activeDays = false; // Reset activeDays for custom date

      // Fetch data using the updated values (using state values which are already correct)
      await this.fetchData(
        start,
        end,
        this.filter_state.activeDiscipline // Pass the current discipline filter
      );

      // Charts are only rendered if data was successfully fetched (start and end were set)
      this.renderTimeChart();
      this.renderStateChart();
    } else {
      console.warn(
        "Custom date filter requires both start and end dates to be set."
      );
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

  switchTimeChart(type) {
    this.timeChartType = type;
    this.renderTimeChart();
  }

  switchStateChart(type) {
    this.stateChartType = type;
    this.renderStateChart();
  }
  async onKpiClick(stateName) {
    const stateLabelMap = {
      "1-allotment_pending": "Allotment Pending",
      "2-alloted": "Alloted",
      "3-pending_verification": "Pending Verification",
      "5-pending_approval": "Pending Approval",
      "4-in_report": "In Report",
    };
    const domain = [
      ["sample_received_date", ">=", this.filter_state.start_date],
      ["sample_received_date", "<=", this.filter_state.end_date],
      ["state", "=", stateName],
    ];

    this.action.doAction({
      type: "ir.actions.act_window",
      name: stateLabelMap[stateName] || "Sample Records",
      res_model: "lerm.srf.sample",
      domain: domain,
      views: [
        [false, "list"],
        [false, "form"],
      ],
    });
  }

  async _onDisciplineFilter(ev) {
    // <-- ADDED ASYNC HERE
    const discipline = ev.currentTarget.dataset.discipline;

    // Update reactive filter state property
    this.filter_state.activeDiscipline = discipline;

    // Fetch data using the updated values
    await this.fetchData(
      // <-- ADDED AWAIT HERE
      this.filter_state.start_date,
      this.filter_state.end_date,
      this.filter_state.activeDiscipline
    );
    this.renderTimeChart();
    this.renderStateChart();
  }

  // --- New Event Handler (Technician Card Click) ---

  async _onTechnicianCardClick(technicianId) {
    // Construct the action to open the 'Sample' model filtered by the technician
    const domain = [
      ["technicians", "in", [technicianId]], // Changed field from technician_id to technicians (assuming it's a many2many field based on backend logic)
      // Use the current dates from the filter_state
      ["sample_received_date", ">=", this.filter_state.start_date],
      ["sample_received_date", "<=", this.filter_state.end_date],

      // Conditionally add the discipline filter if it's not 'ALL'
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

    // The action config to open the standard Odoo tree/form view
    const action = {
      type: "ir.actions.act_window",
      // FIX: Replaced this.env._t(...) with a plain string to avoid env error
      name: "Samples for Technician",
      res_model: "lerm.srf.sample", // <--- USE YOUR CORRECT SAMPLE MODEL NAME
      views: [
        [false, "list"],
        [false, "form"],
      ],
      domain: domain,
      context: {
        // Group by state as requested
        group_by: ["state"],
      },
    };

    return this.action.doAction(action);
  }

  renderTimeChart() {
    // --- Time chart ---
    if (this.chartInstance) this.chartInstance.destroy();
    const ctx = this.chartRef.el.getContext("2d");
    this.chartInstance = new Chart(ctx, {
      type: this.timeChartType,
      data: {
        labels: this.dashboard_state.labels,
        datasets: [
          {
            label: "Samples No",
            data: this.dashboard_state.counts,
            borderWidth: 2,
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false, // 👈 allow custom height
        plugins: { legend: { display: true } },
      },
    });
  }

  renderStateChart() {
    // --- State chart ---
    if (this.stateChartInstance) this.stateChartInstance.destroy();
    const ctx2 = this.stateChartRef.el.getContext("2d");
    // Add colors only if bar
    const stateDataset = {
      label: "Samples No",
      data: this.dashboard_state.state_counts,
      borderWidth: 2,
      fill: true,
    };
    if (this.stateChartType === "bar") {
      stateDataset.backgroundColor = [
        "rgba(255, 99, 132, 0.2)",
        "rgba(255, 159, 64, 0.2)",
        "rgba(255, 205, 86, 0.2)",
        "rgba(75, 192, 192, 0.2)",
        "rgba(54, 162, 235, 0.2)",
        "rgba(153, 102, 255, 0.2)",
        "rgba(201, 203, 207, 0.2)",
      ];
      stateDataset.borderColor = [
        "rgb(255, 99, 132)",
        "rgb(255, 159, 64)",
        "rgb(255, 205, 86)",
        "rgb(75, 192, 192)",
        "rgb(54, 162, 235)",
        "rgb(153, 102, 255)",
        "rgb(201, 203, 207)",
      ];
    }
    this.stateChartInstance = new Chart(ctx2, {
      type: this.stateChartType,
      data: {
        labels: this.dashboard_state.state_labels,
        datasets: [stateDataset],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false, // 👈 allow custom height
        plugins: { legend: { display: true } },
      },
    });
  }
}

MainDashboard.template = "lerm_civil_dashboard.MainDashboard";
// MainDashboard.components = { KpiBox };
actionRegistry.add("main_dashboard", MainDashboard);
