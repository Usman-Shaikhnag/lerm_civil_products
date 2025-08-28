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
    });

    this.startDateRef = useRef("start_date");
    this.endDateRef = useRef("end_date");
    this.chartRef = useRef("chartCanvas");
    this.stateChartRef = useRef("stateChartCanvas");
    this.action = useService("action");

    this.chartInstance = null;
    this.stateChartInstance = null;

    this.timeChartType = "line";
    this.stateChartType = "bar";

    this.start_date = this._getDateXDaysAgo(30);
    this.end_date = this._today();

    onWillStart(async () => {
      await this.fetchData(this.start_date, this.end_date);
    });

    onMounted(() => {
      this.renderTimeChart();
      this.renderStateChart();
    });
  }

  async fetchData(start_date, end_date) {
    const data_result = await jsonrpc("/dashboard/getdata", {
      start_date,
      end_date,
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

  async _onDateFilter(ev) {
    const days = parseInt(ev.target.dataset.days);
    this.start_date = this._getDateXDaysAgo(days);
    this.end_date = this._today();
    await this.fetchData(this.start_date, this.end_date);
    this.renderTimeChart();
    this.renderStateChart();
  }

  async _onCustomDate() {
    const start = this.startDateRef.el.value;
    const end = this.endDateRef.el.value;
    if (start && end) {
      this.start_date = start;
      this.end_date = end;
      await this.fetchData(start, end);
    }
    this.renderTimeChart();
    this.renderStateChart();
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
      "4-in_report": "In Report",
      "5-pending_approval": "Pending Approval",
    };
    const domain = [
      ["sample_received_date", ">=", this.start_date],
      ["sample_received_date", "<=", this.end_date],
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
}

MainDashboard.template = "lerm_civil_dashboard.MainDashboard";
MainDashboard.components = { KpiBox };
actionRegistry.add("main_dashboard", MainDashboard);
