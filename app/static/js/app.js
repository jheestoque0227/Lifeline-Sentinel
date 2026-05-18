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

            const select2Options = {
                width: "100%",
                dropdownAutoWidth: false,
                dropdownParent: $dropdownParent,
                placeholder: $field.data("placeholder") || "Select options",
                closeOnSelect: !$field.prop("multiple"),
                allowClear: true
            };

            if ($field.data("ajaxUrl")) {
                select2Options.ajax = {
                    url: $field.data("ajaxUrl"),
                    dataType: "json",
                    delay: 250,
                    data: function (params) {
                        return {
                            q: params.term || ""
                        };
                    },
                    processResults: function (data) {
                        return {
                            results: data.results || []
                        };
                    },
                    cache: true
                };
            }

            $field.select2(select2Options);
        });
    }
};

window.initConditionalOtherFields = function initConditionalOtherFields(root) {
    const scope = root || document;
    const isOtherValue = (value) => ["other", "others"].includes((value || "").trim().toLowerCase());

    scope.querySelectorAll("[data-other-trigger]").forEach((trigger) => {
        const targetId = trigger.dataset.otherTrigger;
        const target = scope.querySelector(`#${CSS.escape(targetId)}`) || document.getElementById(targetId);
        if (!target) return;

        const sync = () => {
            const isOther = isOtherValue(trigger.value);
            target.disabled = !isOther;
            target.required = isOther;
            target.setAttribute("aria-disabled", isOther ? "false" : "true");
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
        if (window.jQuery) {
            window.jQuery(trigger)
                .off(".conditionalOther")
                .on("change.conditionalOther select2:select.conditionalOther select2:clear.conditionalOther", sync);
        }
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

window.initPatientSearchModal = function initPatientSearchModal(root) {
    if (!window.jQuery || !window.jQuery.fn || !window.jQuery.fn.DataTable) return;

    const scope = root || document;
    const modal = scope.querySelector("[data-patient-search-modal]") || document.querySelector("[data-patient-search-modal]");
    const patientIdentifier = scope.querySelector("[data-patient-search-trigger]") || document.querySelector("[data-patient-search-trigger]");
    if (!modal || !patientIdentifier || modal.dataset.patientSearchBound === "true") return;

    const searchUrl = modal.dataset.patientSearchUrl;
    const searchInput = modal.querySelector("[data-patient-search-input]");
    const searchButton = modal.querySelector("[data-patient-search-button]");
    const closeButtons = modal.querySelectorAll("[data-patient-search-close]");
    const tableElement = modal.querySelector("table.js-patient-search-table");
    if (!searchUrl || !searchInput || !searchButton || !tableElement) return;

    modal.dataset.patientSearchBound = "true";
    const dataTableRender = window.jQuery.fn.dataTable.render;
    const textRenderer = dataTableRender && dataTableRender.text ? dataTableRender.text() : undefined;

    const patientTable = window.jQuery(tableElement).DataTable({
        autoWidth: false,
        data: [],
        pageLength: 10,
        lengthChange: false,
        searching: false,
        ordering: false,
        responsive: false,
        layout: {
            topStart: null,
            topEnd: null,
            bottomStart: "info",
            bottomEnd: "paging"
        },
        language: {
            info: "Showing _START_ to _END_ of _TOTAL_ entries",
            emptyTable: "No data available"
        },
        columns: [
            { data: "hospital_number", defaultContent: "", render: textRenderer },
            { data: "patient_name", defaultContent: "", render: textRenderer }
        ]
    });

    const openModal = () => {
        if (!modal.classList.contains("hidden")) return;
        modal.classList.remove("hidden");
        modal.classList.add("flex");
        modal.setAttribute("aria-hidden", "false");
        searchInput.value = patientIdentifier.value || "";
        window.setTimeout(() => {
            searchInput.focus();
            patientTable.columns.adjust();
        }, 0);
    };

    const closeModal = () => {
        modal.classList.add("hidden");
        modal.classList.remove("flex");
        modal.setAttribute("aria-hidden", "true");
    };

    const normalizeRows = (payload) => {
        const rows = Array.isArray(payload) ? payload : payload.results || payload.patients || [];
        return rows.map((row) => ({
            hospital_number: row.hospital_number || row.hospitalNumber || row.hpercode || "",
            patient_name: row.patient_name || row.patientName || row.full_name || row.name || ""
        }));
    };

    const runSearch = () => {
        const query = searchInput.value.trim();
        if (!query) {
            patientTable.clear().draw();
            return;
        }

        searchButton.disabled = true;
        fetch(`${searchUrl}?q=${encodeURIComponent(query)}`, {
            headers: {
                Accept: "application/json"
            }
        })
            .then((response) => {
                if (!response.ok) throw new Error("Patient search failed.");
                return response.json();
            })
            .then((payload) => {
                patientTable.clear().rows.add(normalizeRows(payload)).draw();
                patientTable.columns.adjust();
            })
            .catch(() => {
                patientTable.clear().draw();
            })
            .finally(() => {
                searchButton.disabled = false;
            });
    };

    patientIdentifier.addEventListener("click", openModal);
    patientIdentifier.addEventListener("focus", openModal);
    searchButton.addEventListener("click", runSearch);

    closeButtons.forEach((button) => {
        button.addEventListener("click", closeModal);
    });

    modal.addEventListener("click", (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !modal.classList.contains("hidden")) {
            closeModal();
        }
    });

    window.jQuery(tableElement).on("click", "tbody tr", function () {
        const row = patientTable.row(this).data();
        if (!row || !row.hospital_number) return;
        patientIdentifier.value = row.hospital_number;
        patientIdentifier.dispatchEvent(new Event("input", { bubbles: true }));
        patientIdentifier.dispatchEvent(new Event("change", { bubbles: true }));
        closeModal();
    });
};

document.addEventListener("DOMContentLoaded", () => {
    window.initRegistrySelect2(document);
    window.initConditionalOtherFields(document);
    window.initSubstanceTypeFields(document);
    window.initDataTables(document);
    window.initPatientSearchModal(document);

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
