sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/ui/core/UIComponent",
    "sap/m/MessageToast",
    "sap/m/MessageBox",
    "sap/ui/model/json/JSONModel",
    "sap/ui/model/Filter",
    "sap/ui/model/FilterOperator",
    "sap/ui/core/routing/History",
    "sap/ui/model/Sorter"
], function (Controller, UIComponent, MessageToast, MessageBox, JSONModel, Filter, FilterOperator, History, Sorter) {
    "use strict";

    return Controller.extend("com.hr.unesco.yhrappoffboardingemp.controller.Employee", {

        // ================== onInit ==================
        onInit: function () {
        	console.log("updated");
            var oModel = this.getOwnerComponent().getModel("offboardingModel");

            if (oModel && !this.getView().getModel("offboardingModel")) {
                this.getView().setModel(oModel, "offboardingModel");
            }

            this._mSortState = {
                CreatorPernr: null,
                CreatorLname: null,
                ActionType: null,
                EffectiveDate: null,
                Endda: null,
                Guid: null
            };
        },

        // ================== onFilterPress ==================
        onFilterPress: function () {
            var oTable = this.byId("requestTable");
            var oBinding = oTable.getBinding("items");
            var oBundle = this.getOwnerComponent().getModel("i18n").getResourceBundle();
            var sMsg;
            
            if (!oBinding) {
            	sMsg = oBundle.getText("NoDataForFiltering");
            	MessageToast.show(sMsg);
                //MessageToast.show("No data available for filtering.");
                return;
            }

            var aFilters = [];

            var oEffectiveDatePicker = this.byId("effectiveDateFilter");
            if (oEffectiveDatePicker) {
                var oEffectiveDate = oEffectiveDatePicker.getDateValue();
                if (oEffectiveDate) {
                    var sIsoDate = oEffectiveDate.toISOString().substring(0, 10);
                    aFilters.push(new Filter("EffectiveDate", FilterOperator.EQ, sIsoDate));
                }
            }

            var oEndDatePicker = this.byId("endDateFilter");
            if (oEndDatePicker) {
                var oEndDate = oEndDatePicker.getDateValue();
                if (oEndDate) {
                    var sIsoEndDate = oEndDate.toISOString().substring(0, 10);
                    aFilters.push(new Filter("Endda", FilterOperator.EQ, sIsoEndDate));
                }
            }

            var oActionTypeCombo = this.byId("ActionTypeCombo");
            if (oActionTypeCombo) {
                var sActionType = oActionTypeCombo.getSelectedKey();
                if (sActionType) {
                    aFilters.push(new Filter("ActionType", FilterOperator.EQ, sActionType));
                }
            }

            oBinding.filter(aFilters);
			
			if(aFilters.length > 0){
				sMsg = oBundle.getText("NbFiltersApplied", [aFilters.length]);	
			}else{
				sMsg = oBundle.getText("NoFilters");
			}
			MessageToast.show(sMsg);
            //MessageToast.show(aFilters.length > 0
            //    ? aFilters.length + " filter(s) applied"
            //    : "No active filters");
        },

        // ================== onResetFilters ==================
        onResetFilters: function () {
        	var oBundle = this.getOwnerComponent().getModel("i18n").getResourceBundle();
        	
            ["effectiveDateFilter", "endDateFilter"].forEach(function (sId) {
                var oPicker = this.byId(sId);
                if (oPicker) {
                    oPicker.setDateValue(null);
                }
            }.bind(this));

            var oActionTypeCombo = this.byId("ActionTypeCombo");
            if (oActionTypeCombo) {
                oActionTypeCombo.setSelectedKey("");
            }

            var oTable = this.byId("requestTable");
            if (oTable) {
                var oBinding = oTable.getBinding("items");
                if (oBinding) {
                    oBinding.filter([]);
                }
            }
			var sMsg = oBundle.getText("AllFiltersCleared");
			MessageToast.show(sMsg);
            //MessageToast.show("All filters have been reset");
        },

        // ================== onColumnSort ==================
        onColumnSort: function (oEvent) {
            var oButton = oEvent.getSource();
            var sSortField = oButton.data("sortField");
            
            var oBundle = this.getOwnerComponent().getModel("i18n").getResourceBundle();
            var sMsg;

            if (!sSortField) {
            	sMsg = oBundle.getText("SortFieldNotDefined");
            	MessageToast.show(sMsg);
                //MessageToast.show("Sort field not defined.");
                return;
            }

            var oTable = this.byId("requestTable");
            var oBinding = oTable.getBinding("items");
            if (!oBinding) {
            	sMsg = oBundle.getText("NoDataForSorting");
            	MessageToast.show(sMsg);
                //MessageToast.show("No data available for sorting.");
                return;
            }

            var bDescending = false;
            var sMessage = "";

            if (this._mSortState[sSortField] === null) {
                bDescending = false;
                this._mSortState[sSortField] = false;
                //sMessage = "Ascending sort on " + sSortField;
                sMessage = oBundle.getText("AscendingSortOn", [sSortField]);
            } else if (this._mSortState[sSortField] === false) {
                bDescending = true;
                this._mSortState[sSortField] = true;
                //sMessage = "Descending sort on " + sSortField;
                sMessage = oBundle.getText("DescendingSortOn", [sSortField]);
            } else {
                this._mSortState[sSortField] = null;
                oBinding.sort(null);
                sMsg = oBundle.getText("SortCleared");
            	MessageToast.show(sMsg);
                //MessageToast.show("Sort cleared");
                return;
            }

            var oSorter = new Sorter(sSortField, bDescending);
            oBinding.sort(oSorter);
            MessageToast.show(sMessage);
        },

        // ================== formatDate ==================
        formatDate: function (sDate) {
		    if (!sDate) {
		        return "-";
		    }
		
		    var oDate;
		
		    if (sDate instanceof Date) {
		        oDate = sDate;
		    } else if (typeof sDate === "string" && sDate.indexOf("/Date") === 0) {
		        var timestamp = parseInt(sDate.replace(/\/Date\((\d+)\)\//, "$1"), 10);
		        oDate = new Date(timestamp);
		    } else if (typeof sDate === "string" && sDate.indexOf("T") !== -1) {
		        oDate = new Date(sDate);
		    } else if (typeof sDate === "string" && sDate.length === 8 && sDate.indexOf("/") === -1) {
		        var year = parseInt(sDate.substring(0, 4), 10);
		        var month = parseInt(sDate.substring(4, 6), 10) - 1;
		        var day = parseInt(sDate.substring(6, 8), 10);
		        oDate = new Date(year, month, day);
		    } else if (typeof sDate === "number") {
		        oDate = new Date(sDate);
		    }
		
		    if (oDate && !isNaN(oDate.getTime())) {
		        var oDateFormat = sap.ui.core.format.DateFormat.getDateInstance({
		            pattern: "dd/MM/yyyy"
		        });
		        var sFormatted = oDateFormat.format(oDate);
		
		        // Check for sentinel values
		        if (sFormatted === "31/12/9999" || sFormatted === "00/00/0000" || sFormatted === "") {
		            return "-";
		        }
		
		        return sFormatted;
		    }
		
		    return sDate.toString();
		},

        // formatDate: function (sDate) {
        //     if (!sDate) {
        //         return "";
        //     }

        //     var oDate;

        //     if (sDate instanceof Date) {
        //         oDate = sDate;
        //     } else if (typeof sDate === "string" && sDate.indexOf("/Date") === 0) {
        //         var timestamp = parseInt(sDate.replace(/\/Date\((\d+)\)\//, "$1"), 10);
        //         oDate = new Date(timestamp);
        //     } else if (typeof sDate === "string" && sDate.indexOf("T") !== -1) {
        //         oDate = new Date(sDate);
        //     } else if (typeof sDate === "string" && sDate.length === 8 && sDate.indexOf("/") === -1) {
        //         var year = parseInt(sDate.substring(0, 4), 10);
        //         var month = parseInt(sDate.substring(4, 6), 10) - 1;
        //         var day = parseInt(sDate.substring(6, 8), 10);
        //         oDate = new Date(year, month, day);
        //     } else if (typeof sDate === "number") {
        //         oDate = new Date(sDate);
        //     }

        //     if (oDate && !isNaN(oDate.getTime())) {
        //         var oDateFormat = sap.ui.core.format.DateFormat.getDateInstance({
        //             pattern: "dd/MM/yyyy"
        //         });
        //         return oDateFormat.format(oDate);
        //     }

        //     return sDate.toString();
        // },

        // ================== formatFullName ==================
        formatFullName: function (sFirstName, sLastName) {
            var sFirst = sFirstName ? sFirstName.trim() : "";
            var sLast = sLastName ? sLastName.trim() : "";

            if (!sFirst && !sLast) {
                return "";
            }
            if (!sFirst) {
                return sLast;
            }
            if (!sLast) {
                return sFirst;
            }

            return sFirst + " " + sLast;
        },

        // ================== onAddFilesPress ==================
        onAddFilesPress: function (oEvent) {
        	var oBundle = this.getOwnerComponent().getModel("i18n").getResourceBundle();
			var sMsg;
        	
            if (!oEvent) {
            	sMsg = oBundle.getText("MissingEvent");
            	MessageToast.show(sMsg);
                //MessageToast.show("Missing event.");
                return;
            }

            var oSource = oEvent.getSource();
            var oBindingContext = oSource.getBindingContext("offboardingModel");

            if (!oBindingContext) {
            	sMsg = oBundle.getText("UnableRetrieveContextSelectedRow");
            	MessageToast.show(sMsg);
                //MessageToast.show("Unable to retrieve the context of the selected row.");
                return;
            }

            var oData = oBindingContext.getObject();
            var sGuid = oData.Guid;

            if (!sGuid) {
            	sMsg = oBundle.getText("GuidMissing");
            	MessageToast.show(sMsg);
                //MessageToast.show("GUID is missing for this request.");
                return;
            }

            var sCleanGuid = this._normalizeGuid(sGuid);

            if (!/^[0-9A-F]{32}$/i.test(sCleanGuid)) {
                MessageBox.error("Invalid GUID format: " + sCleanGuid);
                return;
            }

            var oRouter = UIComponent.getRouterFor(this);
            if (!oRouter) {
            	sMsg = oBundle.getText("RouterNotFound");
            	MessageToast.show(sMsg);
                //MessageToast.show("Router not found.");
                return;
            }

            var sEncodedGuid = encodeURIComponent(sCleanGuid);

            try {
                oRouter.navTo("RouteUpload", {
                    RequestId: sEncodedGuid
                }, false);
            } catch (e) {
                MessageBox.error("Navigation error: " + e.message);
            }
        },

        // ================== onNavToDetail ==================
        onNavToDetail: function (oEvent) {
        	var oBundle = this.getOwnerComponent().getModel("i18n").getResourceBundle();
        	var sMsg;
        	
            if (!oEvent) {
            	sMsg = oBundle.getText("MissingEvent");
            	MessageToast.show(sMsg);	
                //MessageToast.show("Missing event.");
                return;
            }

            var oSource = oEvent.getSource();
            var oBindingContext = oSource.getBindingContext("offboardingModel");

            if (!oBindingContext) {
            	sMsg = oBundle.getText("UnableRetrieveContextSelectedRow");
            	MessageToast.show(sMsg);
                //MessageToast.show("Unable to retrieve the context of the selected row.");
                return;
            }

            var oData = oBindingContext.getObject();
            var sGuid = oData.Guid;

            if (!sGuid) {
            	sMsg = oBundle.getText("GuidMissing");
            	MessageToast.show(sMsg);
                //MessageToast.show("GUID is missing for this request.");
                return;
            }

            var sCleanGuid = this._normalizeGuid(sGuid);

            if (!/^[0-9A-F]{32}$/i.test(sCleanGuid)) {
                MessageBox.error("Invalid GUID format: " + sCleanGuid);
                return;
            }

            var oRouter = UIComponent.getRouterFor(this);
            if (!oRouter) {
            	sMsg = oBundle.getText("RouterNotFound");
            	MessageToast.show(sMsg);
                //MessageToast.show("Router not found.");
                return;
            }

            var sEncodedGuid = encodeURIComponent(sCleanGuid);

            try {
                oRouter.navTo("RouteDetail", {
                    RequestId: sEncodedGuid
                }, false);
            } catch (e) {
                MessageBox.error("Navigation error: " + e.message);
            }
        },

        // ================== _normalizeGuid ==================
        _normalizeGuid: function (sGuidInput) {
            if (!sGuidInput) {
                return "";
            }

            try {
                var sGuid = String(sGuidInput).trim();

                if (/^[0-9A-Fa-f]{32}$/.test(sGuid)) {
                    return sGuid.toUpperCase();
                }

                if (/^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$/.test(sGuid)) {
                    return sGuid.replace(/-/g, '').toUpperCase();
                }

                if (sGuid.indexOf('-') > -1) {
                    var sWithoutDashes = sGuid.replace(/-/g, '').toUpperCase();
                    if (/^[0-9A-F]{32}$/.test(sWithoutDashes)) {
                        return sWithoutDashes;
                    }
                    return sWithoutDashes.substring(0, 32);
                }

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
                    } catch (e) {}
                }

                return sGuid.toUpperCase().substring(0, 32);

            } catch (e) {
                return String(sGuidInput).toUpperCase().substring(0, 32);
            }
        },

        // ================== _isValidGuid ==================
        _isValidGuid: function (sGuid) {
            if (!sGuid) return false;
            return /^[0-9A-F]{32}$/.test(sGuid);
        }
    });
});