sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/ui/core/UIComponent",
    "sap/m/MessageToast",
    "sap/m/MessageBox",
    "sap/ui/model/json/JSONModel",
    "sap/ui/model/Filter",
    "sap/ui/model/FilterOperator",
    "sap/ui/core/routing/History"
], function (Controller, UIComponent, MessageToast, MessageBox, JSONModel, Filter, FilterOperator, History) {
    "use strict";

    return Controller.extend("com.hr.unesco.yhrappoffboardingemp.controller.Detail", {

        /* =========================================================== */
        /* ======================= INIT ============================== */
        /* =========================================================== */

        onInit: function () {
            // ModÃ¨le pour la requÃªte/employÃ© sÃ©lectionnÃ©
            var oSelectedRequestModel = new JSONModel();
            this.getView().setModel(oSelectedRequestModel, "selectedRequest");

            // ModÃ¨le pour le statut d'upload
            var oUploadModel = new JSONModel({ fileSelected: false, uploadInProgress: false });
            this.getView().setModel(oUploadModel, "uploadModel");

            // Attache la route "RouteDetail"
            var oRouter = UIComponent.getRouterFor(this);
            if (oRouter.getRoute("RouteDetail")) {
                oRouter.getRoute("RouteDetail").attachPatternMatched(this.onRouteMatched, this);
            }
        },

        /* =========================================================== */
        /* ============== ROUTING & CHARGEMENT DES DONNÃ‰ES =========== */
        /* =========================================================== */

        onRouteMatched: function (oEvent) {
            var oArgs = oEvent.getParameter("arguments");

            if (oArgs && oArgs.RequestId) {
                var sRawGuid = decodeURIComponent(oArgs.RequestId);
                var sGuid = this._normalizeGuid(sRawGuid);

                if (!/^[0-9A-F]{32}$/i.test(sGuid)) {
                    MessageBox.error("Format de GUID invalide: " + sGuid);
                    this._clearSelection();
                    return;
                }

                this._sCurrentRequestId = sGuid;
                this._clearSelection();
                this._loadRequestByGuidOData(sGuid);
            } else {
                this._clearSelection();
            }
        },

        _loadRequestByGuidOData: function (sCleanGuid) {
            var oModel = this.getView().getModel("offboardingModel");
            var oSelectedModel = this.getView().getModel("selectedRequest");

            if (!oModel) {
                MessageBox.error("ModÃ¨le OData introuvable");
                return;
            }

            if (!sCleanGuid || sCleanGuid.length !== 32) {
                MessageBox.error("GUID invalide: " + sCleanGuid);
                return;
            }

            var sFormattedGuid = sCleanGuid.replace(/-/g, '').toUpperCase();
            this.getView().setBusy(true);

            var aFilters = [new Filter("Guid", FilterOperator.EQ, sFormattedGuid)];

            oModel.read("/RequestSet", {
                filters: aFilters,
                success: function (oData) {
                	// debugger;
                    this.getView().setBusy(false);

                    var oResult = null;

                    if (oData.results && oData.results.length > 0) {
                        var aMatches = oData.results.filter(function (item) {
                            var sItemGuid = this._normalizeGuid(item.Guid);
                            return sItemGuid === sFormattedGuid;
                        }.bind(this));

                        if (aMatches.length > 0) {
                            oResult = aMatches[0];
                        } else {
                            oResult = oData.results[0];
                        }
                    } else {
                        oResult = oData;
                    }

                    if (!oResult || !oResult.Guid) {
                        MessageBox.error("Aucune donnÃ©e trouvÃ©e pour le GUID: " + sFormattedGuid);
                        oSelectedModel.setData({});
                        return;
                    }

                    var sReturnedGuid = this._normalizeGuid(oResult.Guid);

                    if (sReturnedGuid !== sFormattedGuid) {
                        // GUID mismatch
                    }

                    oSelectedModel.setData(oResult);
                    var oBundle = this.getView().getModel("i18n").getResourceBundle();
        			var sMsg = oBundle.getText("EmployeeLoaded", [oResult.CreatorFname, oResult.CreatorLname]);
        			MessageToast.show(sMsg);
                    //MessageToast.show("EmployÃ© chargÃ©: " + (oResult.CreatorFname || "") + " " + (oResult.CreatorLname || ""));

                    this._loadDocuments(sFormattedGuid);
                    this._loadComments(sFormattedGuid);
                    this._loadWorkflowSteps(sFormattedGuid);
                    this._loadLinks(sFormattedGuid);

                }.bind(this),
                error: function (oError) {
                    this.getView().setBusy(false);

                    var sErrorMsg = "EmployÃ© introuvable avec GUID: " + sFormattedGuid;

                    try {
                        var oErrParsed = JSON.parse(oError.responseText);
                        if (oErrParsed.error && oErrParsed.error.message) {
                            sErrorMsg = oErrParsed.error.message.value || sErrorMsg;
                        }
                    } catch (e) {}

                    MessageBox.error(sErrorMsg, {
                        details: oError.responseText
                    });

                    oSelectedModel.setData({});
                }.bind(this)
            });
        },
		_loadDocuments: function (sGuid) {
			// debugger;
		    const oModel = this.getView().getModel("offboardingModel");
		    const oSelectedModel = this.getView().getModel("selectedRequest");
		    
		    var oBundle = this.getOwnerComponent().getModel("i18n").getResourceBundle();
		    
		    if (!oModel || !sGuid) return Promise.resolve();
		
		    const oView = this.getView();
		    oView.setBusy(true);
		
		    return new Promise((resolve) => {
		        const aDocFilters = [new sap.ui.model.Filter("REQUEST_ID", sap.ui.model.FilterOperator.EQ, sGuid)];
		        const aVisibilityFilters = [new sap.ui.model.Filter("Guid", sap.ui.model.FilterOperator.EQ, sGuid)];
		
		        // Step 1: Fetch visible document types
				oModel.read("/DocumentToUploadSet", {
				    filters: aVisibilityFilters,
				    success: function (oVisibilityData) {
				        const aVisibleTypes = (oVisibilityData.results || [])
				            .filter(v => v.Visible === true)
				            .map(v => v.Doc_Type);
				
				        // Step 2: Fetch actual uploaded documents
				        oModel.read("/TOAATSet", {
				            filters: aDocFilters,
				            success: function (oDocData) {
				
				                // Helper: format YYYYMMDD â†’ dd-mm-yyyy
				                var formatDate = function (sDate) {
				                    if (!sDate) return "";
				                    var sVal = String(sDate).trim();
				                    if (sVal.length !== 8) return sVal; // fallback if not YYYYMMDD
				                    var year = sVal.substring(0, 4);
				                    var month = sVal.substring(4, 6);
				                    var day = sVal.substring(6, 8);
				                    return day + "/" + month + "/" + year;
				                };
				
				                const aDocs = (oDocData.results || []).filter(function (d) {
				                    return !!d.Filename && aVisibleTypes.includes(d.AttachType);
				                }).map(function (oDoc) {
				                    return {
				                        DocumentName: oDoc.Filename || "",
				                        Type: oDoc.AttachTypeTxt || "",
				                        CREATOR: (oDoc.CreatorFname + " " + oDoc.CreatorLname).trim(),
				                        UploadDate: formatDate(oDoc.CreationDate) // <-- formatted here
				                    };
				                });
				
				                const oCurrentData = oSelectedModel.getData() || {};
				                oCurrentData.Documents = aDocs;
				                oSelectedModel.setData(oCurrentData);
				                oView.setBusy(false);
				                resolve();
				            },
				            error: function () {
				                oSelectedModel.setProperty("/Documents", []);
				                var sMsg = oBundle.getText("ErrorLoadingDocuments"); 
				                sap.m.MessageToast.show(sMsg);
				                //sap.m.MessageToast.show("Erreur lors du chargement des documents");
				                oView.setBusy(false);
				                resolve();
				            }
				        });
				    },
				    error: function () {
				        oSelectedModel.setProperty("/Documents", []);
				        var sMsg = oBundle.getText("ErrorLoadingDocumentTypes"); 
				        sap.m.MessageToast.show(sMsg);
				        //sap.m.MessageToast.show("Erreur lors du chargement des types de documents Ã  afficher");
				        oView.setBusy(false);
				        resolve();
				    }
				});

		        // oModel.read("/DocumentToUploadSet", {
		        //     filters: aVisibilityFilters,
		        //     success: function (oVisibilityData) {
		        //         const aVisibleTypes = (oVisibilityData.results || [])
		        //             .filter(v => v.Visible === true)
		        //             .map(v => v.Doc_Type);
		
		        //         // Step 2: Fetch actual uploaded documents
		        //         oModel.read("/TOAATSet", {
		        //             filters: aDocFilters,
		        //             success: function (oDocData) {
		        //                 const aDocs = (oDocData.results || []).filter(function (d) {
		        //                     return !!d.Filename && aVisibleTypes.includes(d.AttachType);
		        //                 }).map(function (oDoc) {
		        //                     return {
		        //                         DocumentName: oDoc.Filename || "",
		        //                         Type: oDoc.AttachTypeTxt || "",
		        //                         CREATOR: (oDoc.CreatorFname + " " + oDoc.CreatorLname).trim(),
		        //                         UploadDate: oDoc.CreationDate
		        //                     };
		        //                 });
		
		        //                 const oCurrentData = oSelectedModel.getData() || {};
		        //                 oCurrentData.Documents = aDocs;
		        //                 oSelectedModel.setData(oCurrentData);
		        //                 oView.setBusy(false);
		        //                 resolve();
		        //             },
		        //             error: function () {
		        //                 oSelectedModel.setProperty("/Documents", []);
		        //                 sap.m.MessageToast.show("Erreur lors du chargement des documents");
		        //                 oView.setBusy(false);
		        //                 resolve();
		        //             }
		        //         });
		        //     },
		        //     error: function () {
		        //         oSelectedModel.setProperty("/Documents", []);
		        //         sap.m.MessageToast.show("Erreur lors du chargement des types de documents Ã  afficher");
		        //         oView.setBusy(false);
		        //         resolve();
		        //     }
		        // });
		    });
		},

		
        // _loadDocuments: function (sGuid) {
        //     var oModel = this.getView().getModel("offboardingModel");
        //     var oSelectedModel = this.getView().getModel("selectedRequest");
        //     if (!oModel || !sGuid) return Promise.resolve();

        //     return new Promise(function (resolve) {
        //         var aFilters = [new sap.ui.model.Filter("REQUEST_ID", sap.ui.model.FilterOperator.EQ, sGuid)];
        //         oModel.read("/TOAATSet", {
        //             filters: aFilters,
        //             success: function (oData) {
        //                 var aDocs = (oData.results || []).filter(function (d) {
        //                     return !!d.Filename;
        //                 }).map(function (oDoc) {
        //                     return {
        //                         DocumentName: oDoc.Filename || "",
        //                         Type: oDoc.AttachTypeTxt || "",
        //                         CREATOR: (oDoc.CreatorFname + " " + oDoc.CreatorLname).trim(),
        //                         UploadDate: oDoc.CreationDate + " " + oDoc.CreationTime
        //                     };
        //                 });

        //                 var oCurrentData = oSelectedModel.getData() || {};
        //                 oCurrentData.Documents = aDocs;
        //                 oSelectedModel.setData(oCurrentData);
        //                 resolve();
        //             },
        //             error: function () {
        //                 var oCurrentData = oSelectedModel.getData() || {};
        //                 oCurrentData.Documents = [];
        //                 oSelectedModel.setData(oCurrentData);
        //                 sap.m.MessageToast.show("Erreur lors du chargement des documents");
        //                 resolve();
        //             }
        //         });
        //     });
        // },
        _loadLinks: function (sGuid) {
        	// debugger;
		    const oModel = this.getView().getModel("offboardingModel");
		    const oSelectedModel = this.getView().getModel("selectedRequest");
		    var oBundle = this.getOwnerComponent().getModel("i18n").getResourceBundle();
		    if (!oModel || !sGuid) return Promise.resolve();
			if (oSelectedModel.getData().ActionType === "01"){
				this.getView().byId("invitation").setVisible(true);
			}else{
				this.getView().byId("invitation").setVisible(false);
			}
		    return new Promise(function (resolve) {
		        const aFilters = [new sap.ui.model.Filter("Guid", sap.ui.model.FilterOperator.EQ, sGuid)];
		
		        oModel.read("/DocumentLinkSet", {
		            filters: aFilters,
		            success: function (oData) {
		                const aLinks = (oData.results || []).filter(function (link) {
		                    return !!link.Link;
		                }).map(function (link) {
		                    return {
		                        DocumentName: link.DocTxt || "",
		                        Url: link.Link || "",
		                        Id: link.IdLink || "",
		                        LinkTxt: link.LinkTxt || ""
		                    };
		                });
		
		                const oCurrentData = oSelectedModel.getData() || {};
		                oCurrentData.DocumentLinks = aLinks;
		                oSelectedModel.setData(oCurrentData);
		                resolve();
		            },
		            error: function () {
		                const oCurrentData = oSelectedModel.getData() || {};
		                oCurrentData.DocumentLinks = [];
		                oSelectedModel.setData(oCurrentData);
		                var sMsg = oBundle.getText("ErrorLoadingLinks");
		                sap.m.MessageToast.show(sMsg);
		                //sap.m.MessageToast.show("Erreur lors du chargement des liens de documents");
		                resolve();
		            }
		        });
		    });
		},



        _loadComments: function (sGuid) {
            var oModel = this.getView().getModel("offboardingModel");
            var oSelectedModel = this.getView().getModel("selectedRequest");
            
            var oBundle = this.getOwnerComponent().getModel("i18n").getResourceBundle();
            
            if (!oModel || !sGuid) return;

            var sCleanGuid = sGuid.replace(/-/g, "");
            var aFilters = [new Filter("Guid", FilterOperator.EQ, sCleanGuid)];

            oModel.read("/CommentSet", {
                filters: aFilters,
                success: function (oData) {
                    var oCurrentData = oSelectedModel.getData() || {};
                    oCurrentData.Commentset = oData.results || [];
                    oSelectedModel.setData(oCurrentData);
                },
                error: function () {
                    var oCurrentData = oSelectedModel.getData() || {};
                    oCurrentData.Commentset = [];
                    oSelectedModel.setData(oCurrentData);
                    var sMsg = oBundle.getText("ErrorLoadingComents");
                    MessageToast.show(sMsg);
                    //MessageToast.show("Erreur lors du chargement des commentaires");
                }
            });
        },

        _loadWorkflowSteps: function (sGuid) {
            var oModel = this.getView().getModel("offboardingModel");
            var oSelectedModel = this.getView().getModel("selectedRequest");
            var oBundle = this.getOwnerComponent().getModel("i18n").getResourceBundle();
            if (!oModel || !sGuid) return;

            var sCleanGuid = sGuid.replace(/-/g, "");
            var aFilters = [new Filter("Guid", FilterOperator.EQ, sCleanGuid)];

            oModel.read("/WorkflowStepSet", {
                filters: aFilters,
                success: function (oData) {
                    var oCurrentData = oSelectedModel.getData() || {};
                    oCurrentData.WorkflowStepSet = oData.results || [];
                    oSelectedModel.setData(oCurrentData);
                }.bind(this),
                error: function () {
                    var oCurrentData = oSelectedModel.getData() || {};
                    oCurrentData.WorkflowStepSet = [];
                    oSelectedModel.setData(oCurrentData);
                    var sMsg = oBundle.getText("ErrorLoadingWfSteps");
                    MessageToast.show(sMsg);
                    //MessageToast.show("Erreur lors du chargement des Ã©tapes du workflow");
                }
            });
        },

        _clearSelection: function () {
            var oSelectedModel = this.getView().getModel("selectedRequest");
            if (oSelectedModel) {
                oSelectedModel.setData({});
            }
        },

        /* =========================================================== */
        /* ==================== ACTIONS UI ============================ */
        /* =========================================================== */

        onOpenDocument: function (oEvent) {
            var oContext = oEvent.getSource().getBindingContext("selectedRequest");
            if (!oContext) {
                MessageBox.error("Impossible de rÃ©cupÃ©rer les informations du document.");
                return;
            }

            var oDocData = oContext.getObject();
            var sDocId = oDocData.ARC_DOC_ID;
            var sFileName = oDocData.FILENAME || "Document.pdf";

            if (!sDocId) {
                MessageBox.error("Aucun identifiant de document (ARC_DOC_ID) trouvÃ©.");
                return;
            }

            var sUrl = "/sap/opu/odata/sap/ZARCHIVE_SRV/DocumentSet('" + encodeURIComponent(sDocId) + "')/$value";
            window.open(sUrl, "_blank");
        },

        onDownloadDocument: function (oEvent) {
            var oContext = oEvent.getSource().getBindingContext("selectedRequest");
            if (!oContext) {
                MessageBox.error("Impossible de rÃ©cupÃ©rer les informations du document.");
                return;
            }

            var oDocData = oContext.getObject();
            var sDocId = oDocData.ARC_DOC_ID;
            var sFileName = oDocData.FILENAME || "document.pdf";

            if (!sDocId) {
                MessageBox.error("Aucun identifiant de document (ARC_DOC_ID) trouvÃ©.");
                return;
            }

            var sUrl = "/sap/opu/odata/sap/ZARCHIVE_SRV/DocumentSet('" + encodeURIComponent(sDocId) + "')/$value";

            var oLink = document.createElement("a");
            oLink.href = sUrl;
            oLink.download = sFileName;
            oLink.target = "_blank";
            document.body.appendChild(oLink);
            oLink.click();
            document.body.removeChild(oLink);
        },

        onDeleteDocument: function () {
            MessageBox.warning("FonctionnalitÃ© de suppression Ã  implÃ©menter");
        },

        onNavToUpload: function () {
            var sGuid = this._sCurrentRequestId;

            if (!sGuid) {
                MessageBox.warning("Aucune demande sÃ©lectionnÃ©e !");
                return;
            }

            var sCleanGuid = sGuid.replace(/-/g, "");
            var sEncodedGuid = encodeURIComponent(sCleanGuid);

            var oRouter = UIComponent.getRouterFor(this);

            if (!oRouter) {
                MessageBox.error("Erreur : Router non disponible");
                return;
            }

            try {
                oRouter.navTo("RouteUpload", {
                    RequestId: sEncodedGuid
                }, false);
            } catch (e) {
                MessageBox.error("Erreur lors de la navigation vers Upload");
            }
        },

        onNavBack: function () {
            var oHistory = History.getInstance();
            var sPreviousHash = oHistory.getPreviousHash();

            if (sPreviousHash !== undefined) {
                window.history.go(-1);
            } else {
                var oRouter = UIComponent.getRouterFor(this);
                oRouter.navTo("RouteMaster", {}, true);
            }
        },

        /* =========================================================== */
        /* ==================== FORMATTERS ============================ */
        /* =========================================================== */

        formatFullName: function (sLastName, sFirstName) {
            var last = sLastName || "";
            var first = sFirstName || "";
            return (last + " " + first).trim().toUpperCase();
        },

        // formatRequestStatus: function (bClosed) {
        //     return bClosed === 'X' ? "Closed" : "In Progress";
        // },
       formatRequestStatus: function (bClosed) {
		    const urlParams = new URLSearchParams(window.location.search);
		    const lang = urlParams.get("sap-language") ? urlParams.get("sap-language").toUpperCase() : "EN";
			
		    //console.log("[formatRequestStatus] sap-language param:", lang);
		    //console.log("[formatRequestStatus] Closed flag:", bClosed);
		    
		    var oBundle = this.getOwnerComponent().getModel("i18n").getResourceBundle();
			var txtClosed = oBundle.getText("Closed");
			var txtInProgress = oBundle.getText("inProgress");
		    let result;
		    result = bClosed === 'X' ? txtClosed : txtInProgress;

		
		    //console.log("[formatRequestStatus] Returning:", result);
		    return result;
		},






        formatRequestStatusState: function (bClosed) {
            return bClosed === 'X' ? "Success" : "Warning";
        },
        getLanguageFromUrl: function () {
		    const urlParams = new URLSearchParams(window.location.search);
		    const lang = urlParams.get("language");
		    return lang ? lang.toUpperCase() : "EN"; // default to EN
		},

        formatDateApproval: function (sDateStr) {
        	var sFormatted;
        	
            if (!sDateStr || sDateStr.length !== 8) return "";
            
            var year = sDateStr.substring(0, 4);
            var month = sDateStr.substring(4, 6);
            var day = sDateStr.substring(6, 8);
            sFormatted = day + "/" + month + "/" + year;
            
            if (sFormatted === "31/12/9999" || sFormatted === "00/00/0000") {
		            return "-";
		    }else{
		    	return sFormatted;	
		    }
        },

        formatCompletedStatus: function (sCompleted) {
            if (!sCompleted) return false;
            var sValue = String(sCompleted).trim().toUpperCase();
            return sValue === "X" || sValue === "1" || sValue === "TRUE";
        },

        formatGuidReadable: function (sGuidInput) {
            if (!sGuidInput) return "N/A";
            try {
                var sNormalized = this._normalizeGuid(sGuidInput);
                return sNormalized;
            } catch (e) {
                return String(sGuidInput).substring(0, 32);
            }
        },

        getDocumentType: function (sDocumentName) {
            if (!sDocumentName) return "Unknown";
            var sExtension = sDocumentName.split('.').pop().toLowerCase();
            var oTypeMap = {
                pdf: "pdf",
                doc: "Word",
                docx: "Word",
                xls: "Excel",
                xlsx: "Excel",
                jpg: "Image",
                jpeg: "Image",
                png: "Image",
                txt: "Text"
            };
            return oTypeMap[sExtension] || "Other";
        },

        formatDocumentTypeState: function (sDocumentName) {
            var sType = this.getDocumentType(sDocumentName);
            var oStateMap = {
                "pdf": "Error",
                "Word": "Warning",
                "Excel": "Success",
                "Image": "Information",
                "Text": "None"
            };
            return oStateMap[sType] || "None";
        },

        /* =========================================================== */
        /* ==================== GUID HELPERS ============================ */
        /* =========================================================== */

        _normalizeGuid: function (sGuidInput) {
            if (!sGuidInput) return "";

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

        _isValidGuid: function (sGuid) {
            if (!sGuid) return false;
            return /^[0-9A-F]{32}$/.test(sGuid);
        },

        formatLastUpdate: function (sDate, sTime, sFName, sLName) {
            if (!sDate || !sTime) return "";
            const dateStr = this.formatDateTime(sDate, sTime);
            const userStr = [sFName, sLName].filter(Boolean).join(" ");
            return `${dateStr} by ${userStr}`;
        },

        formatDateTime: function (sDate, sTime) {
            if (!sDate || !sTime) return "";
            const date = sap.ui.core.format.DateFormat.getDateInstance({ pattern: "dd/MM/yyyy HH:mm:ss" });
            const oDate = new Date(
                sDate.substring(0, 4),
                sDate.substring(4, 6) - 1,
                sDate.substring(6, 8),
                sTime.substring(0, 2),
                sTime.substring(2, 4),
                sTime.substring(4, 6)
            );
            return date.format(oDate);
        },

        // ================== NAVIGATION ==================
        onAddFilesPress: function () {
            var oSelectedModel = this.getView().getModel("selectedRequest");
            var oBundle = this.getOwnerComponent().getModel("i18n").getResourceBundle();
            var sMsg;

            if (!oSelectedModel) {
            	sMsg = oBundle.getText("ModelSelectedReqNotFound");
            	MessageToast.show(sMsg);
                //MessageToast.show("ModÃ¨le selectedRequest introuvable.");
                return;
            }

            var oData = oSelectedModel.getData();
            var sGuid = oData.Guid;

            if (!sGuid) {
            	sMsg = oBundle.getText("GuidMissing");
            	MessageToast.show(sMsg);
                //MessageToast.show("Le GUID est manquant pour cette requÃªte.");
                return;
            }

            var sCleanGuid = this._normalizeGuid(sGuid);

            if (!/^[0-9A-F]{32}$/i.test(sCleanGuid)) {
                MessageBox.error("Format de GUID invalide: " + sCleanGuid);
                return;
            }

            var oRouter = UIComponent.getRouterFor(this);
            if (!oRouter) {
            	sMsg = oBundle.getText("RouterNotFound");
            	MessageToast.show(sMsg);
                //MessageToast.show("Router introuvable.");
                return;
            }

            var sEncodedGuid = encodeURIComponent(sCleanGuid);

            try {
                oRouter.navTo("RouteUpload", {
                    RequestId: sEncodedGuid
                }, false);
            } catch (e) {
                MessageBox.error("Erreur lors de la navigation: " + e.message);
            }
        }

    });
});