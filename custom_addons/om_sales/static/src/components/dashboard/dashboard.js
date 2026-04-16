/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

import { DateFilter } from "../filters/date_filter";
import { KpiCard } from "../kpi_cards/kpi_card";
import { RevenueChart } from "../charts/revenue_chart";
import { OrdersChart } from "../charts/orders_chart";
import { TopProductsTable } from "../data_tables/top_products";
import { TopCouponsTable } from "../data_tables/top_coupons";

export class BackendDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            date_filter: "all",
            date_start: "",
            date_end: "",
            dashboard_data: {},
        });

        onWillStart(async () => {
            // Chart.js dùng cho các chart con
            await loadJS("https://cdn.jsdelivr.net/npm/chart.js");
            await this.fetchData();
        });
    }

    async fetchData() {
        this.state.dashboard_data = await this.orm.call(
            "sm.shopping.cart",
            "get_owl_dashboard_data",
            [this.state.date_filter, this.state.date_start, this.state.date_end]
        );
    }

    async onDateFilterChange(filter) {
        this.state.date_filter = filter;
        if (filter !== "custom") {
            await this.fetchData();
        }
    }

    async applyCustomDate() {
        if (!this.state.date_start || !this.state.date_end) {
            return;
        }
        await this.fetchData();
    }

    formatCurrency(value) {
        if (!value) {
            return "0 " + (this.state.dashboard_data.currency_symbol || "VNĐ");
        }
        return (
            value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",") +
            " " +
            (this.state.dashboard_data.currency_symbol || "VNĐ")
        );
    }
}

BackendDashboard.template = "om_sales.BackendDashboard";
BackendDashboard.components = {
    DateFilter,
    KpiCard,
    RevenueChart,
    OrdersChart,
    TopProductsTable,
    TopCouponsTable,
};

registry.category("actions").add("om_sales.backend_dashboard", BackendDashboard);

