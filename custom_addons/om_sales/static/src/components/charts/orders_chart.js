/** @odoo-module **/

import { Component, onMounted, useRef, useEffect } from "@odoo/owl";

export class OrdersChart extends Component {
    setup() {
        this.canvasRef = useRef("ordersChart");
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
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "Đơn hàng",
                    data,
                    backgroundColor: "rgba(17, 17, 201, 0.35)",
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
                        ticks: { precision: 0, stepSize: 1 },
                    },
                },
            },
        });
    }
}

OrdersChart.template = "om_sales.OrdersChart";

