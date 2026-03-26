sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/ui/core/UIComponent",
    "sap/m/MessageToast",
    "sap/m/MessageBox",
    "sap/ui/model/json/JSONModel",
    "sap/ui/model/Filter",
    "sap/ui/model/FilterOperator",
    "sap/ui/core/routing/History",
    "sap/m/Dialog",
    "sap/m/VBox",
    "sap/m/HBox",
    "sap/m/Label",
    "sap/m/Title",
    "sap/m/Select",
    "sap/m/TextArea",
    "sap/m/CheckBox",
    "sap/m/Button",
    "sap/m/Panel",
    "sap/ui/core/Item",
    "sap/ui/core/SeparatorItem"
], function (Controller, UIComponent, MessageToast, MessageBox, JSONModel, Filter, FilterOperator, History,
    Dialog, VBox, HBox, Label, Title, Select, TextArea, CheckBox, Button, Panel, Item, SeparatorItem) {
    "use strict";
    return Controller.extend("com.hr.unesco.yhrappoffboarding.controller.Detail", {
        /*------------------onInit--------------------*/
        onInit: function () {
            var oSelectedRequestModel = new JSONModel();
            this.getView().setModel(oSelectedRequestModel, "selectedRequest");
            var oUploadModel = new JSONModel({ fileSelected: false, uploadInProgress: false });
            this.getView().setModel(oUploadModel, "uploadModel");
            var oRouter = UIComponent.getRouterFor(this);
            oRouter.getRoute("RouteDetail").attachPatternMatched(this.onRouteMatched, this);
        },
        /*------------------onRouteMatched--------------------*/
        onRouteMatched: function (oEvent) {
            var oArgs = oEvent.getParameter("arguments");
            if (oArgs && oArgs.RequestId) {
                var sRawGuid = decodeURIComponent(oArgs.RequestId);
                var sGuid = this._normalizeGuid(sRawGuid);
                if (!/^[0-9A-F]{32}$/i.test(sGuid)) {
                    MessageBox.error("Invalid GUID format: " + sGuid);
                    this._clearSelection();
                    return;
                }
                this._sCurrentRequestId = sGuid;
                this._clearSelection();
                this._loadRequestByGuidOData(sGuid);
            } else {
                MessageBox.error("No RequestId found in route arguments");
                this._clearSelection();
            }
        },
        /*------------------_normalizeGuid--------------------*/
        _normalizeGuid: function (sGuidInput) {
            if (!sGuidInput) return "";
            try {
                // If it looks like Base64, decode it
                if (/^[A-Za-z0-9+/=]+$/.test(sGuidInput) && sGuidInput.length > 32) {
                    try {
                        var sBinary = atob(sGuidInput);
                        var sHex = Array.from(sBinary)
                            .map(function (c) {
                                return ('0' + c.charCodeAt(0).toString(16)).slice(-2);
                            })
                            .join('')
                            .toUpperCase();
                        return sHex;
                    } catch (e) {
                        MessageBox.error("Failed to decode Base64 GUID, treating as hex");
                    }
                }
                // If it has dashes, remove them
                if (sGuidInput.indexOf('-') > -1) {
                    return sGuidInput.replace(/-/g, '').toUpperCase();
                }
                // Already hex format
                return sGuidInput.toUpperCase();
            } catch (e) {
                MessageBox.error("Error normalizing GUID");
                return sGuidInput.toUpperCase();
            }
        },
        /*------------------ _loadDocuments--------------------*/
        _loadDocuments: function (sGuid) {
            var oModel = this.getView().getModel("offboardingModel");
            var oSelectedModel = this.getView().getModel("selectedRequest");
            if (!oModel || !sGuid) return;
            var aFilters = [new Filter("REQUEST_ID", FilterOperator.EQ, sGuid)];
            oModel.read("/TOAATSet", {
                filters: aFilters,
                success: function (oData) {
                    var aDocuments = (oData.results || []).map(function (oDoc) {
                        return {
                            Filename: oDoc.Filename || "No Name",
                            AttachTypeTxt: oDoc.AttachTypeTxt || "",
                            Filesize: oDoc.Filesize || "",
                            CreatorFname: oDoc.CreatorFname || "",
                            CreatorLname: oDoc.CreatorLname || "",
                            CreationDate: oDoc.CreationDate || "",
                            CreationTime: oDoc.CreationTime || "",
                            LastUpdDate: oDoc.LastUpdDate || "",
                            LastUpdTime: oDoc.LastUpdTime || "",
                            ArchiveDocId: oDoc.ArchiveDocId || ""
                        };
                    });
                    var oCurrentData = oSelectedModel.getData() || {};
                    oCurrentData.Documents = aDocuments;
                    oSelectedModel.setData(oCurrentData);
                }.bind(this),
                error: function (oError) {
                    var oCurrentData = oSelectedModel.getData() || {};
                    oCurrentData.Documents = [];
                    oSelectedModel.setData(oCurrentData);
                    MessageToast.show("Error loading documents");
                }
            });
        },
        /*------------------ _loadRequestByGuidOData--------------------*/
        _loadRequestByGuidOData: function (sCleanGuid) {
            var oModel = this.getView().getModel("offboardingModel");
            var oSelectedModel = this.getView().getModel("selectedRequest");
            if (!oModel) {
                MessageBox.error("OData model 'offboardingModel' not found");
                return;
            }
            if (!sCleanGuid || sCleanGuid.length !== 32) {
                MessageBox.error("Invalid GUID: " + sCleanGuid);
                return;
            }
            // Format GUID for OData (uppercase, no dashes)
            var sFormattedGuid = sCleanGuid.replace(/-/g, '').toUpperCase();
            // Set busy indicator
            this.getView().setBusy(true);
            // Create filter
            var aFilters = [new Filter("Guid", FilterOperator.EQ, sFormattedGuid)];
            oModel.read("/RequestSet", {
                filters: aFilters,
                success: function (oData) {
                    this.getView().setBusy(false);
                    var oResult = null;
                    // Handle both array and single result
                    if (oData.results && oData.results.length > 0) {
                        var aMatches = oData.results.filter(function (item) {
                            var sItemGuid = this._normalizeGuid(item.Guid);
                            return sItemGuid === sFormattedGuid;
                        }.bind(this));
                        if (aMatches.length > 0) {
                            oResult = aMatches[0];
                        } else {
                            oResult = oData.results[0]; // Fallback
                        }
                    } else {
                        oResult = oData;
                    }
                    if (!oResult || !oResult.Guid) {
                        MessageBox.error("No data found for GUID: " + sFormattedGuid);
                        oSelectedModel.setData({});
                        return;
                    }
                    // Verify GUID match
                    var sReturnedGuid = this._normalizeGuid(oResult.Guid);
                    if (sReturnedGuid !== sFormattedGuid) {
                        MessageBox.warning(
                            "The returned GUID does not match the requested GUID.\n\n" +
                            "Expected: " + sFormattedGuid + "\n" +
                            "Received: " + sReturnedGuid
                        );
                    }
                    // Set data to model
                    oSelectedModel.setData(oResult);
                    // Load related data
                    Promise.all([
                        this._loadDocuments(sFormattedGuid),
                        this._loadComments(sFormattedGuid),
                        this._loadWorkflowSteps(sFormattedGuid)
                    ]).then(function () {
                        MessageToast.show("Data loaded successfully");
                    }).catch(function () {
                        MessageToast.show("Error loading related data");
                    });
                }.bind(this),
                error: function (oError) {
                    this.getView().setBusy(false);
                    var sErrorMsg = "Request not found for GUID: " + sFormattedGuid;
                    try {
                        var oErrParsed = JSON.parse(oError.responseText);
                        if (oErrParsed.error && oErrParsed.error.message) {
                            sErrorMsg = oErrParsed.error.message.value || sErrorMsg;
                        }
                    } catch (e) {
                        // Ignore JSON parse errors
                    }
                    MessageBox.error(sErrorMsg, {
                        details: oError.responseText
                    });
                    oSelectedModel.setData({});
                }.bind(this)
            });
        },
        /*------------------ _loadComments--------------------*/
        _loadComments: function (sGuid) {
            var oModel = this.getView().getModel("offboardingModel");
            var oSelectedModel = this.getView().getModel("selectedRequest");
            return new Promise(function (resolve) {
                if (!oModel || !sGuid) {
                    resolve();
                    return;
                }
                var aFilters = [new Filter("Guid", FilterOperator.EQ, sGuid)];
                oModel.read("/CommentSet", {
                    filters: aFilters,
                    success: function (oData) {
                        var oCurrentData = oSelectedModel.getData() || {};
                        oCurrentData.Commentset = oData.results || [];
                        oSelectedModel.setData(oCurrentData);
                        resolve();
                    },
                    error: function () {
                        var oCurrentData = oSelectedModel.getData() || {};
                        oCurrentData.Commentset = [];
                        oSelectedModel.setData(oCurrentData);
                        MessageToast.show("Error loading comments");
                        resolve();
                    }
                });
            });
        },
        /*------------------ _loadWorkflowSteps--------------------*/
        _loadWorkflowSteps: function (sGuid) {
            var oModel = this.getView().getModel("offboardingModel");
            var oSelectedModel = this.getView().getModel("selectedRequest");
            return new Promise(function (resolve) {
                if (!oModel || !sGuid) {
                    resolve();
                    return;
                }
                var aFilters = [new Filter("Guid", FilterOperator.EQ, sGuid)];
                oModel.read("/WorkflowStepSet", {
                    filters: aFilters,
                    success: function (oData) {
                        var oCurrentData = oSelectedModel.getData() || {};
                        oCurrentData.WorkflowStepSet = oData.results || [];
                        oSelectedModel.setData(oCurrentData);
                        resolve();
                    },
                    error: function () {
                        var oCurrentData = oSelectedModel.getData() || {};
                        oCurrentData.WorkflowStepSet = [];
                        oSelectedModel.setData(oCurrentData);
                        MessageToast.show("Error loading workflow steps");
                        resolve();
                    }
                });
            });
        },
        /*------------------ _clearSelection --------------------*/
        _clearSelection: function () {
            var oSelectedModel = this.getView().getModel("selectedRequest");
            if (oSelectedModel) {
                oSelectedModel.setData({});
            }
        },
        onUpdateRequest: function () {
            var that = this;
            var oSelectedModel = this.getView().getModel("selectedRequest");
            var oData = oSelectedModel.getData();

            if (!oData || !oData.Guid) {
                MessageBox.error("No request selected.");
                return;
            }

            var bIsClosed = oData.Closed === 'X';
            if (bIsClosed) {
                MessageBox.warning("This request is already closed and cannot be updated.");
                return;
            }

            var oDialog = new Dialog({
                title: "Update the request - " + this.formatGuidReadable(oData.Guid),
                contentWidth: "600px",
                content: [
                    new VBox({
                        items: [
                            new Label({
                                text: "Request for: " + this.formatFullName(oData.CreatorLname, oData.CreatorFname),
                                design: "Bold"
                            }).addStyleClass("sapUiTinyMarginBottom sapUiSmallMarginTop"),

                            new Title({ text: "Workflow steps", level: "H3" }).addStyleClass("sapUiSmallMarginTop"),
                            new Label({ text: "Select the step to update:" }),
                            new Select("updateStepSelect", {
                                width: "100%",
                                selectedKey: "",
                                items: [
                                    new SeparatorItem({ text: "INITIALIZATION" }),
                                    new Item({ key: "REQUEST_INIT", text: "Request Initiation" }),
                                    new SeparatorItem({ text: "SEPARATION PROCESS" }),
                                    new Item({ key: "SEP_SLWOP", text: "Separation/SLWOP Letter" }),
                                    new Item({ key: "SEP_LETTER_STAF", text: "Separation Letter Sent to Staff" }),
                                    new Item({ key: "SEP_SLWOP_OTH_PARTIES", text: "Separation/SLWOP Letter Sent to Other Parties" }),
                                    new SeparatorItem({ text: "CHECKOUT & LOGISTICS" }),
                                    new Item({ key: "CHECKOUT", text: "Checkout" }),
                                    new Item({ key: "TRAVEL", text: "Travel" }),
                                    new Item({ key: "SHIPMENT", text: "Shipment (Relocation Grant)" }),
                                    new SeparatorItem({ text: "FINANCE & ADMINISTRATION" }),
                                    new Item({ key: "SALARY_SUSPENSE", text: "Salary Suspense" }),
                                    new Item({ key: "ACTION_REC_IRIS", text: "Action Recorded in iRIS" }),
                                    new Item({ key: "PAF", text: "PAF (Personnel Action Form)" }),
                                    new SeparatorItem({ text: "FINALIZATION" }),
                                    new Item({ key: "CLOSE_REQUEST", text: "Completed" }),
                                ]
                            }),

                            new Title({ text: "Comment", level: "H3" }).addStyleClass("sapUiSmallMarginTop"),
                            new Label({ text: "Add a comment (optional):" }),
                            new TextArea("commentTextArea", {
                                width: "100%",
                                rows: 6,
                                placeholder: "Add a detailed comment for this action...",
                                growing: true,
                                growingMaxLines: 10,
                                showExceededText: true,
                                maxLength: 255
                            }),

                            new Panel({
                                headerText: "Current status of the request",
                                expandable: true,
                                expanded: false
                            })
                                .addStyleClass("sapUiSmallMarginTop")
                                .addContent(
                                    new VBox({
                                        items: [
                                            { label: "Request Init:", key: "RequestInit" },
                                            { label: "SEP SLWOP:", key: "SepSlwop" },
                                            { label: "SEP Letter Staff:", key: "Sep_Letter_Staf" },
                                            { label: "SEP SLWOP Other Parties:", key: "Sep_Slwop_Oth_Parties" },
                                            { label: "Checkout:", key: "Checkout" },
                                            { label: "Travel:", key: "Travel" },
                                            { label: "Shipment:", key: "Shipment" },
                                            { label: "Salary Suspense:", key: "SalarySuspense" },
                                            { label: "Action iRIS:", key: "Action_Rec_Iris" },
                                            { label: "PAF:", key: "Paf" }
                                        ].map(function (item) {
                                            return new HBox({
                                                alignItems: "Center",
                                                items: [
                                                    new Label({
                                                        text: item.label,
                                                        width: "180px"
                                                    }),
                                                    new CheckBox({
                                                        selected: (oData[item.key] || '').toString().toUpperCase() === 'X',
                                                        enabled: false,
                                                        layoutData: new sap.m.FlexItemData({ alignSelf: "Center" })
                                                    })
                                                ]
                                            });
                                        })
                                    })
                                )
                        ]
                    }).addStyleClass("sapUiSmallMargin")
                ],

                beginButton: new Button({
                    text: "Approve Request",
                    type: "Emphasized",
                    icon: "sap-icon://save",
                    press: function () {
                        var sStep = sap.ui.getCore().byId("updateStepSelect").getSelectedKey();
                        var sComments = sap.ui.getCore().byId("commentTextArea").getValue();
                        var bClose = sap.ui.getCore().byId("closeRequestCheckbox")?.getSelected();

                        if (!sStep) {
                            MessageBox.error("Please select a step.");
                            return;
                        }

                        // ============================================
                        // MAPPING : ClÃ©s du Select â†’ Champs OData
                        // ============================================
                        var oFieldMapping = {
                            "REQUEST_INIT": "RequestInit",
                            "SEP_SLWOP": "SepSlwop",
                            "SEP_LETTER_STAF": "Sep_Letter_Staf",
                            "SEP_SLWOP_OTH_PARTIES": "Sep_Slwop_Oth_Parties",
                            "CHECKOUT": "Checkout",
                            "TRAVEL": "Travel",
                            "SHIPMENT": "Shipment",
                            "SALARY_SUSPENSE": "SalarySuspense",
                            "ACTION_REC_IRIS": "Action_Rec_Iris",
                            "PAF": "Paf"
                        };

                        // RÃ©cupÃ©rer le champ OData correspondant
                        var sODataField = oFieldMapping[sStep];
                        console.log("ðŸ” VÃ©rification Ã©tape avant validation:");
                        console.log("   Step sÃ©lectionnÃ©:", sStep);
                        console.log("   Champ OData:", sODataField);
                        console.log("   Valeur actuelle:", oData[sODataField]);

                        // VÃ©rification robuste
                        var bAlreadyValidated = (oData[sODataField] && oData[sODataField].toString().trim().toUpperCase() === 'X');
                        if (sStep !== 'CLOSE_REQUEST' && sODataField && bAlreadyValidated) {
                            MessageBox.warning(
                                "âš ï¸ This step (" + sStep + ") has already been approved.\n\n" +
                                "You cannot validate the same step twice.\n\n" +
                                "Please select another step or just add a comment.",
                                { title: "Step Already Approved" }
                            );
                            console.log("âŒ Validation bloquÃ©e - Ã‰tape dÃ©jÃ  approuvÃ©e");
                            return;
                        }

                        console.log("âœ… VÃ©rification OK - Ã‰tape non validÃ©e, on continue");

                        // ============================================
                        // CONFIRMATION pour fermeture
                        // ============================================
                        if (sStep === 'CLOSE_REQUEST' || bClose) {
                            MessageBox.confirm(
                                "You are about to close this request. Do you confirm this action?",
                                {
                                    title: "Close Confirmation",
                                    onClose: function (oAction) {
                                        if (oAction === MessageBox.Action.OK) {
                                            that._performUpdate(oDialog, oData, sStep, sComments, bClose);
                                        }
                                    }
                                }
                            );
                        } else {
                            // ============================================
                            // SINON : ProcÃ©der Ã  la mise Ã  jour
                            // ============================================
                            that._performUpdate(oDialog, oData, sStep, sComments, bClose);
                        }
                    }
                }),

                endButton: new Button({
                    text: "Cancel",
                    icon: "sap-icon://decline",
                    press: function () {
                        oDialog.close();
                    }
                }),

                afterClose: function () {
                    oDialog.destroy();
                }
            });

            oDialog.open();
        },

        _performUpdate: function (oDialog, oData, sStep, sComments, bClose) {
            var that = this;
            var oModel = this.getView().getModel("offboardingModel");

            if (!oModel || !oData || !oData.Guid) {
                MessageBox.error("Unable to update: missing GUID or OData model not found.");
                return;
            }

            // ðŸ”¹ Get current user PERNR
            var sCurrentPernr = "00000000";
            try {
                if (sap.ushell && sap.ushell.Container) {
                    var oUserInfo = sap.ushell.Container.getService("UserInfo").getUser();
                    sCurrentPernr = oUserInfo.getEmployeeNumber && oUserInfo.getEmployeeNumber() ||
                        oUserInfo.getProperty && oUserInfo.getProperty("PERNR") ||
                        oUserInfo.getId && oUserInfo.getId() ||
                        "00000000";
                }
            } catch (e) {
                // ignore if UShell not available
            }

            if (sCurrentPernr && sCurrentPernr !== "00000000") {
                sCurrentPernr = ("00000000" + sCurrentPernr).slice(-8);
            }

            // ðŸ”¹ Valid fields (SANS ValidationType et ExecMode)
            var aValidFields = [
                "CreatorPernr", "CreatorLname", "CreatorFname",
                "Reason", "ActionType", "EffectiveDate", "Endda",
                "RequestInit", "SepSlwop", "Checkout", "Travel", "Shipment",
                "SalarySuspense", "Closed", "UpdPernr", "UpdLname", "UpdFname",
                "Seqno", "Comments", "Status", "ContractType",
                "Persg", "Year", "Month", "EmployeeName", "Date_approval",
                "Sep_Letter_Staf", "Sep_Slwop_Oth_Parties", "Action_Rec_Iris", "Paf"
            ];

            var aDateFields = ["EffectiveDate", "Endda", "Date_approval"];
            var oUpdateData = {};

            // ðŸ”¹ Copy allowed fields and format dates
            aValidFields.forEach(function (sField) {
                if (oData.hasOwnProperty(sField)) {
                    var value = oData[sField];
                    if (value === undefined || value === null || value === '') return;

                    if (aDateFields.indexOf(sField) > -1 && /^\d{8}$/.test(value)) {
                        var year = value.substring(0, 4);
                        var month = value.substring(4, 6);
                        var day = value.substring(6, 8);
                        oUpdateData[sField] = year + '-' + month + '-' + day;
                    } else {
                        oUpdateData[sField] = value;
                    }
                }
            });

            // ðŸ”¹ Add update info
            oUpdateData.UpdPernr = sCurrentPernr;

            // âŒ SUPPRIMÃ‰ : Ne pas envoyer ValidationType et ExecMode
            // Ces champs sont gÃ©rÃ©s automatiquement par le backend dans zthrfiori_dapprv

            // ðŸ”¹ Field mapping for step checkboxes
            var oFieldMapping = {
                "REQUEST_INIT": "RequestInit",
                "SEP_SLWOP": "SepSlwop",
                "SEP_LETTER_STAF": "Sep_Letter_Staf",
                "SEP_SLWOP_OTH_PARTIES": "Sep_Slwop_Oth_Parties",
                "CHECKOUT": "Checkout",
                "TRAVEL": "Travel",
                "SHIPMENT": "Shipment",
                "SALARY_SUSPENSE": "SalarySuspense",
                "ACTION_REC_IRIS": "Action_Rec_Iris",
                "PAF": "Paf"
            };

            // ðŸ”¹ Comments
            var sFinalComments = sStep;
            if (sComments && sComments.trim()) {
                sFinalComments += " " + sComments.trim();
            }
            oUpdateData.Comments = sFinalComments;

            // ðŸ”¹ Step handling
            if (sStep && sStep !== 'COMMENT_ONLY' && sStep !== 'CLOSE_REQUEST') {
                var sODataField = oFieldMapping[sStep];
                if (sODataField) {
                    oUpdateData[sODataField] = 'X';
                }
            }

            // ðŸ”¹ Handle close request
            if (bClose || sStep === 'CLOSE_REQUEST') {
                oUpdateData.Closed = 'X';
            }

            // ðŸ”¹ Default action type
            if (!oUpdateData.ActionType) {
                oUpdateData.ActionType = '01';
            }

            console.log("ðŸ“¤ DonnÃ©es envoyÃ©es au backend:", JSON.stringify(oUpdateData, null, 2));

            // ðŸ”¹ Backend call
            var sGuidHex = this._convertGuidToHexWithoutDashes(oData.Guid);
            var sPath = "/RequestSet(Guid='" + sGuidHex + "')";

            that.getView().setBusy(true);

            oModel.update(sPath, oUpdateData, {
                method: "MERGE",
                headers: { "If-Match": "*" },
                success: function () {
                    that.getView().setBusy(false);
                    MessageToast.show("Request updated successfully!");
                    oDialog.close();
                    that._loadRequestByGuidOData(sGuidHex);
                },
                error: function (oError) {
                    that.getView().setBusy(false);

                    var sErrorMsg = "Update failed.";
                    var sErrorCode = "";
                    var aErrorDetails = [];

                    try {
                        var oErr = JSON.parse(oError.responseText);

                        if (oErr.error && oErr.error.message && oErr.error.message.value) {
                            sErrorMsg = oErr.error.message.value;
                        }

                        if (oErr.error && oErr.error.code) {
                            sErrorCode = oErr.error.code;
                        }

                        if (oErr.error.innererror) {
                            var inner = oErr.error.innererror;
                            if (inner.message) sErrorMsg = inner.message;

                            if (inner.errordetails && Array.isArray(inner.errordetails)) {
                                inner.errordetails.forEach(function (detail) {
                                    aErrorDetails.push(detail.code + ": " + detail.message);
                                });
                            }
                        }

                        var sLowerMsg = (sErrorMsg || '').toLowerCase();
                        if (sErrorCode === "ERROR_STEP_ALREADY_VALIDATED" ||
                            sLowerMsg.includes("error_step_already_validated")) {
                            MessageBox.error(
                                "âš ï¸ This step has already been validated.\n\n" +
                                "You cannot validate the same step twice.\n\n" +
                                "Please select another step or simply add a comment.",
                                { title: "Step already validated" }
                            );
                            oDialog.close();
                            return;
                        }
                    } catch (e) {
                        // Ignore JSON parse errors
                    }

                    var sDetailedMsg = sErrorMsg;
                    if (aErrorDetails.length > 0) {
                        sDetailedMsg += "\n\nDetails:\n" + aErrorDetails.join("\n");
                    }
                    if (sErrorCode) {
                        sDetailedMsg += "\n\nError code: " + sErrorCode;
                    }

                    MessageBox.error(sDetailedMsg, {
                        title: "Update Error",
                        details: oError.responseText
                    });
                }
            });
        },
       onOpenDocument: function (oEvent) {
            var oContext = oEvent.getSource().getBindingContext("selectedRequest");
            if (!oContext) {
                MessageBox.error("Impossible de rÃ©cupÃ©rer les informations du document.");
                return;
            }

            var oDocData = oContext.getObject();
            var sDocId = oDocData.ArchiveDocId;
            var sFileName = oDocData.FILENAME || "Document.pdf";

            if (!sDocId) {
                MessageBox.error("Aucun identifiant de document (ArchiveDocId) trouvÃ©.");
                return;
            }

            var sUrl = "/sap/opu/odata/sap/ZARCHIVE_SRV/DocumentSet('" + encodeURIComponent(sDocId) + "')/$value";
            window.open(sUrl, "_blank");
        },

        onDownloadDocument: function (oEvent) {
            const oContext = oEvent.getSource().getBindingContext("selectedRequest");
            const oDocument = oContext.getObject();

            if (!oDocument || !oDocument.ArchiveDocId) {
                MessageBox.error("Document ID is missing");
                return;
            }

            sap.ui.core.BusyIndicator.show(0);

            try {
                const sServiceUrl = this.getView().getModel().sServiceUrl;
                const sDocUrl = `${sServiceUrl}/TOAATSet(ArchiveDocId='${oDocument.ArchiveDocId}')/$value`;

                // CrÃ©er un lien temporaire pour forcer le tÃ©lÃ©chargement
                const link = document.createElement('a');
                link.href = sDocUrl;
                link.download = `${oDocument.Filename}.${oDocument.Fileext}`;
                link.target = '_blank';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

                MessageToast.show(`Download started: ${oDocument.Filename}`);
            } catch (error) {
                MessageBox.error("Error downloading document: " + error.message);
            } finally {
                sap.ui.core.BusyIndicator.hide();
            }
        },
        onDeleteDocument: function (oEvent) {
            MessageBox.warning("FonctionnalitÃ© de suppression Ã  implÃ©menter");
        },
        onNavToUpload: function () {
            var sGuid = this._sCurrentRequestId;
            if (!sGuid) {
                MessageBox.warning("Aucune demande sÃ©lectionnÃ©e !");
                return;
            }
            var sEncodedGuid = encodeURIComponent(sGuid);
            var oRouter = UIComponent.getRouterFor(this);
            if (!oRouter) {
                MessageBox.error("Erreur : Router non disponible");
                return;
            }
            try {
                oRouter.navTo("RouteUpload", { RequestId: sEncodedGuid }, false);
            } catch (e) {
                console.error("Erreur lors de la navigation:", e);
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
                oRouter.navTo("RouteMain", {}, true);
            }
        },
        formatFullName: function (sLastName, sFirstName) {
            return [sFirstName, sLastName].filter(Boolean).join(" ");
        },
        /*------------------ formatRequestStatus (CORRIGÃ‰) --------------------*/
        formatRequestStatus: function (
            sClosed, sRequestInit, sSepSlwop, sSepLetterStaf,
            sSepSlwopOth, sCheckout, sTravel, sShipment,
            sSalarySuspense, sActionRecIris, sPaf
        ) {
            // ðŸ”¹ Fonction helper pour vÃ©rifier si une valeur est "cochÃ©e" ('X', '1', 'TRUE')
            var isChecked = function (value) {
                // Retourne false pour null, undefined, 0, "", false
                if (!value) return false;

                // Convertit en string, retire les espaces et met en majuscules pour comparaison
                var sValue = String(value).trim().toUpperCase();

                return sValue === 'X' || sValue === '1' || sValue === 'TRUE';
            };

            // --- DÃ©bogage (laissez-le pour vos tests) ---
            console.log("ðŸ” formatRequestStatus - Valeurs reÃ§ues:", {
                sClosed: sClosed + " (" + typeof sClosed + ")",
                sRequestInit: sRequestInit + " (" + typeof sRequestInit + ")",
                // ... (autres logs si nÃ©cessaire)
            });
            // ----------------------------------------------


            // ðŸ”¹ 1. VÃ©rifier si la demande est FERMÃ‰E (Completed) - PrioritÃ© la plus haute
            if (isChecked(sClosed)) {
                console.log("âœ… Statut = Completed (Closed = X)");
                return "Completed";
            }

            // ðŸ”¹ 2. VÃ©rifier si au moins une Ã©tape est validÃ©e (In Progress)
            var aSteps = [
                sRequestInit, sSepSlwop, sSepLetterStaf,
                sSepSlwopOth, sCheckout, sTravel, sShipment,
                sSalarySuspense, sActionRecIris, sPaf
            ];

            // Utilise 'some' pour vÃ©rifier si au moins un Ã©lÃ©ment est 'checked'
            var bHasAnyStep = aSteps.some(function (step) {
                return isChecked(step); // Utilise la fonction helper pour chaque Ã©tape
            });

            if (bHasAnyStep) {
                console.log("âœ… Statut = In Progress (au moins une Ã©tape cochÃ©e)");
                return "In Progress";
            }

            // ðŸ”¹ 3. Sinon, la demande est AnnulÃ©e (Cancelled) - Cas par dÃ©faut
            // (ArrivÃ© ici, sClosed est false ET toutes les Ã©tapes sont false)
            console.log("âœ… Statut = Cancelled (aucune Ã©tape cochÃ©e et non fermÃ©)");
            return "Cancelled";
        },

        /*------------------ formatRequestStatusState (CORRIGÃ‰) --------------------*/
        /**
         * Convertit le statut textuel en un code de couleur pour l'interface utilisateur.
         * Note: Cette fonction suppose qu'elle est appelÃ©e dans un contexte oÃ¹ "this"
         * est l'objet contenant les deux fonctions.
         */
        formatRequestStatusState: function (
            sClosed, sRequestInit, sSepSlwop, sSepLetterStaf,
            sSepSlwopOth, sCheckout, sTravel, sShipment,
            sSalarySuspense, sActionRecIris, sPaf
        ) {
            // Appel de la premiÃ¨re fonction pour obtenir le statut
            // S'assurer que 'this' est correctement liÃ© si le code est dans un objet
            var sStatus = this.formatRequestStatus(
                sClosed, sRequestInit, sSepSlwop, sSepLetterStaf,
                sSepSlwopOth, sCheckout, sTravel, sShipment,
                sSalarySuspense, sActionRecIris, sPaf
            );

            // Retourne le code de couleur (State) correspondant au statut (Status)
            switch (sStatus) {
                case "Completed":
                    return "Success";    // vert
                case "In Progress":
                    return "Warning";    // orange
                case "Cancelled":
                    return "Error";      // rouge
                default:
                    return "None";       // couleur par dÃ©faut si statut inconnu
            }
        },


        formatCompletedStatus: function (sCompleted) {
            console.log("formatCompletedStatus appelÃ© avec:", sCompleted, "Type:", typeof sCompleted);

            if (!sCompleted) return false;

            var sValue = String(sCompleted).trim().toUpperCase();
            return sValue === "X" || sValue === "1" || sValue === "TRUE";
        },
        formatGuidReadable: function (sGuidInput) {
            if (!sGuidInput) return "N/A";

            try {
                // Normalize first
                var sNormalized = this._normalizeGuid(sGuidInput);
               
                return sNormalized;
            } catch (e) {
                console.error("formatGuidReadable ERROR:", e);
                return String(sGuidInput).substring(0, 32);
            }
        },
        _convertGuidToHexWithoutDashes: function (sGuid) {
            if (!sGuid) return "";

            if (sGuid.indexOf('-') > -1) {
                return sGuid.replace(/-/g, '').toUpperCase();
            }
            if (sGuid.length === 32 && /^[0-9A-Fa-f]+$/.test(sGuid)) {
                return sGuid.toUpperCase();
            }
            try {
                var binary = atob(sGuid);
                var hex = Array.from(binary)
                    .map(function (c) {
                        return ('0' + c.charCodeAt(0).toString(16)).slice(-2);
                    })
                    .join('')
                    .toUpperCase();
                return hex.substring(0, 32);
            } catch (e) {
                console.error("Erreur conversion GUID Base64 â†’ Hex:", e);
                return sGuid.toUpperCase().substring(0, 32);
            }
        },
        getDocumentType: function (sDocumentName) {
            // if (!sDocumentName) return "Unknown";
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
        formatDateApproval: function (sDateStr) {
            if (!sDateStr || sDateStr.length !== 8) return "";
            var year = sDateStr.substring(0, 4);
            var month = sDateStr.substring(4, 6);
            var day = sDateStr.substring(6, 8);
            return day + "-" + month + "-" + year;
        },
        formatDateTime: function (date, time) {
            if (!date) return "";
            const d = new Date(date);
            if (time) {
                const h = time.substring(0, 2);
                const m = time.substring(2, 4);
                const s = time.substring(4, 6);
                d.setHours(h, m, s);
            }
            return sap.ui.core.format.DateFormat.getDateTimeInstance({
                pattern: "dd/MM/yyyy HH:mm"
            }).format(d);
        },
        formatFileSize: function (size) {
            if (!size) return "";
            const kb = parseInt(size, 10) / 1024;
            if (kb < 1024) return kb.toFixed(1) + " KB";
            const mb = kb / 1024;
            return mb.toFixed(1) + " MB";
        }
    });
});