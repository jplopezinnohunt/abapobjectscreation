sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/ui/model/Filter",
    "sap/ui/model/FilterOperator",
    "sap/ui/model/Sorter",
    "sap/m/MessageToast",
    "sap/m/MessageBox",
    "sap/ui/export/Spreadsheet",
    "sap/ui/core/format/DateFormat",
    "sap/m/Dialog",
    "sap/m/Button",
    "sap/m/CheckBox",
    "sap/m/VBox",
    "sap/ui/core/UIComponent",
    "sap/ui/core/Item",
    "sap/ui/core/CustomData"
], function (
    Controller, Filter, FilterOperator, Sorter,
    MessageToast, MessageBox, Spreadsheet, DateFormat,
    Dialog, Button, CheckBox, VBox, UIComponent, Item, CustomData
) {
    "use strict";

    return Controller.extend("com.hr.unesco.yhrappoffboarding.controller.Main", {

        onInit: function () {
            this._bFullScreen = false;
            this._sSearchQuery = "";
            this._oColumnConfig = {};
            this._sSortField = "CreatorPernr";

            var oModel = this.getOwnerComponent().getModel("offboardingModel");
            if (!oModel) {
                MessageBox.error("ModÃ¨le 'offboardingModel' introuvable. VÃ©rifie Component.js");
                this._bODataV2 = false;
                return;
            }

            this._bODataV2 = !!(oModel.isA && oModel.isA("sap.ui.model.odata.v2.ODataModel"));

            if (oModel.metadataLoaded) {
                oModel.metadataLoaded().then(function () {
                    ["categoryCombo", "contractTypeCombo"].forEach(function (id) {
                        var oCB = this.byId(id);
                        if (!oCB) return;
                        var aItems = oCB.getItems ? oCB.getItems() : [];
                        if (!aItems.length || (aItems[0] && aItems[0].getKey && aItems[0].getKey() !== "")) {
                            var sText = id === "contractTypeCombo" ? "All Contract Types" : "All Categories";
                            oCB.insertItem(new Item({
                                key: "",
                                text: sText
                            }), 0);
                        }
                    }.bind(this));
                }.bind(this)).catch(function (err) {
                    console.warn("metadataLoaded failed:", err);
                });
            }

            var oTable = this.byId("requestTable");
            if (oTable) {
                oTable.getColumns().forEach(function (col) {
                    var cd = col.getCustomData && col.getCustomData().find(function (d) {
                        return d.getKey && d.getKey() === "property";
                    });
                    var sProp = cd ? cd.getValue() : null;
                    if (sProp) {
                        this._oColumnConfig[sProp] = {
                            visible: col.getVisible ? col.getVisible() : true,
                            label: (col.getHeader && col.getHeader().getText) ? col.getHeader().getText() : sProp
                        };
                    }
                }.bind(this));
            }

            console.info("Controller initialisÃ©. OData V2:", this._bODataV2);

            this._oColumnConfig = {
                CreatorPernr: { visible: true, label: "Employee ID" },
                CreatorName: { visible: true, label: "Employee Name" },
                Reason: { visible: true, label: "Reason" },
                EffectiveDate: { visible: true, label: "Effective Date" },
                Endda: { visible: true, label: "End Date" },
                RequestInit: { visible: true, label: "Letter" },
                Checkout: { visible: true, label: "Checkout" },
                SalarySuspense: { visible: true, label: "Salary Suspense" },
                SepSlwop: { visible: true, label: "PAF" }
            };
        },

        formatFullName: function (sFirst, sLast) {
            var aParts = [sFirst, sLast].filter(Boolean);
            return aParts.join(" ");
        },

        formatDate: function (v) {
            if (!v) return "";
            if (typeof v === "string" && /^\d{8}$/.test(v)) {
                var y = v.substr(0, 4);
                var m = v.substr(4, 2);
                var d = v.substr(6, 2);
                return d + "-" + m + "-" + y;
            }
            try {
                return DateFormat.getDateInstance({ pattern: "dd/MM/yyyy" }).format(v);
            } catch (e) {
                return "";
            }
        },

        formatCheckBox: function (v) {
            if (v === undefined || v === null) return false;
            var s = String(v).toUpperCase();
            return s === "X" || s === "1" || s === "TRUE" || v === true;
        },

        formatGuid: function (sBase64) {
            if (!sBase64) return "";
            try {
                var hex = atob(sBase64).split("").map(function (c) {
                    return ("0" + c.charCodeAt(0).toString(16)).slice(-2);
                }).join("").toUpperCase();
                if (hex.length === 32) {
                    return hex.substring(0, 8) + "-" + hex.substring(8, 12) + "-" +
                        hex.substring(12, 16) + "-" + hex.substring(16, 20) + "-" + hex.substring(20, 32);
                }
                return hex;
            } catch (e) {
                console.warn("formatGuid:", e);
                return sBase64;
            }
        },

        onFilterPress: function () {
            var oSearchField = this.byId("tableSearchField");
            if (oSearchField && typeof oSearchField.setValue === "function") {
                oSearchField.setValue("");
            }
            this._applyAllFilters();
        },

        _applyAllFilters: function () {
            var oTable = this.byId("requestTable");
            if (!oTable) {
                MessageToast.show("Table introuvable.");
                return;
            }
            var oBinding = oTable.getBinding("items");
            var oModel = this.getOwnerComponent().getModel("offboardingModel");
            if (!oBinding || !oModel) {
                MessageToast.show("Binding ou modÃ¨le introuvable.");
                return;
            }

            var getCombo = function (id) {
                var o = this.byId(id);
                if (!o) return "";
                var key = (typeof o.getSelectedKey === "function") ? o.getSelectedKey() : "";
                var val = (typeof o.getValue === "function") ? o.getValue() : "";
                return (key || val || "").toString().trim();
            }.bind(this);

            var sMonth = getCombo("monthCombo");
            var sYear = getCombo("yearCombo");
            var sCategory = getCombo("categoryCombo");
            var sContractType = getCombo("contractTypeCombo");
            var sActionType = getCombo("actionTypeCombo");
            var sStatus = getCombo("statusCombo");
            var sEmployee = (this.byId("employeeNameInput") && this.byId("employeeNameInput").getValue) ?
                this.byId("employeeNameInput").getValue().trim() : "";

            console.debug("Filtres sÃ©lectionnÃ©s:", {
                month: sMonth, year: sYear, category: sCategory,
                contract: sContractType, action: sActionType,
                status: sStatus, employee: sEmployee
            });

            var aFilters = [];

            if (sMonth) aFilters.push(new Filter("Month", FilterOperator.EQ, sMonth));
            if (sYear) aFilters.push(new Filter("Year", FilterOperator.EQ, sYear));
            if (sCategory) aFilters.push(new Filter("Persg", FilterOperator.EQ, sCategory));
            if (sContractType) aFilters.push(new Filter("ContractType", FilterOperator.EQ, sContractType));
            if (sActionType) aFilters.push(new Filter("ActionType", FilterOperator.EQ, sActionType));
            if (sStatus) aFilters.push(new Filter("Status", FilterOperator.EQ, sStatus));

            if (sEmployee) {
                var aEmpFilters = [
                    new Filter("EmployeeName", FilterOperator.Contains, sEmployee),
                    new Filter("CreatorPernr", FilterOperator.Contains, sEmployee),
                    new Filter("CreatorFname", FilterOperator.Contains, sEmployee),
                    new Filter("CreatorLname", FilterOperator.Contains, sEmployee)
                ];
                aFilters.push(new Filter({ filters: aEmpFilters, and: false }));
            }

            console.group("Applying filters");
            console.log("Total filters:", aFilters.length);
            aFilters.forEach(function (f, i) {
                console.log(i, f.sPath || f.aFilters || f);
            });
            console.groupEnd();

            var oSearchField = this.byId("tableSearchField");
            if (oSearchField && typeof oSearchField.setValue === "function") {
                oSearchField.setValue("");
            }

            if (this._bODataV2) {
                try {
                    oBinding.filter(aFilters, "Application");
                    if (typeof oBinding.refresh === "function") {
                        try { oBinding.refresh(true); } catch (e) { /* ignore */ }
                    }
                } catch (e) {
                    console.error("Erreur lors de l'application des filtres au binding:", e);
                }
            } else {
                oBinding.filter(aFilters, "Control");
                console.warn("Mode fallback: modÃ¨le non OData. Les filtres sont appliquÃ©s cÃ´tÃ© client uniquement.");
            }

            var iCount = aFilters.length;
            MessageToast.show("Filtres appliquÃ©s â€” total : " + iCount);
        },

        onResetFilters: function () {
            ["monthCombo", "yearCombo", "categoryCombo", "contractTypeCombo", "actionTypeCombo", "statusCombo"].forEach(function (id) {
                var o = this.byId(id);
                if (!o) return;
                if (typeof o.setSelectedKey === "function") o.setSelectedKey("");
                if (typeof o.setValue === "function") o.setValue("");
            }.bind(this));

            var oInput = this.byId("employeeNameInput");
            if (oInput && typeof oInput.setValue === "function") oInput.setValue("");

            var oSearchField = this.byId("tableSearchField");
            if (oSearchField && typeof oSearchField.setValue === "function") {
                oSearchField.setValue("");
            }

            var oTable = this.byId("requestTable");
            var oBinding = oTable && oTable.getBinding("items");
            if (oBinding) {
                try { oBinding.filter([], "Application"); } catch (e) { }
                try { oBinding.filter([], "Control"); } catch (e) { }
                try { oBinding.sort([new Sorter(this._sSortField, false)]); } catch (e) { }
            }

            MessageToast.show("Filtres rÃ©initialisÃ©s");
        },

        onTableSearch: function (oEvent) {
            var sVal = oEvent.getParameter("newValue") || "";
            var oTable = this.byId("requestTable");
            if (!oTable) return;
            var oBinding = oTable.getBinding("items");
            if (!oBinding) return;

            if (sVal && sVal.trim().length > 0) {
                ["monthCombo", "yearCombo", "categoryCombo", "contractTypeCombo",
                    "actionTypeCombo", "statusCombo"].forEach(function (id) {
                        var o = this.byId(id);
                        if (o && typeof o.setSelectedKey === "function") o.setSelectedKey("");
                    }.bind(this));

                var oEmployeeInput = this.byId("employeeNameInput");
                if (oEmployeeInput && typeof oEmployeeInput.setValue === "function") {
                    oEmployeeInput.setValue("");
                }

                if (typeof oBinding.changeParameters === "function") {
                    oBinding.changeParameters({ search: sVal });
                } else {
                    var aFilters = [
                        new Filter("CreatorFname", FilterOperator.Contains, sVal),
                        new Filter("CreatorLname", FilterOperator.Contains, sVal),
                        new Filter("EmployeeName", FilterOperator.Contains, sVal),
                        new Filter("Reason", FilterOperator.Contains, sVal)
                    ];
                    var oSearchFilter = new Filter({ filters: aFilters, and: false });
                    oBinding.filter(oSearchFilter, "Application");
                }
            } else {
                this._applyAllFilters();
            }
        },

        onSortAscending: function (oEvent) {
            console.info("âœ… onSortAscending CALLED");
            this._sortTable("CreatorPernr", false);
        },

        onSortDescending: function (oEvent) {
            console.info("âœ… onSortDescending CALLED");
            this._sortTable("CreatorPernr", true);
        },

        _sortTable: function (sPath, bDescending) {
            var oTable = this.byId("requestTable");
            if (!oTable) {
                MessageToast.show("Table introuvable");
                return;
            }
            var oBinding = oTable.getBinding("items");
            if (!oBinding) {
                MessageToast.show("Binding introuvable");
                return;
            }

            this._sSortField = sPath;
            var aSorters = [new Sorter(sPath, bDescending)];

            console.log("_sortTable executed - Path:", sPath, "| Descending:", bDescending, "| Sorters:", aSorters);

            if (this._bODataV2 && typeof oBinding.sort === "function") {
                try {
                    oBinding.sort(aSorters);
                    console.log("Sort applied to OData V2 binding");
                } catch (e) {
                    console.error("Erreur lors du tri:", e);
                    MessageToast.show("Erreur lors du tri");
                }
            } else {
                oBinding.sort(aSorters);
                console.log("Sort applied to non-OData binding");
            }

            MessageToast.show("Tri appliquÃ©: " + sPath + " " + (bDescending ? "â†“ (DESC)" : "â†‘ (ASC)"));
        },

        onToggleFilters: function () {
            var oPage = this.byId("dynamicPage");
            if (!oPage) return;

            var bExpanded = oPage.getHeaderExpanded();
            oPage.setHeaderExpanded(!bExpanded);

            MessageToast.show(bExpanded ? "Filtres masquÃ©s" : "Filtres affichÃ©s");
        },

        onSettingsPress: function () {
            var oTable = this.byId("requestTable");
            if (!oTable) {
                MessageToast.show("Table introuvable");
                return;
            }

            if (!this._oSettingsDialog) {
                this._oSettingsDialog = new Dialog({
                    title: "Column Settings",
                    contentWidth: "400px",
                    contentHeight: "500px",
                    resizable: true,
                    draggable: true,
                    content: new VBox({
                        items: []
                    }),
                    beginButton: new Button({
                        text: "Apply",
                        type: "Emphasized",
                        press: function () {
                            this._applyColumnSettings();
                            this._oSettingsDialog.close();
                        }.bind(this)
                    }),
                    endButton: new Button({
                        text: "Cancel",
                        press: function () {
                            this._oSettingsDialog.close();
                        }.bind(this)
                    })
                });
                this.getView().addDependent(this._oSettingsDialog);
            }

            var oContent = this._oSettingsDialog.getContent()[0];
            oContent.removeAllItems();

            var aColumns = oTable.getColumns();
            aColumns.forEach(function (oColumn, iIndex) {
                var oHeader = oColumn.getHeader();
                var sText = oHeader && oHeader.getText ? oHeader.getText() : "Column " + iIndex;

                if (sText === "Guid") {
                    return;
                }

                var oCheckBox = new CheckBox({
                    text: sText,
                    selected: oColumn.getVisible(),
                    customData: [
                        new CustomData({
                            key: "columnIndex",
                            value: iIndex
                        })
                    ]
                });

                oContent.addItem(oCheckBox);
            });

            this._oSettingsDialog.open();
        },

        _applyColumnSettings: function () {
            if (!this._oSettingsDialog) return;

            var oTable = this.byId("requestTable");
            if (!oTable) return;

            var oContent = this._oSettingsDialog.getContent()[0];
            var aCheckBoxes = oContent.getItems();
            var aColumns = oTable.getColumns();

            aCheckBoxes.forEach(function (oCheckBox) {
                var aCustomData = oCheckBox.getCustomData();
                var iIndex = aCustomData[0].getValue();
                var bSelected = oCheckBox.getSelected();

                if (aColumns[iIndex]) {
                    aColumns[iIndex].setVisible(bSelected);
                }
            });

            MessageToast.show("ParamÃ¨tres de colonnes appliquÃ©s");
        },

        onToggleFullScreen: function () {
            var oPage = this.byId("dynamicPage");
            if (!oPage) return;

            this._bFullScreen = !this._bFullScreen;

            if (this._bFullScreen) {
                oPage.setHeaderExpanded(false);
                MessageToast.show("Mode plein Ã©cran activÃ©");
            } else {
                oPage.setHeaderExpanded(true);
                MessageToast.show("Mode plein Ã©cran dÃ©sactivÃ©");
            }
        },

        _refreshTableData: function () {
            var oTable = this.byId("requestTable");
            if (!oTable) return;

            var oBinding = oTable.getBinding("items");
            if (oBinding && typeof oBinding.refresh === "function") {
                oBinding.refresh(true);
                MessageToast.show("DonnÃ©es actualisÃ©es");
            }
        },

        _exportSelected: function () {
            var oTable = this.byId("requestTable");
            if (!oTable) {
                MessageToast.show("Table introuvable");
                return;
            }

            var aSelectedItems = oTable.getSelectedItems();
            if (!aSelectedItems || aSelectedItems.length === 0) {
                MessageToast.show("Aucune ligne sÃ©lectionnÃ©e");
                return;
            }

            var aCols = [];
            oTable.getColumns().forEach(function (col) {
                if (!col.getVisible || !col.getVisible()) return;
                var aCD = col.getCustomData ? col.getCustomData() : [];
                var cd = aCD.find(function (d) { return d.getKey && d.getKey() === "property"; });
                var sProp = cd ? cd.getValue() : null;
                if (sProp) {
                    var oHeader = col.getHeader && col.getHeader();
                    var sLabel = (oHeader && oHeader.getText) ? oHeader.getText() : sProp;
                    aCols.push({ label: sLabel, property: sProp });
                }
            });

            if (!aCols.length) {
                MessageToast.show("Aucune colonne disponible pour l'export");
                return;
            }

            var aData = aSelectedItems.map(function (oItem) {
                var oCtx = oItem.getBindingContext("offboardingModel");
                return oCtx ? oCtx.getObject() : null;
            }).filter(Boolean);

            if (!aData.length) {
                MessageToast.show("Aucune donnÃ©e Ã  exporter");
                return;
            }

            var aRows = aData.map(function (row) {
                var oRow = {};
                aCols.forEach(function (col) {
                    oRow[col.property] = row[col.property] !== undefined ? row[col.property] : "";
                });
                return oRow;
            });

            console.info("Export Selected - columns:", aCols);
            console.info("Export Selected - rows:", aRows.length);

            var oSettings = {
                workbook: { columns: aCols },
                dataSource: aRows,
                fileName: "Export_selected_offboarding.xlsx",
                worker: false,
                mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            };

            try {
                var oSheet = new Spreadsheet(oSettings);
                oSheet.build().then(function () {
                    MessageToast.show(aRows.length + " ligne(s) exportÃ©e(s)");
                }).catch(function (err) {
                    console.error("Erreur pendant l'export sÃ©lectionnÃ©:", err);
                    var sMsg = (err && typeof err === 'object') ?
                        (err.message || JSON.stringify(err)) :
                        String(err);
                    MessageBox.error("Erreur pendant l'export: " + sMsg);
                }).finally(function () {
                    try { oSheet.destroy(); } catch (e) { }
                });
            } catch (e) {
                console.error("Export selected - exception:", e);
                var sMsg = (e && e.message) ? e.message : String(e);
                MessageBox.error("Impossible de lancer l'export: " + sMsg);
            }
        },

        onExportToExcelAdvanced: function () {
            var oTable = this.byId("requestTable");
            if (!oTable) return MessageBox.error("Table introuvable");
            var oBinding = oTable.getBinding("items");
            if (!oBinding) return MessageBox.error("Binding introuvable.");

            var iLength = oBinding.getLength ? oBinding.getLength() : 0;
            if (iLength === 0) return MessageToast.show("Aucune donnÃ©e Ã  exporter.");

            var aContexts = oBinding.getContexts(0, iLength);
            var aData = aContexts.map(function (c) { return c.getObject(); }).filter(Boolean);

            var that = this;
            var aFormatted = aData.map(function (item) {
                return {
                    "Employee ID": item.CreatorPernr || "",
                    "Employee Name": [item.CreatorFname, item.CreatorLname].filter(Boolean).join(" "),
                    "Reason": item.Reason || "",
                    "Effective Date": (function (d) {
                        if (!d) return "";
                        if (/^\d{8}$/.test(d)) {
                            return d.substring(6, 8) + "/" + d.substring(4, 6) + "/" + d.substring(0, 4);
                        } else if (typeof d === "string" && d.startsWith("/Date(")) {
                            var dateObj = new Date(parseInt(d.replace(/\/Date\((-?\d+)\)\//, "$1"), 10));
                            if (isNaN(dateObj.getTime())) return "";
                            return ("0" + dateObj.getDate()).slice(-2) + "/" + ("0" + (dateObj.getMonth() + 1)).slice(-2) + "/" + dateObj.getFullYear();
                        } else {
                            var dateObj = new Date(d);
                            if (isNaN(dateObj.getTime())) return "";
                            return ("0" + dateObj.getDate()).slice(-2) + "/" + ("0" + (dateObj.getMonth() + 1)).slice(-2) + "/" + dateObj.getFullYear();
                        }
                    })(item.EffectiveDate),
                    "End Date": (function (d) {
                        if (!d) return "";
                        if (/^\d{8}$/.test(d)) {
                            return d.substring(6, 8) + "/" + d.substring(4, 6) + "/" + d.substring(0, 4);
                        } else if (typeof d === "string" && d.startsWith("/Date(")) {
                            var dateObj = new Date(parseInt(d.replace(/\/Date\((-?\d+)\)\//, "$1"), 10));
                            if (isNaN(dateObj.getTime())) return "";
                            return ("0" + dateObj.getDate()).slice(-2) + "/" + ("0" + (dateObj.getMonth() + 1)).slice(-2) + "/" + dateObj.getFullYear();
                        } else {
                            var dateObj = new Date(d);
                            if (isNaN(dateObj.getTime())) return "";
                            return ("0" + dateObj.getDate()).slice(-2) + "/" + ("0" + (dateObj.getMonth() + 1)).slice(-2) + "/" + dateObj.getFullYear();
                        }
                    })(item.Endda),
                    "Letter": markIfX(item.SepSlwop),
                    "Checkout": markIfX(item.Checkout),
                    "Salary Suspense": markIfX(item.SalarySuspense),
                    "Action Rec IRIS": markIfX(item.Action_Rec_Iris),
                    "PAF": markIfX(item.Paf)
                };
            });

            if (!aFormatted.length) return MessageToast.show("Aucune donnÃ©e formatÃ©e Ã  exporter.");

            if (window.XLSX) {
                try {
                    var wb = window.XLSX.utils.book_new();
                    var ws = window.XLSX.utils.json_to_sheet(aFormatted, { origin: "A1" });

                    Object.keys(ws).forEach(function (cell) {
                        if (cell[0] === "!") return;
                        var cellObj = ws[cell];

                        if (cell[0] === "A" || cell[0] === "B") {
                            cellObj.s = { font: { bold: true } };
                        }

                        if (cellObj.v === "âœ”") {
                            cellObj.s = cellObj.s || {};
                            cellObj.s.font = cellObj.s.font || {};
                            cellObj.s.font.color = { rgb: "008000" };
                        }

                        if (cellObj.v === "-") {
                            cellObj.s = cellObj.s || {};
                            cellObj.s.font = cellObj.s.font || {};
                            cellObj.s.font.color = { rgb: "FFA500" };
                        }
                    });

                    window.XLSX.utils.book_append_sheet(wb, ws, "Offboarding");
                    var sFilename = "Offboarding_Export_" + new Date().toISOString().slice(0, 10) + ".xlsx";
                    window.XLSX.writeFile(wb, sFilename);
                    MessageToast.show("Export Excel terminÃ© (" + aFormatted.length + " ligne(s)).");
                } catch (e) {
                    console.error("Erreur XLSX:", e);
                    MessageBox.error("Erreur export Excel : " + (e.message || e));
                }
            } else {
                MessageBox.warning("BibliothÃ¨que XLSX manquante : impossible de crÃ©er un vrai fichier Excel.");
            }

            function markIfX(val) {
                return (val === "X" || val === "x" || val === true || val === "Yes" || val === "âœ”") ? "âœ”" : "-";
            }
        },

        // ====================================================================
        // MÃ‰THODE DE NAVIGATION CORRIGÃ‰E - Main.controller.js
        // ====================================================================

        onNavToDetail: function (oEvent) {
            console.log("ðŸš€ onNavToDetail triggered");

            if (!oEvent) {
                MessageToast.show("Ã‰vÃ©nement manquant.");
                return;
            }

            // Get the source (button) and its binding context
            var oSource = oEvent.getSource();
            var oBindingContext = oSource.getBindingContext("offboardingModel");

            console.log("ðŸ” Source:", oSource);
            console.log("ðŸ” Binding Context:", oBindingContext);

            if (!oBindingContext) {
                MessageToast.show("Impossible de rÃ©cupÃ©rer le contexte de la ligne.");
                console.error("âŒ No binding context found");
                return;
            }

            // Get the GUID from the context
            var oData = oBindingContext.getObject();
            console.log("ðŸ” Row Data:", JSON.stringify(oData, null, 2));

            var sGuid = oData.Guid;

            if (!sGuid) {
                MessageToast.show("Le GUID est manquant pour cette requÃªte.");
                console.error("âŒ No GUID in data:", oData);
                return;
            }

            console.log("âœ… Original GUID from row:", sGuid);

            // Normalize GUID (remove dashes, uppercase)
            var sCleanGuid = this._normalizeGuid(sGuid);

            console.log("âœ… Cleaned GUID:", sCleanGuid);

            // Validate GUID format (must be 32 hex chars)
            if (!/^[0-9A-F]{32}$/i.test(sCleanGuid)) {
                MessageBox.error("Format de GUID invalide: " + sCleanGuid);
                console.error("âŒ Invalid GUID format:", sCleanGuid);
                return;
            }

            // Get router
            var oRouter = UIComponent.getRouterFor(this);
            if (!oRouter) {
                MessageToast.show("Router introuvable.");
                console.error("âŒ Router not found");
                return;
            }

            // Encode GUID for URL (important!)
            var sEncodedGuid = encodeURIComponent(sCleanGuid);

            console.log("ðŸš€ Navigating to detail with GUID:", sEncodedGuid);

            // Navigate to detail view
            try {
                oRouter.navTo("RouteDetail", {
                    RequestId: sEncodedGuid
                }, false); // false = add to browser history

                console.log("âœ… Navigation successful");
            } catch (e) {
                console.error("âŒ Navigation error:", e);
                MessageBox.error("Erreur lors de la navigation: " + e.message);
            }
        },

        _normalizeGuid: function (sGuidInput) {
            if (!sGuidInput) {
                return "";
            }

            try {
                var sGuid = String(sGuidInput).trim();

                // Case 1: Already 32-char hex (PRIORITÃ‰ 1 - vÃ©rifier en premier)
                if (/^[0-9A-Fa-f]{32}$/.test(sGuid)) {
                    return sGuid.toUpperCase();
                }

                // Case 2: 36-char UUID with dashes (PRIORITÃ‰ 2)
                if (/^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$/.test(sGuid)) {
                    return sGuid.replace(/-/g, '').toUpperCase();
                }

                // Case 3: Contains dashes anywhere else - remove and retry
                if (sGuid.indexOf('-') > -1) {
                    var sWithoutDashes = sGuid.replace(/-/g, '').toUpperCase();

                    // VÃ©rifier si c'est du hex valide aprÃ¨s suppression des tirets
                    if (/^[0-9A-F]{32}$/.test(sWithoutDashes)) {
                        return sWithoutDashes;
                    }

                    // Sinon retourner max 32 chars
                    return sWithoutDashes.substring(0, 32);
                }

                // Case 4: Base64 encoded (APRÃˆS autres cas, car c'est ambigÃ¼)
                // Base64 valide doit Ãªtre multiple de 4 ET contenir des caractÃ¨res spÃ©cifiques
                if (/^[A-Za-z0-9+/=]+$/.test(sGuid) && sGuid.length % 4 === 0 && sGuid.length > 32) {
                    try {
                        var sBinary = atob(sGuid);
                        var sHex = Array.from(sBinary)
                            .map(function (c) {
                                return ('0' + c.charCodeAt(0).toString(16)).slice(-2);
                            })
                            .join('')
                            .toUpperCase();
                        return sHex.substring(0, 32);
                    } catch (e) {
                        console.warn("Failed to decode Base64:", e);
                        // Fallback ci-dessous
                    }
                }

                // Fallback: Just take first 32 chars uppercase
                return sGuid.toUpperCase().substring(0, 32);

            } catch (e) {
                console.error("_normalizeGuid ERROR:", e);
                return String(sGuidInput).toUpperCase().substring(0, 32);
            }
        },

        // ============================================================
        // HELPER: Valider que le GUID est au bon format
        // ============================================================
        _isValidGuid: function (sGuid) {
            if (!sGuid) return false;
            // GUID normalisÃ© = 32 caractÃ¨res hex
            return /^[0-9A-F]{32}$/.test(sGuid);
        },

        onTableUpdateFinished: function (oEvent) {
            var iTotal = oEvent.getParameter && oEvent.getParameter("total");
            console.info("Table update finished - total:", iTotal);
        }

    });
});