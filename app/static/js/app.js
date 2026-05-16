document.addEventListener("DOMContentLoaded", () => {
    const charts = {
        caseTrend: {
            type: "line",
            data: {
                labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                datasets: [{
                    label: "Cases",
                    data: [0, 0, 0, 0, 0, 0],
                    borderColor: "#2563eb",
                    backgroundColor: "rgba(37, 99, 235, 0.12)",
                    fill: true,
                    tension: 0.35
                }]
            }
        },
        riskDistribution: {
            type: "doughnut",
            data: {
                labels: ["Low", "Moderate", "High"],
                datasets: [{
                    data: [1, 1, 1],
                    backgroundColor: ["#10b981", "#f59e0b", "#ef4444"],
                    borderWidth: 0
                }]
            }
        },
        registryCompleteness: {
            type: "bar",
            data: {
                labels: ["Demographics", "Incident", "History", "Disposition"],
                datasets: [{
                    label: "Completeness",
                    data: [0, 0, 0, 0],
                    backgroundColor: "#2563eb",
                    borderRadius: 12
                }]
            }
        }
    };

    document.querySelectorAll("canvas[data-chart]").forEach((canvas) => {
        const config = charts[canvas.dataset.chart];
        if (!config || !window.Chart) return;
        new Chart(canvas, {
            ...config,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            boxWidth: 12,
                            color: getComputedStyle(document.documentElement).getPropertyValue("--chart-label-color").trim() || "#475569"
                        }
                    }
                },
                scales: config.type === "doughnut" ? undefined : {
                    x: { grid: { display: false }, ticks: { color: "#64748b" } },
                    y: { beginAtZero: true, grid: { color: "rgba(148, 163, 184, 0.25)" }, ticks: { color: "#64748b" } }
                }
            }
        });
    });
});
