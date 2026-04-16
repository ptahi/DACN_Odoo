/** @odoo-module **/

import { Component, onMounted, useRef, useEffect } from "@odoo/owl";

export class RevenueChart extends Component {
    setup() {
        this.canvasRef = useRef("revenueChart");
        this.chart = null;

        onMounted(() => this.renderChart());

        useEffect(
            () => this.renderChart(),
            () => [this.props.labels, this.props.data]
        );
    }

    renderChart() {
        if (!this.canvasRef.el || !this.props.labels) return;

        if (this.chart) {
            this.chart.destroy();
        }

        const labels = this.props.labels || [];
        const data = this.props.data || [];

        const ctx = this.canvasRef.el.getContext("2d");
        this.chart = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [{
                    label: "Doanh thu (VNĐ)",
                    data: data,
                    borderColor: "#0d6efd",
                    backgroundColor: "rgba(13, 110, 253, 0.08)",
                    fill: true,
                    tension: 0.4,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false } },
                    y: {
                        grid: { color: "rgba(0, 0, 0, 0.03)" },
                        ticks: { precision: 0 },
                    },
                },
            },
        });
    }
}

RevenueChart.template = "om_sales.RevenueChart";

