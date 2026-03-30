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
      labs: [],
      companies: [],
      aging_data: {},
    });
    this.filter_state = useState({
      // <-- NEW REACTIVE STATE OBJECT
      start_date: this._getDateXDaysAgo(30),
      end_date: this._today(),
      activeDiscipline: "ALL", // <-- CORRECTLY PLACED HERE
      activeLab: "ALL",
      activeCompany: "ALL",
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
      const filterOptions = await jsonrpc("/dashboard/get_filter_options", {});
      this.dashboard_state.labs = filterOptions.labs || [];
      this.dashboard_state.companies = filterOptions.companies || [];

      await this.fetchData();
    });

    onMounted(() => {
      this.renderTimeChart();
      this.renderStateChart();
    });
  }

  async fetchData() {
    const { start_date, end_date, activeDiscipline, activeLab, activeCompany } = this.filter_state;
    
    const data_result = await jsonrpc("/dashboard/getdata", {
      start_date,
      end_date,
      discipline: activeDiscipline,
      lab_id: activeLab,
      company_id: activeCompany,
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
        (item) => item.state_label,
      );
      this.dashboard_state.state_counts = data_result.state_data.map(
        (item) => item.count,
      );
      this.dashboard_state.aging_data = data_result.aging_data || {};
    }

    const tech_data_result = await jsonrpc("/lerm/overview/data", {
      start_date,
      end_date,
      discipline: activeDiscipline,
      lab_id: activeLab,
      company_id: activeCompany,
    });
    this.dashboard_state.technician_data = tech_data_result;
  }

  _onDateInputChange(ev) {
    const field = ev.target.dataset.field; // 'start_date' or 'end_date'
    this.filter_state[field] = ev.target.value;
    // console.log(`Updated ${field} to: ${ev.target.value}`); // Optional debug
  }

  async _onLabFilter(ev) {
    const labId = ev.target.value;
    this.filter_state.activeLab = labId;
    await this.fetchData();
    this.renderTimeChart();
    this.renderStateChart();
  }

  async _onCompanyFilter(ev) {
    const companyId = ev.target.value;
    this.filter_state.activeCompany = companyId;

    // Reset Lab filter if the currently active lab isn't in the new company's list
    if (companyId !== "ALL") {
      const labs = this.dashboard_state.labs.filter(
        (l) => l.company_id === parseInt(companyId),
      );
      if (!labs.some((l) => l.id == this.filter_state.activeLab)) {
        this.filter_state.activeLab = "ALL";
      }
    }

    await this.fetchData();
    this.renderTimeChart();
    this.renderStateChart();
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
  get styleMap() {
    return {
      "1-allotment_pending": { icon: "fa-hourglass-o", color: "#fd7e14", label: "Assignment Pending" },
      "7-partially-alloted": { icon: "fa-adjust", color: "#8b5cf6", label: "Partially Alloted" },
      "2-alloted": { icon: "fa-play-circle", color: "#0066ff", label: "Alloted" },
      "7-calculated": { icon: "fa-calculator", color: "#6366f1", label: "In-Test" },
      "3-pending_verification": { icon: "fa-hourglass-half", color: "#d97706", label: "Pending Verification" },
      "5-pending_approval": { icon: "fa-clock-o", color: "#dc2626", label: "Pending Approval" },
      "4-in_report": { icon: "fa-file-text-o", color: "#16a34a", label: "In Report" },
      "6-cancelled": { icon: "fa-times-circle", color: "#9ca3af", label: "Cancelled" },
    };
  }

  get kpiData() {
    const styleMap = this.styleMap;


    const data = [{
      state: 'total',
      state_label: 'Total Samples',
      count: this.dashboard_state.projects_count,
      icon: "fa-bar-chart",
      color: "#007bff",
      isTotal: true
    }];

    this.dashboard_state.state_data.forEach(item => {
      const style = styleMap[item.state] || { icon: "fa-question-circle", color: "#6c757d", label: item.state_label };
      data.push({
        ...item,
        icon: style.icon,
        color: style.color,
        state_label: style.label || item.state_label
      });
    });

    return data;
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

  async _onDateFilter(ev) {
    const days = parseInt(ev.target.dataset.days);

    // Update reactive filter state properties
    this.filter_state.start_date = this._getDateXDaysAgo(days);
    this.filter_state.end_date = this._today();
    this.filter_state.activeDays = days; // <-- UPDATED: Track the active day count

    // Fetch data using the updated values
    await this.fetchData();
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
      await this.fetchData();

      // Charts are only rendered if data was successfully fetched (start and end were set)
      this.renderTimeChart();
      this.renderStateChart();
    } else {
      console.warn(
        "Custom date filter requires both start and end dates to be set.",
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
  async onAgingClick(bucketKey, stateKey = null, techId = null) {
    const today = new Date();
    // Handle 60+ specifically or parse min-max
    let minDays, maxDays;
    if (bucketKey === "60+") {
        minDays = 61;
        maxDays = null;
    } else {
        [minDays, maxDays] = bucketKey.split("-").map(Number);
    }
    
    // Create new date objects for boundaries
    const dMax = new Date(today);
    dMax.setDate(today.getDate() - minDays);
    dMax.setHours(23, 59, 59, 999);
    
    let dMin = null;
    if (maxDays !== null) {
        dMin = new Date(today);
        dMin.setDate(today.getDate() - maxDays);
        dMin.setHours(0, 0, 0, 0);
    }

    const domain = [
        ["state", "in", ["2-alloted", "7-calculated", "3-pending_verification", "5-pending_approval"]],
        ["eln_id", "!=", false],
        ["eln_id.create_date", "<=", dMax.toISOString()],
    ];

    if (dMin) {
        domain.push(["eln_id.create_date", ">=", dMin.toISOString()]);
    }

    if (stateKey) {
        domain.push(["state", "=", stateKey]);
    }

    if (techId) {
        domain.push("|", ["technicians", "=", techId], ["eln_id.technician", "=", techId]);
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

    this.action.doAction({
      type: "ir.actions.act_window",
      name: `Samples Aging: ${bucketKey} Days`,
      res_model: "lerm.srf.sample",
      domain: domain,
      views: [
        [false, "list"],
        [false, "form"],
      ],
      context: {
        group_by: ["state"],
      }
    });
  }

  async onKpiClick(stateName) {
    const stateLabelMap = {
      "1-allotment_pending": "Assignment Pending",
      "7-partially-alloted": "Partially Alloted",
      "2-alloted": "Alloted",
      "7-calculated": "In-Test",
      "3-pending_verification": "Pending Verification",
      "5-pending_approval": "Pending Approval",
      "4-in_report": "In Report",
      "6-cancelled": "Cancelled",
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
    await this.fetchData();
    this.renderTimeChart();
    this.renderStateChart();
  }

  // --- New Event Handler (Technician Card Click) ---

  async _onTechnicianCardClick(technicianId) {
    // Construct the action to open the 'Sample' model filtered by the technician
    const domain = [
      "|",
      ["technicians", "in", [technicianId]],
      "|",
      ["eln_id.technician", "=", technicianId],
      ["eln_id.technician_ids", "in", [technicianId]],
      // Use the current dates from the filter_state
      ["sample_received_date", ">=", this.filter_state.start_date],
      ["sample_received_date", "<=", this.filter_state.end_date],

      ...(this.filter_state.activeDiscipline !== "ALL"
        ? [
            [
              "discipline_id.discipline",
              "=",
              this.filter_state.activeDiscipline,
            ],
          ]
        : []),
      ...(this.filter_state.activeLab !== "ALL"
        ? [["lab_location", "=", parseInt(this.filter_state.activeLab)]]
        : []),
      ...(this.filter_state.activeCompany !== "ALL"
        ? [
            [
              "lab_location.company_id",
              "=",
              parseInt(this.filter_state.activeCompany),
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
