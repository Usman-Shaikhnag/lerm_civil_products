/** @odoo-module **/

import { Component, useRef, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";

export class ChartRenderer extends Component {
    setup() {
        this.chartRef = useRef("chart");

        onWillStart(async () => {
            if (typeof Chart === "undefined") {
                await new Promise((resolve, reject) => {
                    const script = document.createElement("script");
                    script.src = "'https://cdn.jsdelivr.net/npm/chart.js',";
                    script.onload = resolve;
                    script.onerror = reject;
                    document.head.appendChild(script);
                });
            }
        });

        onMounted(() => this.renderChart());
        onWillUnmount(() => {
            if (this.chart) {
                this.chart.destroy();
            }
        });
    }

    renderChart() {
        if (!this.chartRef.el) return;

        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new Chart(this.chartRef.el, {
            type: this.props.type || "bar",
            data: this.props.data,
            options: {
                responsive: true,
                plugins: {
                    legend: { position: "bottom" },
                    title: {
                        display: true,
                        text: this.props.title || "",
                        position: "bottom",
                    },
                },
                scales: {
                    y: { beginAtZero: true, ticks: { stepSize: 1 } },
                },
            },
        });
    }
}

ChartRenderer.template = "lerm_civil_dashboard.ChartRenderer";
