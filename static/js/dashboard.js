// Dashboard charts: fetches JSON from the server and draws six Chart.js charts

(function () {
    "use strict";

    var root = document.getElementById("dashboard-root");
    if (!root || typeof Chart === "undefined") {
        return;
    }

    var DATA_URL = root.dataset.url;

    // One fixed colour per disease so charts stay consistent
    var DISEASE_COLORS = {
        Healthy: "#2e7d32",
        Coccidiosis: "#f57c00",
        Salmonella: "#c62828",
        Newcastle: "#6a1b9a"
    };
    var FALLBACK_COLOR = "#607d8b";
    var SICK_COLOR = "#f9a825";
    var DEAD_COLOR = "#b71c1c";

    var charts = {};

    Chart.defaults.font.family = '"Segoe UI", system-ui, sans-serif';
    Chart.defaults.plugins.legend.labels.usePointStyle = true;

    function colorFor(label) {
        return DISEASE_COLORS[label] || FALLBACK_COLOR;
    }

    function sum(values) {
        return values.reduce(function (total, value) {
            return total + value;
        }, 0);
    }

    // Draw a chart, or show the "No data yet" message when all values are zero
    function drawChart(canvasId, config, hasData) {
        var canvas = document.getElementById(canvasId);
        if (!canvas) {
            return;
        }
        var emptyBox = canvas.parentElement.querySelector(".chart-empty");

        if (charts[canvasId]) {
            charts[canvasId].destroy();
            delete charts[canvasId];
        }

        if (!hasData) {
            canvas.classList.add("d-none");
            emptyBox.classList.remove("d-none");
            return;
        }

        canvas.classList.remove("d-none");
        emptyBox.classList.add("d-none");
        charts[canvasId] = new Chart(canvas, config);
    }

    // Shared options for charts that have axes
    function axisOptions(extra) {
        var options = {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, ticks: { precision: 0 } }
            },
            plugins: { legend: { display: false } }
        };
        return Object.assign(options, extra || {});
    }

    function renderDiseaseCount(data) {
        drawChart("chartDiseaseCount", {
            type: "bar",
            data: {
                labels: data.labels,
                datasets: [{
                    label: "Scans",
                    data: data.values,
                    backgroundColor: data.labels.map(colorFor),
                    borderRadius: 6
                }]
            },
            options: axisOptions()
        }, sum(data.values) > 0);
    }

    function renderHealthyDiseased(data) {
        drawChart("chartHealthyDiseased", {
            type: "doughnut",
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: [DISEASE_COLORS.Healthy, DISEASE_COLORS.Salmonella],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "60%",
                plugins: {
                    legend: { position: "bottom" },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                var total = sum(context.dataset.data);
                                var percent = total ? (context.parsed * 100 / total).toFixed(1) : 0;
                                return context.label + ": " + context.parsed + " (" + percent + "%)";
                            }
                        }
                    }
                }
            }
        }, sum(data.values) > 0);
    }

    function renderMonthlyTrend(data) {
        drawChart("chartMonthlyTrend", {
            type: "line",
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: "Disease cases",
                        data: data.disease_cases,
                        borderColor: DISEASE_COLORS.Salmonella,
                        backgroundColor: "rgba(198, 40, 40, 0.15)",
                        fill: true,
                        tension: 0.3,
                        pointRadius: 4
                    },
                    {
                        label: "Total scans",
                        data: data.total_scans,
                        borderColor: "#1565c0",
                        backgroundColor: "rgba(21, 101, 192, 0.1)",
                        borderDash: [6, 4],
                        tension: 0.3,
                        pointRadius: 3
                    }
                ]
            },
            options: axisOptions({ plugins: { legend: { position: "bottom" } } })
        }, sum(data.total_scans) > 0);
    }

    function renderBatchComparison(data) {
        drawChart("chartBatchComparison", {
            type: "bar",
            data: {
                labels: data.labels,
                datasets: [{
                    label: "Disease cases",
                    data: data.values,
                    backgroundColor: "#ef6c00",
                    borderRadius: 6
                }]
            },
            options: axisOptions()
        }, data.labels.length > 0);
    }

    function renderSickDead(data) {
        drawChart("chartSickDead", {
            type: "bar",
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: "Sick birds",
                        data: data.sick,
                        backgroundColor: SICK_COLOR,
                        borderRadius: 4
                    },
                    {
                        label: "Dead birds",
                        data: data.dead,
                        backgroundColor: DEAD_COLOR,
                        borderRadius: 4
                    }
                ]
            },
            options: axisOptions({ plugins: { legend: { position: "bottom" } } })
        }, sum(data.sick) + sum(data.dead) > 0);
    }

    function renderFarmDead(data) {
        drawChart("chartFarmDead", {
            type: "bar",
            data: {
                labels: data.labels,
                datasets: [{
                    label: "Dead birds",
                    data: data.values,
                    backgroundColor: DEAD_COLOR,
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                scales: { x: { beginAtZero: true, ticks: { precision: 0 } } },
                plugins: { legend: { display: false } }
            }
        }, sum(data.values) > 0);
    }

    function showError() {
        document.getElementById("dashboard-error").classList.remove("d-none");
    }

    function loadDashboard() {
        fetch(DATA_URL, {
            credentials: "same-origin",
            headers: { Accept: "application/json" }
        })
            .then(function (response) {
                // An expired session redirects to the login page
                if (response.redirected) {
                    window.location.href = response.url;
                    return null;
                }
                if (!response.ok) {
                    throw new Error("HTTP " + response.status);
                }
                return response.json();
            })
            .then(function (data) {
                if (!data) {
                    return;
                }
                renderDiseaseCount(data.disease_counts);
                renderHealthyDiseased(data.healthy_vs_diseased);
                renderMonthlyTrend(data.monthly_trend);
                renderBatchComparison(data.batch_comparison);
                renderSickDead(data.disease_sick_dead);
                renderFarmDead(data.farm_dead_birds);
            })
            .catch(showError);
    }

    loadDashboard();
})();