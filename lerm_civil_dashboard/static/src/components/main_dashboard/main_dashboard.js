/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, useState, useRef, onMounted } from "@odoo/owl";
import { jsonrpc } from "@web/core/network/rpc_service";
// import { ChartRenderer } from "@lerm_civil_dashboard/components/chart_renderer/chart_renderer";

const actionRegistry = registry.category("actions");

class MainDashboard extends Component {
  setup() {
    this.project_state = useState({
      projects_count: 0,
      labels: [],
      counts: [],
    });

    this.startDateRef = useRef("start_date");
    this.endDateRef = useRef("end_date");
    this.chartRef = useRef("chartCanvas");
    this.chartInstance = null;
    this.currentChartType = "line"; // default

    this.start_date = this._getDateXDaysAgo(30);
    this.end_date = this._today();

    onWillStart(async () => {
      await this.fetchData(this.start_date, this.end_date);
    });

    onMounted(() => {
      this.renderChart(); // render only after canvas exists
    });
  }

  async onWillStart() {
    await this.fetchData(this.start_date, this.end_date);
  }

  async fetchData(start_date, end_date) {
    const data_result = await jsonrpc("/dashboard/getdata", {
      start_date,
      end_date,
    });

    if (!data_result.error) {
      this.project_state.labels = data_result.labels;
      this.project_state.counts = data_result.counts;
      this.project_state.projects_count = data_result.total_count;

      //   if (this.chartInstance) {
      //     this.chartInstance.destroy();
      //   }
      //   if (this.chartRef.el) {
      //     this.renderChart(); // safe now, because canvas exists
      //   }
    }
  }

  renderChart() {
    if (this.chartInstance) {
      this.chartInstance.destroy();
    }

    const ctx = this.chartRef.el.getContext("2d");
    this.chartInstance = new Chart(ctx, {
      // <-- Chart, not ChartRenderer
      type: this.currentChartType,
      data: {
        labels: this.project_state.labels,
        datasets: [
          {
            label: "Samples",
            data: this.project_state.counts,
            borderWidth: 2,
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: true },
        },
      },
    });
  }

  async _onDateFilter(ev) {
    const days = parseInt(ev.target.dataset.days);
    this.start_date = this._getDateXDaysAgo(days);
    this.end_date = this._today();
    await this.fetchData(this.start_date, this.end_date);
    this.renderChart();
  }

  async _onCustomDate() {
    const start = this.startDateRef.el.value;
    const end = this.endDateRef.el.value;
    if (start && end) {
      this.start_date = start;
      this.end_date = end;
      await this.fetchData(start, end);
    }
    this.renderChart();
  }

  _today() {
    return new Date().toISOString().split("T")[0];
  }

  _getDateXDaysAgo(days) {
    const d = new Date();
    d.setDate(d.getDate() - days);
    return d.toISOString().split("T")[0];
  }

  switchChart(type) {
    this.currentChartType = type;
    this.renderChart();
  }
}

MainDashboard.template = "lerm_civil_dashboard.MainDashboard";
actionRegistry.add("main_dashboard", MainDashboard);
