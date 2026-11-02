// Analytics page: auto-submit the period filter and draw four Chart.js charts
// from the JSON embedded in the page by the server.

(function () {
    "use strict";

    // Period dropdown reloads the page as soon as it changes
    var periodForm = document.getElementById("period-form");
    var periodSelect = document.getElementById("period");
    if (periodForm && periodSelect) {
        periodSelect.addEventListener("change", function () {
            periodForm.submit();
        });
    }

    var dataElement = document.getElementById("analytics-data");
    if (!dataElement || typeof Chart === "undefined") {
        return;
    }

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

    // Draw a chart, or show the empty message when there is nothing to plot
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

    function renderDiseaseSickDead(data) {
        drawChart("chartDiseaseSickDead", {
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
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
                plugins: { legend: { position: "bottom" } }
            }
        }, sum(data.sick) + sum(data.dead) > 0);
    }

    function renderDeadShare(data) {
        drawChart("chartDeadShare", {
            type: "doughnut",
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: data.labels.map(colorFor),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "55%",
                plugins: {
                    legend: { position: "bottom" },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                var total = sum(context.dataset.data);
                                var percent = total ? (context.parsed * 100 / total).toFixed(1) : 0;
                                return context.label + ": " + context.parsed + " dead (" + percent + "%)";
                            }
                        }
                    }
                }
            }
        }, sum(data.values) > 0);
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

    function renderMonthly(data) {
        drawChart("chartMonthly", {
            type: "line",
            data: {
                labels: data.labels,
                datasets: [{
                    label: "Disease cases",
                    data: data.disease_cases,
                    borderColor: DISEASE_COLORS.Salmonella,
                    backgroundColor: "rgba(198, 40, 40, 0.15)",
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
                plugins: { legend: { display: false } }
            }
        }, sum(data.disease_cases) > 0);
    }

    try {
        var data = JSON.parse(dataElement.textContent);
        renderDiseaseSickDead(data.disease);
        renderDeadShare(data.dead_share);
        renderFarmDead(data.farms);
        renderMonthly(data.monthly);
    } catch (error) {
        document.getElementById("analytics-error").classList.remove("d-none");
    }
})();