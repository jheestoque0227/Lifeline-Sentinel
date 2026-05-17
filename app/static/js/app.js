window.initRegistrySelect2 = function initRegistrySelect2(root) {
    if (window.jQuery && window.jQuery.fn && window.jQuery.fn.select2) {
        const scope = root || document;
        window.jQuery(scope).find("select.js-registry-select, select.js-example-basic-multiple").addBack("select.js-registry-select, select.js-example-basic-multiple").each(function () {
            const $field = window.jQuery(this);
            if ($field.hasClass("select2-hidden-accessible")) {
                $field.select2("destroy");
            }
            const $dropdownParent = $field.parent();
            $dropdownParent.addClass("select2-field-parent");

            $field.select2({
                width: "100%",
                dropdownAutoWidth: false,
                dropdownParent: $dropdownParent,
                placeholder: $field.data("placeholder") || "Select options",
                closeOnSelect: !$field.prop("multiple"),
                allowClear: true
            });
        });
    }
};

window.initConditionalOtherFields = function initConditionalOtherFields(root) {
    const scope = root || document;
    scope.querySelectorAll("[data-other-trigger]").forEach((trigger) => {
        const targetId = trigger.dataset.otherTrigger;
        const target = scope.querySelector(`#${CSS.escape(targetId)}`) || document.getElementById(targetId);
        if (!target) return;

        const sync = () => {
            const isOther = (trigger.value || "").trim().toLowerCase() === "other";
            target.disabled = !isOther;
            target.required = isOther;
            document.querySelectorAll(`[data-required-marker-for="${target.id}"]`).forEach((marker) => {
                marker.classList.toggle("hidden", !isOther);
            });
            if (!isOther) {
                target.value = "";
            }
        };

        trigger.removeEventListener("change", trigger._conditionalOtherSync);
        trigger._conditionalOtherSync = sync;
        trigger.addEventListener("change", sync);
        sync();
    });
};

window.initSubstanceTypeFields = function initSubstanceTypeFields(root) {
    const scope = root || document;
    scope.querySelectorAll("[data-substance-trigger]").forEach((trigger) => {
        const targetId = trigger.dataset.substanceTrigger;
        const target = scope.querySelector(`#${CSS.escape(targetId)}`) || document.getElementById(targetId);
        if (!target) return;

        const sync = () => {
            target.disabled = !trigger.checked;
            target.required = trigger.checked;
            document.querySelectorAll(`[data-required-marker-for="${target.id}"]`).forEach((marker) => {
                marker.classList.toggle("hidden", !trigger.checked);
            });
            if (!trigger.checked) {
                target.value = "";
            }
        };

        trigger.removeEventListener("change", trigger._substanceTypeSync);
        trigger._substanceTypeSync = sync;
        trigger.addEventListener("change", sync);
        sync();
    });
};

window.initDataTables = function initDataTables(root) {
    if (!window.jQuery || !window.jQuery.fn || !window.jQuery.fn.DataTable) return;
    const scope = root || document;
    window.jQuery(scope).find("table.js-data-table").addBack("table.js-data-table").each(function () {
        const $table = window.jQuery(this);
        if (window.jQuery.fn.DataTable.isDataTable(this)) return;
        const dataTable = $table.DataTable({
            autoWidth: false,
            pageLength: 10,
            lengthMenu: [10, 25, 50, 100],
            order: [],
            responsive: false,
            layout: {
                topStart: null,
                topEnd: "search",
                bottomStart: ["pageLength", "info"],
                bottomEnd: "paging"
            },
            language: {
                search: "",
                searchPlaceholder: "Search",
                lengthMenu: "_MENU_",
                info: "Showing _START_ to _END_ of _TOTAL_ entries",
                emptyTable: "No data available"
            },
            columnDefs: [
                { orderable: false, targets: "no-sort" }
            ]
        });
        const $container = window.jQuery(dataTable.table().container());
        $container.find(".dt-search label").each(function () {
            const $label = window.jQuery(this);
            const $input = $label.find("input").detach();
            $label.replaceWith($input);
        });
    });
};

window.refreshDataTables = function refreshDataTables() {
    if (!window.jQuery || !window.jQuery.fn || !window.jQuery.fn.DataTable) return;
    window.jQuery("table.js-data-table").each(function () {
        if (!window.jQuery.fn.DataTable.isDataTable(this)) return;
        const table = window.jQuery(this).DataTable();
        table.columns.adjust();
        if (table.responsive && typeof table.responsive.recalc === "function") {
            table.responsive.recalc();
        }
    });
};

window.scheduleDataTableRefresh = function scheduleDataTableRefresh() {
    [0, 120, 320].forEach((delay) => {
        window.setTimeout(window.refreshDataTables, delay);
    });
};

document.addEventListener("DOMContentLoaded", () => {
    window.initRegistrySelect2(document);
    window.initConditionalOtherFields(document);
    window.initSubstanceTypeFields(document);
    window.initDataTables(document);

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

    document.querySelectorAll("[aria-label='Collapse sidebar']").forEach((button) => {
        button.addEventListener("click", window.scheduleDataTableRefresh);
    });

    window.addEventListener("resize", () => {
        window.clearTimeout(window._dataTableResizeTimer);
        window._dataTableResizeTimer = window.setTimeout(window.refreshDataTables, 120);
    });

    window.scheduleDataTableRefresh();
});
