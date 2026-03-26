sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/ui/core/UIComponent",
    "sap/m/MessageBox",
    "sap/m/MessageToast",
    "sap/ui/unified/FileUploaderParameter",
    "sap/ui/core/routing/History",
    "sap/ui/model/json/JSONModel",
    "sap/ui/model/Filter",
    "sap/ui/model/FilterOperator"
], function (Controller, UIComponent, MessageBox, MessageToast, FileUploaderParameter, History, JSONModel, Filter, FilterOperator) {
    "use strict";

    return Controller.extend("com.hr.unesco.yhrappoffboardingemp.controller.Upload", {

        // ================== INITIALIZATION ==================

        onInit: function () {
            this._uploadedFiles = { file1: false, file2: false, file3: false, file4: false };
            this._csrfToken = null;
            this._requestId = null;

            var oComponent = this.getOwnerComponent();
            this.oModel = oComponent ? oComponent.getModel("offboardingModel") : null;

            if (!this.oModel) {
                MessageBox.error("OData Model not found!");
                return;
            }
            
            var oDocumentsModel = new JSONModel();
            this.getView().setModel(oDocumentsModel, "selectedRequest");

            var oRouter = UIComponent.getRouterFor(this);
            if (oRouter) {
                oRouter.getRoute("RouteUpload").attachPatternMatched(this._onObjectMatched, this);
            }

            this._fetchCSRFToken();
        },

        _onObjectMatched: function (oEvent) {
            var oArgs = oEvent.getParameter("arguments");
            this._requestId = oArgs ? decodeURIComponent(oArgs.RequestId) : null;
            
            var oBundle = this.getOwnerComponent().getModel("i18n").getResourceBundle();

            if (!this._requestId) {
                MessageBox.error("Request ID missing in URL!");
                return;
            }
			
			var sMsg = oBundle.getText("UploadForReqId", [this._requestId]);
			MessageToast.show(sMsg);
            //MessageToast.show("Upload for RequestID: " + this._requestId);
            this._loadOffboardingLinks(this._requestId);
            this._loadDocuments();
        },
        _loadOffboardingLinks: function (sGuid) {
		    const oModel = this.getView().getModel("offboardingModel");
		    const oSelectedModel = this.getView().getModel("selectedRequest");
		    var oBundle = this.getOwnerComponent().getModel("i18n").getResourceBundle();

		    if (!oModel || !sGuid) return Promise.resolve();
		    this.getView().setBusy(true);
		
		    return new Promise((resolve) => {
		        const aFilters = [new sap.ui.model.Filter("Guid", sap.ui.model.FilterOperator.EQ, sGuid)];
		
		        oModel.read("/DocumentLinkSet", {
		            filters: aFilters,
		            success: function (oData) {
		                const aLinks = (oData.results || []).filter(link => !!link.Link).map(link => ({
		                    DocumentName: link.DocTxt || "",
		                    Url: link.Link || "",
		                    Id: link.IdLink || "",
		                    LinkTxt: link.LinkTxt || "",
		                    ActionType: link.ActionType || ""
		                }));
		                
						if (aLinks[1].ActionType === "01"){
							this.getView().byId("invitation").setVisible(true);
						}else{
							this.getView().byId("invitation").setVisible(false);
						}
						
		                const oCurrentData = oSelectedModel.getData() || {};
		                oCurrentData.DocumentLinks = aLinks;
		                oSelectedModel.setData(oCurrentData);
		
		                resolve();
		                this.getView().setBusy(false);
		            }.bind(this),
		            error: function () {
		                const oCurrentData = oSelectedModel.getData() || {};
		                oCurrentData.DocumentLinks = [];
		                oSelectedModel.setData(oCurrentData);
						
						var sMsg = oBundle.getText("ErrorLoadingDocumentLeave");
						sap.m.MessageToast.show(sMsg);
		                //sap.m.MessageToast.show("Erreur lors du chargement des documents de sortie");
		                resolve();
		                this.getView().setBusy(false);
		            }.bind(this)
		        });
		    });
		},

        // ================== DOCUMENT MANAGEMENT ==================
		_loadDocuments: function () {
		    const that = this;
		
		    if (!this._requestId) {
		        return;
		    }
		
		    const sRequestIdClean = this._requestId.replace(/-/g, "").toUpperCase();
		    const sDocPath = "/TOAATSet";
		    const sVisibilityPath = "/DocumentToUploadSet";
		    const aDocFilters = [new Filter("REQUEST_ID", FilterOperator.EQ, sRequestIdClean)];
		    const aVisibilityFilters = [new Filter("Guid", FilterOperator.EQ, sRequestIdClean)];
		
		    this.getView().setBusy(true);
		
		    // Step 1: Fetch visible document types
		    this.oModel.read(sVisibilityPath, {
		        filters: aVisibilityFilters,
		        success: function (oVisibilityData) {
		            const aVisibleTypes = (oVisibilityData.results || [])
		                .filter(v => v.Visible === true)
		                .map(v => v.Doc_Type);

				    const oReqDocModel = that.getView().getModel("selectedRequest");
		            oReqDocModel.setProperty("/RequiredDocuments", oVisibilityData.results);

		            // ðŸ”¹ Control Required Documents tab visibility
		            const oRequiredTab = that.byId("requiredDocsTab");
		            if (oRequiredTab) {
		                const bTabVisible = aVisibleTypes.length > 0;
		                oRequiredTab.setVisible(bTabVisible);
		                jQuery.sap.log.info("Required Documents tab visibility set to: " + bTabVisible);
		            }
		
		            // ðŸ”¹ Control individual rows visibility
		            //that._updateRequiredRowsVisibility(aVisibleTypes);
		
		            // Step 2: Fetch actual documents
		            that.oModel.read(sDocPath, {
		                filters: aDocFilters,
		                success: function (oData) {
		                    const results = (oData.results || [])
		                        .filter(function (item) {
		                            return aVisibleTypes.includes(item.AttachType);
		                        })
		                        .map(function (item) {
		                            return {
		                                REQUEST_ID: item.REQUEST_ID || sRequestIdClean,
		                                AttachType: item.AttachType || "",
		                                IncNb: item.IncNb || "",
		                                ArchiveDocId: item.ArchiveDocId || "",
		                                AttachTypeTxt: item.AttachTypeTxt || "",
		                                Filename: item.Filename || "Document.pdf",
		                                Fileext: item.Fileext || "",
		                                Filesize: item.Filesize || 0,
		                                MimeType: item.MimeType || "application/pdf",
		                                CreatorFname: item.CreatorFname || "",
		                                CreatorLname: item.CreatorLname || "",
		                                CreatorPernr: item.CreatorPernr || "",
		                                CreationDate: item.CreationDate || "",
		                                CreationTime: item.CreationTime || "",
		                                LastUpdDate: item.LastUpdDate || "",
		                                LastUpdTime: item.LastUpdTime || "",
		                                UpdFname: item.UpdFname || "",
		                                UpdLname: item.UpdLname || ""
		                            };
		                        });
		
		                    const oDocModel = that.getView().getModel("selectedRequest");
		                    oDocModel.setProperty("/Documents", results);
		                    that.getView().setBusy(false);
		
		                    that._updateUploadStatus(results);
		                    
		                    var oBundle = that.getOwnerComponent().getModel("i18n").getResourceBundle();
		                    var sMsg;
		
		                    if (results.length === 0) {
		                    	sMsg = oBundle.getText("NoVisibleDocumentForRequest");
		                    	MessageToast.show(sMsg);
		                        //MessageToast.show("No visible documents found for this request");
		                    } else {
		                    	sMsg = oBundle.getText("NbVisibleDocLoaded", [results.length]);
		                    	MessageToast.show(sMsg);
		                        //MessageToast.show(results.length + " visible document(s) loaded");
		                    }
		                },
		                error: function (oError) {
		                    that.getView().setBusy(false);
		                    const sErrorMsg = that._extractODataError(oError);
		                    MessageBox.error("Unable to load documents: " + sErrorMsg);
		                }
		            });
		        },
		        error: function () {
		            that.getView().setBusy(false);
		            MessageBox.error("Unable to load document visibility settings");
		        }
		    });
		},
		_updateRequiredRowsVisibility: function (aVisibleTypes) {
			
		    // const mapping = [
		    //     { rowId: "rowSeparationLetter",   docType: "SEP_LETTER" },
		    //     { rowId: "rowRepatriationTravel", docType: "REPAT_TRAVEL" },
		    //     { rowId: "rowExitQuestionnaire",  docType: "EXIT_QUEST" },
		    //     { rowId: "rowRepatriationShipment", docType: "REPAT_SHIP" }
		    // ];
		
		    // mapping.forEach(m => {
		    //     const bVisible = aVisibleTypes.includes(m.docType);
		    //     const oRow = this.byId(m.rowId);
		    //     if (oRow) {
		    //         oRow.setVisible(bVisible);
		    //         jQuery.sap.log.info("Row " + m.rowId + " (" + m.docType + ") visible: " + bVisible);
		    //     }
		    // });
		},




        // _loadDocuments: function () {
        // 	debugger;
        //     var that = this;

        //     if (!this._requestId) {
        //         return;
        //     }

        //     var sRequestIdClean = this._requestId.replace(/-/g, "").toUpperCase();
        //     var sPath = "/TOAATSet";
        //     var aFilters = [
        //         new Filter("REQUEST_ID", FilterOperator.EQ, sRequestIdClean)
        //     ];

        //     this.getView().setBusy(true);

        //     this.oModel.read(sPath, {
        //         filters: aFilters,
        //         success: function (oData) {
        //             var results = oData.results.map(function (item) {
        //                 return {
        //                     REQUEST_ID: item.REQUEST_ID || sRequestIdClean,
        //                     AttachType: item.AttachType || "",
        //                     IncNb: item.IncNb || "",
        //                     ArchiveDocId: item.ArchiveDocId || "",
        //                     AttachTypeTxt: item.AttachTypeTxt || "",
        //                     Filename: item.Filename || "Document.pdf",
        //                     Fileext: item.Fileext || "",
        //                     Filesize: item.Filesize || 0,
        //                     MimeType: item.MimeType || "application/pdf",
        //                     CreatorFname: item.CreatorFname || "",
        //                     CreatorLname: item.CreatorLname || "",
        //                     CreatorPernr: item.CreatorPernr || "",
        //                     CreationDate: item.CreationDate || "",
        //                     CreationTime: item.CreationTime || "",
        //                     LastUpdDate: item.LastUpdDate || "",
        //                     LastUpdTime: item.LastUpdTime || "",
        //                     UpdFname: item.UpdFname || "",
        //                     UpdLname: item.UpdLname || ""
        //                 };
        //             });

        //             var oDocModel = that.getView().getModel("selectedRequest");
        //             oDocModel.setProperty("/Documents", results);
        //             that.getView().setBusy(false);

        //             // Mettre Ã  jour les statuts des fichiers uploadÃ©s
        //             that._updateUploadStatus(results);

        //             if (!oData.results || oData.results.length === 0) {
        //                 MessageToast.show("No documents found for this request");
        //             } else {
        //                 MessageToast.show(oData.results.length + " document(s) loaded");
        //             }
        //         },
        //         error: function (oError) {
        //             that.getView().setBusy(false);
        //             var sErrorMsg = that._extractODataError(oError);
        //             MessageBox.error("Unable to load documents: " + sErrorMsg);
        //         }
        //     });
        // },

        /**
         * _updateUploadStatus - Met Ã  jour les statuts d'upload dans l'interface
         */
  //       _updateUploadStatus: function(aDocuments) {
		//     var that = this;
		//     var oBundle = this.getView().getModel("i18n").getResourceBundle();
		
		//     var mapping = {
		//         "SEP_LETTER": { statusId: "statusText1", fileId: "file1" },
		//         "REPAT_TRAVEL": { statusId: "statusText2", fileId: "file2" },
		//         "EXIT_QUEST": { statusId: "statusText3", fileId: "file3" },
		//         "REPAT_SHIP": { statusId: "statusText4", fileId: "file4" }
		//     };
		
		//     // Reset all statuses
		//     Object.keys(mapping).forEach(function(key) {
		//         var oStatus = that.byId(mapping[key].statusId);
		//         if (oStatus) {
		//             oStatus.setText(oBundle.getText("uploadStatusNoFile"));
		//             oStatus.removeStyleClass("sapUiSuccessText");
		//             oStatus.removeStyleClass("sapUiErrorText");
		//         }
		//         that._uploadedFiles[mapping[key].fileId] = false;
		//     });
		
		//     // Mark existing documents
		//     aDocuments.forEach(function(doc) {
		//     	console.log("Checking doc.AttachType:", doc.AttachType);
		//         var mapEntry = mapping[doc.AttachType];
		//         if (mapEntry) {
		//             var oStatus = that.byId(mapEntry.statusId);
		//             if (oStatus) {
		//                 oStatus.setText(oBundle.getText("uploadStatusFileUploaded", [doc.Filename]));
		//                 oStatus.addStyleClass("sapUiSuccessText");
		//             }
		//             that._uploadedFiles[mapEntry.fileId] = true;
		//         } else {
		// 	        console.warn("No mapping found for AttachType:", doc.AttachType);
		// 	    }
		//     });
		// },
		// _updateUploadStatus: function(aDocuments) {
		//     var that = this;
		//     var oBundle = this.getView().getModel("i18n").getResourceBundle();
		
		//     var mapping = {
		//         "SEP_LETTER": { statusId: "statusText1", fileId: "file1" },
		//         "REPAT_TRAVEL": { statusId: "statusText2", fileId: "file2" },
		//         "EXIT_QUEST": { statusId: "statusText3", fileId: "file3" },
		//         "REPAT_SHIP": { statusId: "statusText4", fileId: "file4" }
		//     };
		
		//     // Reset all statuses
		//     Object.keys(mapping).forEach(function(key) {
		//         var mapEntry = mapping[key];
		//         var oStatus = that.byId(mapEntry.statusId);
		//         console.log(`[RESET] ${key} â†’ ${mapEntry.statusId}`, !!oStatus ? "âœ… Found" : "âŒ Not found");
		//         if (oStatus) {
		//             oStatus.setText(oBundle.getText("uploadStatusNoFile"));
		//             oStatus.removeStyleClass("sapUiSuccessText");
		//             oStatus.removeStyleClass("sapUiErrorText");
		//         }
		//         that._uploadedFiles[mapEntry.fileId] = false;
		//     });
		
		//     // Mark existing documents
		//     aDocuments.forEach(function(doc) {
		//         console.log(`[UPDATE] Checking doc.AttachType: ${doc.AttachType}`);
		//         var mapEntry = mapping[doc.AttachType];
		//         if (mapEntry) {
		//             var oStatus = that.byId(mapEntry.statusId);
		//             console.log(`[UPDATE] ${doc.AttachType} â†’ ${mapEntry.statusId}`, !!oStatus ? "âœ… Found" : "âŒ Not found");
		//             if (oStatus) {
		//                 var statusText = oBundle.getText("uploadStatusFileUploaded", [doc.Filename]);
		//                 console.log(`[UPDATE] Setting status text: "${statusText}"`);
		//                 oStatus.setText(statusText);
		//                 oStatus.addStyleClass("sapUiSuccessText");
		//             }
		//             that._uploadedFiles[mapEntry.fileId] = true;
		//         } else {
		//             console.warn(`[WARN] No mapping found for AttachType: ${doc.AttachType}`);
		//         }
		//     });
		// },
		_updateUploadStatus: function(aDocuments) {
		    var that = this;
		    var oBundle = this.getView().getModel("i18n").getResourceBundle();
		

		},

        // _updateUploadStatus: function(aDocuments) {
        //     var that = this;
        //     var mapping = {
        //         "SEP_LETTER": { statusId: "statusText1", fileId: "file1" },
        //         "REPAT_TRAVEL": { statusId: "statusText2", fileId: "file2" },
        //         "EXIT_QUEST": { statusId: "statusText3", fileId: "file3" },
        //         "REPAT_SHIP": { statusId: "statusText4", fileId: "file4" }
        //     };

        //     // RÃ©initialiser tous les statuts
        //     Object.keys(mapping).forEach(function(key) {
        //         var oStatus = that.byId(mapping[key].statusId);
        //         if (oStatus) {
        //             oStatus.setText("No file uploaded");
        //             oStatus.removeStyleClass("sapUiSuccessText");
        //             oStatus.removeStyleClass("sapUiErrorText");
        //         }
        //         that._uploadedFiles[mapping[key].fileId] = false;
        //     });

        //     // Marquer les documents existants
        //     aDocuments.forEach(function(doc) {
        //         var mapEntry = mapping[doc.AttachType];
        //         if (mapEntry) {
        //             var oStatus = that.byId(mapEntry.statusId);
        //             if (oStatus) {
        //                 oStatus.setText("File uploaded: " + doc.Filename);
        //                 oStatus.addStyleClass("sapUiSuccessText");
        //             }
        //             that._uploadedFiles[mapEntry.fileId] = true;
        //         }
        //     });
        // },

        _extractODataError: function (oError) {
            try {
                if (oError.responseText) {
                    var oErrorResponse = JSON.parse(oError.responseText);
                    if (oErrorResponse.error && oErrorResponse.error.message) {
                        return oErrorResponse.error.message.value || oErrorResponse.error.message;
                    }
                }
                return oError.message || "Unknown error";
            } catch (e) {
                return oError.message || "Unknown error";
            }
        },

        // ================== FORMATTERS ==================

        formatFileTypeState: function (sFileType) {
            if (!sFileType) return "None";
            var typeMap = {
                "PDF": "Success",
                "DOC": "Information",
                "DOCX": "Information",
                "XLS": "Warning",
                "XLSX": "Warning",
                "PPT": "Error",
                "PPTX": "Error",
                "IMG": "Success",
                "TXT": "None"
            };
            return typeMap[sFileType.toUpperCase()] || "None";
        },

        formatFileSize: function (iSize) {
            if (!iSize || iSize === 0) return "0 B";
            var units = ["B", "KB", "MB", "GB"];
            var size = parseInt(iSize);
            var unitIndex = 0;
            while (size >= 1024 && unitIndex < units.length - 1) {
                size = size / 1024;
                unitIndex++;
            }
            return size.toFixed(2) + " " + units[unitIndex];
        },

        formatFullName: function (sFirstName, sLastName) {
            if (!sFirstName && !sLastName) return "";
            if (!sFirstName) return sLastName;
            if (!sLastName) return sFirstName;
            return sFirstName + " " + sLastName;
        },

        formatCreator: function (sFname, sLname, sPernr) {
            var name = [sFname, sLname].filter(Boolean).join(" ");
            if (name && sPernr) {
                return name + " (" + sPernr + ")";
            }
            return name || sPernr || "";
        },

        formatDate: function (sDate) {
            if (!sDate) return "";
            if (typeof sDate === "string" && sDate.length === 8) {
                var year = sDate.substring(0, 4);
                var month = sDate.substring(4, 6);
                var day = sDate.substring(6, 8);
                return day + "/" + month + "/" + year;
            }
            if (sDate instanceof Date) {
                var day = String(sDate.getDate()).padStart(2, '0');
                var month = String(sDate.getMonth() + 1).padStart(2, '0');
                var year = sDate.getFullYear();
                return day + "/" + month + "/" + year;
            }
            return sDate;
        },
        formatDateTime: function (sDate, sTime) {
		    if (!sDate) return "";
		    try {
		        var year = sDate.substring(0, 4);
		        var month = sDate.substring(4, 6);
		        var day = sDate.substring(6, 8);
		        return day + "/" + month + "/" + year;
		    } catch (e) {
		        return "";
		    }
		},


        // formatDateTime: function (sDate, sTime) {
        //     if (!sDate || !sTime) return "";
        //     try {
        //         var year = sDate.substring(0, 4);
        //         var month = sDate.substring(4, 6);
        //         var day = sDate.substring(6, 8);
        //         var hour = sTime.substring(0, 2);
        //         var minute = sTime.substring(2, 4);
        //         var second = sTime.substring(4, 6);
        //         return day + "/" + month + "/" + year + " " + hour + ":" + minute + ":" + second;
        //     } catch (e) {
        //         return "";
        //     }
        // },

        // formatLastUpdate: function (sDate, sTime, sFName, sLName) {
        //     if (!sDate || !sTime) return "";
        //     const dateStr = this.formatDateTime(sDate, sTime);
        //     const userStr = [sFName, sLName].filter(Boolean).join(" ");
        //     if (userStr) {
        //         return dateStr + userStr;
        //     }
        //     return dateStr;
        // },
        formatLastUpdate: function (sDate, sTime, sFName, sLName) {
		    if (!sDate || !sTime) return "";
		    const dateStr = this.formatDateTime(sDate, sTime);
		    const userStr = [sFName, sLName].filter(Boolean).join(" ");
		    if (userStr) {
		        return `${dateStr}\n${userStr}`;
		    }
		    return dateStr;
		},


        // ================== DOCUMENT ACTIONS ==================

        onOpenDocument: function (oEvent) {
        	// debugger;
            const oContext = oEvent.getSource().getBindingContext("selectedRequest");

            if (!oContext) {
                MessageBox.error("Unable to retrieve document information.");
                return;
            }

            const oDocData = oContext.getObject();
            const { REQUEST_ID, AttachType, IncNb, ArchiveDocId } = oDocData;

            if (!REQUEST_ID || !AttachType || !IncNb || !ArchiveDocId) {
                MessageBox.error("Incomplete keys to retrieve the document.");
                return;
            }

            const oModel = this.getView().getModel("offboardingModel");
            const sServiceUrl = oModel.sServiceUrl;
            // const sUrl = `${sServiceUrl}/FileUploadSet(RequestId='${encodeURIComponent(REQUEST_ID)}')/$value`;
            const sDocUrl = `${sServiceUrl}/FileUploadSet(RequestId='${encodeURIComponent(REQUEST_ID)}',DocumentType='${encodeURIComponent(AttachType)}')/$value`;

            window.open(sDocUrl, "_blank");
        },

        onDownloadDocument: function (oEvent) {
            const oContext = oEvent.getSource().getBindingContext("selectedRequest");
            var oBundle = this.getOwnerComponent().getModel("i18n").getResourceBundle();

            if (!oContext) {
                MessageBox.error("Unable to retrieve document information.");
                return;
            }

            const oDocument = oContext.getObject();
            const { REQUEST_ID, AttachType, IncNb, ArchiveDocId, Filename } = oDocument;

            if (!REQUEST_ID || !AttachType || !IncNb || !ArchiveDocId) {
                MessageBox.error("Missing keys to download the document.");
                return;
            }

            sap.ui.core.BusyIndicator.show(0);
            const oModel = this.getView().getModel("offboardingModel");
            const sServiceUrl = oModel.sServiceUrl;
            // const sDocUrl = `${sServiceUrl}/FileUploadSet(RequestId='${encodeURIComponent(REQUEST_ID)}')/$value`;
            const sDocUrl = `${sServiceUrl}/FileUploadSet(RequestId='${encodeURIComponent(REQUEST_ID)}',DocumentType='${encodeURIComponent(AttachType)}')/$value`;

            const link = document.createElement('a');
            link.href = sDocUrl;
            link.download = Filename || "Document.pdf";
            link.target = '_blank';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            sap.ui.core.BusyIndicator.hide();
            var sMsg = oBundle.getText("DownloadStarted", [Filename]);
            MessageToast.show(sMsg);
            //MessageToast.show("Download started: " + Filename);
        },

        onDeleteDocument: function (oEvent) {
            const oContext = oEvent.getSource().getBindingContext("selectedRequest");
            const oDocument = oContext ? oContext.getObject() : null;

            if (!oDocument) {
                MessageBox.error("Unable to delete document. Document data not found.");
                return;
            }

            const sDocName = oDocument.Filename || "this document";
            const self = this;

            MessageBox.confirm(
                `Are you sure you want to delete "${sDocName}"? This action cannot be undone.`,
                {
                    title: "Confirm Deletion",
                    actions: [MessageBox.Action.DELETE, MessageBox.Action.CANCEL],
                    emphasizedAction: MessageBox.Action.DELETE,
                    onClose: function (sAction) {
                        if (sAction === MessageBox.Action.DELETE) {
                            self._performDeleteDocument(oDocument);
                        }
                    }
                }
            );
        },

        _performDeleteDocument: function (oDocument) {
            sap.ui.core.BusyIndicator.show(0);
            const oModel = this.getView().getModel("offboardingModel");

            if (!oModel || typeof oModel.remove !== "function") {
                sap.ui.core.BusyIndicator.hide();
                MessageBox.error("OData Model is not available or 'remove' method missing");
                return;
            }

            const { REQUEST_ID, AttachType, IncNb, ArchiveDocId } = oDocument;

            if (!REQUEST_ID || !AttachType || !IncNb || !ArchiveDocId) {
                sap.ui.core.BusyIndicator.hide();
                MessageBox.error("Missing keys. Cannot delete.");
                return;
            }

            const sPath = `/TOAATSet(REQUEST_ID='${encodeURIComponent(REQUEST_ID.trim())}',AttachType='${encodeURIComponent(AttachType.trim())}',IncNb='${encodeURIComponent(IncNb)}',ArchiveDocId='${encodeURIComponent(ArchiveDocId.trim())}')`;

            oModel.remove(sPath, {
                success: () => {
                    sap.ui.core.BusyIndicator.hide();
                    var oBundle = this.getOwnerComponent().getModel("i18n").getResourceBundle();
                    var sMsg = oBundle.getText("DocumentDeletedSucess");
                    MessageToast.show(sMsg);
                    //MessageToast.show("Document deleted successfully");
                    this._loadDocuments();
                },
                error: (oError) => {
                    sap.ui.core.BusyIndicator.hide();
                    let sErrorMsg = "Unknown error";
                    try {
                        sErrorMsg = JSON.parse(oError.responseText).error.message.value;
                    } catch (e) {
                        // Erreur de parsing
                    }
                    MessageBox.error("Failed to delete document: " + sErrorMsg);
                }
            });
        },

        // ================== CSRF TOKEN MANAGEMENT ==================

        _getServiceBaseUrl: function () {
            var sUrl = this.oModel ? this.oModel.sServiceUrl : "/sap/opu/odata/sap/ZHRF_OFFBOARD_SRV/";
            if (sUrl.charAt(sUrl.length - 1) !== "/") {
                sUrl += "/";
            }
            return sUrl;
        },

        _fetchCSRFToken: function () {
            var that = this;
            return new Promise(function (resolve, reject) {
                var sUrl = that._getServiceBaseUrl();
                if (!sUrl.endsWith("/")) sUrl += "/";
                sUrl += "$metadata";

                jQuery.ajax({
                    url: sUrl,
                    method: "GET",
                    headers: { "X-CSRF-Token": "Fetch" },
                    xhrFields: { withCredentials: true },
                    success: function (data, textStatus, jqXHR) {
                        var sToken = jqXHR.getResponseHeader("x-csrf-token");
                        if (sToken) {
                            that._csrfToken = sToken;
                            resolve(sToken);
                        } else {
                            MessageBox.error("No CSRF token received from OData service.");
                            reject("No CSRF token received.");
                        }
                    },
                    error: function (jqXHR, textStatus, errorThrown) {
                        MessageBox.error("Unable to retrieve CSRF token: " + errorThrown);
                        reject(errorThrown || textStatus);
                    }
                });
            });
        },

        // ================== FILE UPLOAD ==================

        onChangeUpload: function (oEvent) {
            var aFiles = oEvent.getParameter("files");
            var oFile = aFiles && aFiles.length > 0 ? aFiles[0] : null;
            var oUploader = oEvent.getSource();
            
            var oBundle = this.getOwnerComponent().getModel("i18n").getResourceBundle();
            var sMsg;

            if (!oFile) {
            	sMsg = oBundle.getText("NoFileSelected");
            	MessageToast.show(sMsg);
                //MessageToast.show("No file selected.");
                return;
            }

            var maxSize = 50 * 1024 * 1024;
            var allowedTypes = [
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "image/jpeg",
                "image/png"
            ];

            if (!allowedTypes.includes(oFile.type)) {
                MessageBox.error("Invalid file type. Only PDF, Word, Excel and image files (JPG, PNG) are allowed.");
                oUploader.setValue("");
                return;
            }

            if (oFile.size > maxSize) {
                MessageBox.error("File exceeds maximum allowed size (50 MB).");
                oUploader.setValue("");
                return;
            }
			
			sMsg = oBundle.getText("FileSelected", [oFile.name]);
            MessageToast.show(sMsg);
            //MessageToast.show("File selected: " + oFile.name);
        },

        onPressUpload: function (oEvent) {
            var oButton = oEvent.getSource();
            var oHBox = oButton.getParent();
            
            var oBundle = this.getOwnerComponent().getModel("i18n").getResourceBundle();
            var sMsg;

            if (!oHBox || !oHBox.getItems) {
                MessageBox.error("View structure error");
                return;
            }

            var aItems = oHBox.getItems();
            var oFileUploader = null;

            for (var i = 0; i < aItems.length; i++) {
                if (aItems[i].getMetadata && aItems[i].getMetadata().getName() === "sap.ui.unified.FileUploader") {
                    oFileUploader = aItems[i];
                    break;
                }
            }

            if (!oFileUploader) {
                MessageBox.error("FileUploader component not found");
                return;
            }

            var aFiles = oFileUploader.oFileUpload ? oFileUploader.oFileUpload.files : [];
            if (!aFiles || aFiles.length === 0) {
            	sMsg = oBundle.getText("PleaseSelectFile");
            	MessageToast.show(sMsg);
                //MessageToast.show("Please select a file first");
                return;
            }

            this._proceedWithUpload(oFileUploader, oButton);
        },

        /**
         * _checkDocumentExists - VÃ©rifie si un document existe dÃ©jÃ  pour ce type
         */
        _checkDocumentExists: function(docType) {
            var oDocModel = this.getView().getModel("selectedRequest");
            var aDocuments = oDocModel.getProperty("/Documents") || [];

            var oExisting = aDocuments.find(function(doc) {
                return doc.AttachType === docType;
            });

            return oExisting ? oExisting : null;
        },
        _proceedWithUpload: function (oUploader, oButton) {
    const that = this;
    const oBundle = this.getView().getModel("i18n").getResourceBundle();

    if (oButton?.setEnabled) {
        oButton.setEnabled(false);
        oButton.setText(oBundle.getText("uploadInProgress"));
    }

    const getToken = this._csrfToken ? Promise.resolve(this._csrfToken) : this._fetchCSRFToken();

    getToken
        .then(csrfToken => {
            if (!csrfToken) throw oBundle.getText("unableToRetrieveCSRF");

            const files = oUploader.oFileUpload?.files || [];
            if (!files.length) {
                MessageToast.show(oBundle.getText("pleaseSelectFile"));
                throw oBundle.getText("noFileSelected");
            }

            const oRow = oUploader.getParent().getParent();
            const cells = oRow.getCells();

            const docName = cells[0]?.getText()?.trim() || "";
            const docKeyOrLabel = cells[0].data("docKey") || docName; // fallback to label if no stable key
            //const docMapping = that._getDocMapping(docKeyOrLabel);

			const reqDocList = oRow.getBindingContext("selectedRequest").getModel().oData.RequiredDocuments
			const docMapping = that._getDocMapping(reqDocList, docKeyOrLabel);
            jQuery.sap.log.info("Resolved docKey/label '" + docKeyOrLabel + "' to type '" + docMapping.doc_type + "'");

            const selectCtrl = cells[1];
            //const sSelectedKey = selectCtrl?.getSelectedKey?.() || "new";

            const docType = docMapping.doc_type;
            const oExistingDoc = that._checkDocumentExists(docType);
            const bDocExists = oExistingDoc !== null;

            if (bDocExists) {
            	MessageToast.show(
                    oBundle.getText("docAlreadyExistsMsg", [
                        docName,
                        oExistingDoc.Filename,
                        that.formatDateTime(oExistingDoc.CreationDate, oExistingDoc.CreationTime)
                    ])
                );           	
                // MessageBox.warning(
                //     oBundle.getText("docAlreadyExistsMsg", [
                //         docName,
                //         oExistingDoc.Filename,
                //         that.formatDateTime(oExistingDoc.CreationDate, oExistingDoc.CreationTime)
                //     ]),
                //     {
                //         title: oBundle.getText("docAlreadyExistsTitle"),
                //         actions: [MessageBox.Action.CLOSE],
                //         emphasizedAction: MessageBox.Action.CLOSE
                //     }
                // );
                //that._resetUploadButton(oButton);
                //throw "Document already exists - overwrite required";
            }else{
                MessageToast.show(oBundle.getText("noExistingDocFound", [docName]));
            }

            let fileName = oUploader.getValue().split(/(\\|\/)/).pop();
            fileName = fileName.replace(/[^\w.-]/g, "_");

            let fileExtension = fileName.includes(".")
                ? fileName.split(".").pop().toUpperCase()
                : that._getExtensionFromMimeType(files[0].type || "application/pdf");


            const safeRequestId = (that._requestId || "").replace(/-/g, "").toUpperCase();
            if (!safeRequestId) throw oBundle.getText("requestIdMissing");

            const sPernr = String(that.oModel?.getProperty("/CreatorPernr") || "00000000").padStart(8, "0");
            const mimeType = files[0].type || "application/pdf";
            const replaceFlag = bDocExists ? "TRUE" : "FALSE";

            const sSlug = [
                docType,
                encodeURIComponent(fileName),
                encodeURIComponent(mimeType),
                safeRequestId,
                replaceFlag,
                sPernr,
                fileExtension
            ].join(";");

            oUploader.removeAllHeaderParameters();
            oUploader.addHeaderParameter(new FileUploaderParameter({ name: "X-CSRF-Token", value: csrfToken }));
            oUploader.addHeaderParameter(new FileUploaderParameter({ name: "Slug", value: sSlug }));

            let sUploadUrl = that._getServiceBaseUrl();
            if (!sUploadUrl.endsWith("/")) sUploadUrl += "/";
            sUploadUrl += "TOAATSet";

            oUploader.setUploadUrl(sUploadUrl);
            oUploader.setUseMultipart(false);
            oUploader.setSendXHR(true);

            // Attach refresh logic on upload complete
            oUploader.attachUploadComplete((oEvent) => {
                MessageToast.show(oBundle.getText("uploadSuccess"));

                const oTable = that.byId("docsTable");
                const oModel = that.getView().getModel("selectedRequest");

                if (oModel instanceof sap.ui.model.odata.v2.ODataModel) {
                    jQuery.sap.log.info("Refreshing ODataModel after upload");
                    oModel.refresh(true);
                } else if (oModel instanceof sap.ui.model.json.JSONModel) {
                    jQuery.sap.log.info("Updating JSONModel after upload");
                    const aDocs = oModel.getProperty("/Documents") || [];
                    const oFile = oEvent.getParameters().files?.[0];
                    if (oFile) {
                        aDocs.push({
                            Filename: oFile.name,
                            AttachTypeTxt: docType,
                            Filesize: oFile.size,
                            CreatorFname: that.oModel.getProperty("/CreatorFname"),
                            CreatorLname: that.oModel.getProperty("/CreatorLname"),
                            CreatorPernr: sPernr,
                            CreationDate: new Date(),
                            CreationTime: new Date(),
                            LastUpdDate: new Date(),
                            LastUpdTime: new Date()
                        });
                        oModel.setProperty("/Documents", aDocs);
                    }
                }

                const oBinding = oTable.getBinding("items");
                if (oBinding) {
                    oBinding.refresh();
                    jQuery.sap.log.info("Docs table binding refreshed");
                }
            });

            oUploader.upload();
        })
        .catch(err => {
            if (err !== "Document already exists - overwrite required") {
                MessageBox.error(oBundle.getText("uploadPrepError", [err]));
            }
            that._resetUploadButton(oButton);
        });
},


  //      _proceedWithUpload: function (oUploader, oButton) {
		//     const that = this;
		//     const oBundle = this.getView().getModel("i18n").getResourceBundle();
		
		//     if (oButton?.setEnabled) {
		//         oButton.setEnabled(false);
		//         oButton.setText(oBundle.getText("uploadInProgress"));
		//     }
		
		//     const getToken = this._csrfToken ? Promise.resolve(this._csrfToken) : this._fetchCSRFToken();
		
		//     getToken
		//         .then(csrfToken => {
		//             if (!csrfToken) throw oBundle.getText("unableToRetrieveCSRF");
		
		//             const files = oUploader.oFileUpload?.files || [];
		//             if (!files.length) {
		//                 MessageToast.show(oBundle.getText("pleaseSelectFile"));
		//                 throw oBundle.getText("noFileSelected");
		//             }
		
		//             const oRow = oUploader.getParent().getParent();
		//             const cells = oRow.getCells();
		
		//             const docName = cells[0]?.getText()?.trim() || "";
		//             const docKey = cells[0].data("docKey");
		//             const docMapping = that._getDocMapping(docKey);
		
		//             const selectCtrl = cells[1];
		//             const sSelectedKey = selectCtrl?.getSelectedKey?.() || "new";
		
		//             const docType = docMapping.type;
		//             const oExistingDoc = that._checkDocumentExists(docType);
		//             const bDocExists = oExistingDoc !== null;
		
		//             if (sSelectedKey === "new" && bDocExists) {
		//                 MessageBox.warning(
		//                     oBundle.getText("docAlreadyExistsMsg", [
		//                         docName,
		//                         oExistingDoc.Filename,
		//                         that.formatDateTime(oExistingDoc.CreationDate, oExistingDoc.CreationTime)
		//                     ]),
		//                     {
		//                         title: oBundle.getText("docAlreadyExistsTitle"),
		//                         actions: [MessageBox.Action.CLOSE],
		//                         emphasizedAction: MessageBox.Action.CLOSE
		//                     }
		//                 );
		//                 that._resetUploadButton(oButton);
		//                 throw "Document already exists - overwrite required";
		//             }
		
		//             if (sSelectedKey === "overwrite" && !bDocExists) {
		//                 MessageToast.show(oBundle.getText("noExistingDocFound", [docName]));
		//             }
		
		//             let fileName = oUploader.getValue().split(/(\\|\/)/).pop();
		//             fileName = fileName.replace(/[^\w.-]/g, "_");
		
		//             let fileExtension = fileName.includes(".")
		//                 ? fileName.split(".").pop().toUpperCase()
		//                 : that._getExtensionFromMimeType(files[0].type || "application/pdf");
		
		//             const validTypes = ["SEP_LETTER", "REPAT_TRAVEL", "EXIT_QUEST", "REPAT_SHIP"];
		//             if (!validTypes.includes(docType)) {
		//                 throw oBundle.getText("invalidDocType", [docType]);
		//             }
		
		//             const safeRequestId = (that._requestId || "").replace(/-/g, "").toUpperCase();
		//             if (!safeRequestId) throw oBundle.getText("requestIdMissing");
		
		//             const sPernr = String(that.oModel?.getProperty("/CreatorPernr") || "00000000").padStart(8, "0");
		//             const mimeType = files[0].type || "application/pdf";
		//             const replaceFlag = sSelectedKey === "overwrite" ? "TRUE" : "FALSE";
		
		//             const sSlug = [
		//                 docType,
		//                 encodeURIComponent(fileName),
		//                 encodeURIComponent(mimeType),
		//                 safeRequestId,
		//                 replaceFlag,
		//                 sPernr,
		//                 fileExtension
		//             ].join(";");
		
		//             oUploader.removeAllHeaderParameters();
		//             oUploader.addHeaderParameter(new FileUploaderParameter({ name: "X-CSRF-Token", value: csrfToken }));
		//             oUploader.addHeaderParameter(new FileUploaderParameter({ name: "Slug", value: sSlug }));
		
		//             let sUploadUrl = that._getServiceBaseUrl();
		//             if (!sUploadUrl.endsWith("/")) sUploadUrl += "/";
		//             sUploadUrl += "TOAATSet";
		
		//             oUploader.setUploadUrl(sUploadUrl);
		//             oUploader.setUseMultipart(false);
		//             oUploader.setSendXHR(true);
		
		//             oUploader.upload();
		//         })
		//         .catch(err => {
		//             if (err !== "Document already exists - overwrite required") {
		//                 MessageBox.error(oBundle.getText("uploadPrepError", [err]));
		//             }
		//             that._resetUploadButton(oButton);
		//         });
		// },


  //      _proceedWithUpload: function (oUploader, oButton) {
		//     const that = this;
		
		//     if (oButton?.setEnabled) {
		//         oButton.setEnabled(false);
		//         oButton.setText("Upload in progress...");
		//     }
		
		//     const getToken = this._csrfToken ? Promise.resolve(this._csrfToken) : this._fetchCSRFToken();
		
		//     getToken
		//         .then(csrfToken => {
		//             if (!csrfToken) throw "Unable to retrieve CSRF token";
		
		//             const files = oUploader.oFileUpload?.files || [];
		//             if (!files.length) {
		//                 MessageToast.show("Please select a file.");
		//                 throw "No file selected";
		//             }
		
		//             const oRow = oUploader.getParent().getParent();
		//             const cells = oRow.getCells();
		
		//             // Define both docName (translated text for messages) and docKey (stable i18n key for mapping)
		//             const docName = cells[0]?.getText()?.trim() || "";
		//             const docKey = cells[0].data("docKey");
		//             const docMapping = that._getDocMapping(docKey);
		
		//             const selectCtrl = cells[1];
		//             const sSelectedKey = selectCtrl?.getSelectedKey?.() || "new";
		
		//             const docType = docMapping.type;
		
		//             // VALIDATION: Check if document already exists
		//             const oExistingDoc = that._checkDocumentExists(docType);
		//             const bDocExists = oExistingDoc !== null;
		
		//             // Case: "Create New" but document exists
		//             if (sSelectedKey === "new" && bDocExists) {
		//                 MessageBox.warning(
		//                     `A document already exists for "${docName}".\n\n` +
		//                     `Current file: ${oExistingDoc.Filename}\n` +
		//                     `Uploaded: ${that.formatDateTime(oExistingDoc.CreationDate, oExistingDoc.CreationTime)}\n\n` +
		//                     `Please select "Overwrite Existing" to replace it, or delete the existing document first.`,
		//                     {
		//                         title: "Document Already Exists",
		//                         actions: [MessageBox.Action.CLOSE],
		//                         emphasizedAction: MessageBox.Action.CLOSE
		//                     }
		//                 );
		//                 that._resetUploadButton(oButton);
		//                 throw "Document already exists - overwrite required";
		//             }
		
		//             // Case: "Overwrite" but no existing document
		//             if (sSelectedKey === "overwrite" && !bDocExists) {
		//                 MessageToast.show(`No existing document found. Creating new "${docName}".`);
		//             }
		
		//             let fileName = oUploader.getValue().split(/(\\|\/)/).pop();
		//             fileName = fileName.replace(/[^\w.-]/g, "_");
		
		//             let fileExtension = fileName.includes(".")
		//                 ? fileName.split(".").pop().toUpperCase()
		//                 : that._getExtensionFromMimeType(files[0].type || "application/pdf");
		
		//             const validTypes = ["SEP_LETTER", "REPAT_TRAVEL", "EXIT_QUEST", "REPAT_SHIP"];
		//             if (!validTypes.includes(docType)) {
		//                 throw `Invalid document type: ${docType}`;
		//             }
		
		//             const safeRequestId = (that._requestId || "").replace(/-/g, "").toUpperCase();
		//             if (!safeRequestId) throw "Request ID missing";
		
		//             const sPernr = String(that.oModel?.getProperty("/CreatorPernr") || "00000000").padStart(8, "0");
		//             const mimeType = files[0].type || "application/pdf";
		//             const replaceFlag = sSelectedKey === "overwrite" ? "TRUE" : "FALSE";
		
		//             const sSlug = [
		//                 docType,
		//                 encodeURIComponent(fileName),
		//                 encodeURIComponent(mimeType),
		//                 safeRequestId,
		//                 replaceFlag,
		//                 sPernr,
		//                 fileExtension
		//             ].join(";");
		
		//             oUploader.removeAllHeaderParameters();
		//             oUploader.addHeaderParameter(new FileUploaderParameter({ name: "X-CSRF-Token", value: csrfToken }));
		//             oUploader.addHeaderParameter(new FileUploaderParameter({ name: "Slug", value: sSlug }));
		
		//             let sUploadUrl = that._getServiceBaseUrl();
		//             if (!sUploadUrl.endsWith("/")) sUploadUrl += "/";
		//             sUploadUrl += "TOAATSet";
		
		//             oUploader.setUploadUrl(sUploadUrl);
		//             oUploader.setUseMultipart(false);
		//             oUploader.setSendXHR(true);
		
		//             oUploader.upload();
		//         })
		//         .catch(err => {
		//             if (err !== "Document already exists - overwrite required") {
		//                 MessageBox.error("Upload preparation error: " + err);
		//             }
		//             that._resetUploadButton(oButton);
		//         });
		// },


        _getExtensionFromMimeType: function (mimeType) {
            var extensionMap = {
                "application/pdf": "PDF",
                "application/vnd.ms-excel": "XLS",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "XLSX",
                "application/msword": "DOC",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
                "image/jpeg": "JPG",
                "image/png": "PNG",
                "image/gif": "GIF"
            };
            return extensionMap[mimeType] || "DAT";
        },

        _resetUploadButton: function (oButton) {
            if (oButton && oButton.setEnabled) {
                oButton.setEnabled(true);
                oButton.setText("Upload");
            }
        },

        onUploadComplete: function (oEvent) {
            var iStatus = oEvent.getParameter("status");
            var sResponse = oEvent.getParameter("response") || oEvent.getParameter("responseRaw") || "";
            var oUploader = oEvent.getSource();
            var oParent = oUploader.getParent();
            var oButton = null;
            var oRow = null;
            var oCellStatus = null;
            var docName = "";
            
            var oBundle = this.getOwnerComponent().getModel("i18n").getResourceBundle();
            var sMsg;

            if (oParent && oParent.getItems) {
                var aItems = oParent.getItems();
                oButton = aItems.length > 1 ? aItems[1] : null;
            }
            if (oParent && oParent.getParent) {
                oRow = oParent.getParent();
                if (oRow && oRow.getCells) {
                    var aCells = oRow.getCells();
                    oCellStatus = aCells.length > 2 ? aCells[2] : null;
                    docName = aCells[0].getText();
                }
            }

            this._resetUploadButton(oButton);

            var sErrorMessage = sResponse;
            try {
                if (sResponse && sResponse.indexOf("{") === 0) {
                    var oJson = JSON.parse(sResponse);
                    sErrorMessage = oJson.error && oJson.error.message && oJson.error.message.value
                        ? oJson.error.message.value
                        : sResponse;
                }
            } catch (e) {
                // Erreur de parsing
            }

            if (iStatus === 201 || iStatus === 200) {
                if (oCellStatus && oCellStatus.setText) {
                    oCellStatus.setText("Upload successful");
                    oCellStatus.removeStyleClass("sapUiErrorText");
                    oCellStatus.addStyleClass("sapUiSuccessText");
                }
				
				sMsg = oBundle.getText("UploadCompleteSucess");
				MessageToast.show(sMsg);
                //MessageToast.show("Upload completed successfully!");

                //var docMapping = this._getDocMapping(docName);
                // if (docMapping.fileId) {
                //     this._uploadedFiles[docMapping.fileId] = true;
                // }

                oUploader.setValue("");
                this._loadDocuments();

            } else {
                if (oCellStatus && oCellStatus.setText) {
                    oCellStatus.setText("Error (" + iStatus + ")");
                    oCellStatus.removeStyleClass("sapUiSuccessText");
                    oCellStatus.addStyleClass("sapUiErrorText");
                }

                MessageBox.error(
                    "Upload error\n\n" +
                    "HTTP Code: " + iStatus + "\n" +
                    "Details: " + sErrorMessage
                );
            }
        },

        onUploadAborted: function (oEvent) {
        	var oBundle = this.getOwnerComponent().getModel("i18n").getResourceBundle();
        	var sMsg = oBundle.getText("UploadInterrupted");
        	
        	MessageToast.show(sMsg);
            //MessageToast.show("Upload interrupted");
            var oUploader = oEvent.getSource();
            var oParent = oUploader.getParent();
            var oButton = null;
            if (oParent && oParent.getItems) {
                var aItems = oParent.getItems();
                oButton = aItems.length > 1 ? aItems[1] : null;
            }
            this._resetUploadButton(oButton);
        },

        // _getDocMapping: function (docName) {
        //     var mapping = {
        //         "Separation Letter": { type: "SEP_LETTER", fileId: "file1" },
        //         "Repatriation Travel": { type: "REPAT_TRAVEL", fileId: "file2" },
        //         "Exit Questionnaire": { type: "EXIT_QUEST", fileId: "file3" },
        //         "Repatriation Shipment": { type: "REPAT_SHIP", fileId: "file4" }
        //     };

        //     var result = mapping[docName];
        //     if (!result) {
        //         throw `Invalid document type: "${docName}". Must be one of: ${Object.keys(mapping).join(', ')}.`;
        //     }

        //     return result;
        // },
  //      _getDocMapping: function (docKey) {
		//     var mapping = {
		//         "separationLetterLabel": { type: "SEP_LETTER", fileId: "file1" },
		//         "repatriationTravelLabel": { type: "REPAT_TRAVEL", fileId: "file2" },
		//         "exitQuestionnaireLabel": { type: "EXIT_QUEST", fileId: "file3" },
		//         "repatriationShipmentLabel": { type: "REPAT_SHIP", fileId: "file4" }
		//     };
		
		//     var result = mapping[docKey];
		//     if (!result) {
		//         throw `Invalid document key: "${docKey}". Must be one of: ${Object.keys(mapping).join(', ')}.`;
		//     }
		
		//     return result;
		// },
		// _getDocMapping: function (docKeyOrLabel) {
		//     // Stable mapping table
		//     var mapping = {
		//         "separationLetterLabel": { type: "SEP_LETTER", fileId: "file1" },
		//         "repatriationTravelLabel": { type: "REPAT_TRAVEL", fileId: "file2" },
		//         "exitQuestionnaireLabel": { type: "EXIT_QUEST", fileId: "file3" },
		//         "repatriationShipmentLabel": { type: "REPAT_SHIP", fileId: "file4" }
		//     };
		
		//     // Reverse lookup for localized labels (English + French)
		//     var reverse = {
		//         "Separation Letter": "separationLetterLabel",
		//         "Lettre de sÃ©paration": "separationLetterLabel",
		
		//         "Repatriation Travel": "repatriationTravelLabel",
		//         "Voyage de rapatriement": "repatriationTravelLabel",
		
		//         "Exit Questionnaire": "exitQuestionnaireLabel",
		//         "Questionnaire de sortie": "exitQuestionnaireLabel",
		
		//         "Repatriation Shipment": "repatriationShipmentLabel",
		//         "ExpÃ©dition de rapatriement": "repatriationShipmentLabel"
		//     };
		
		//     // Resolve stable key
		//     var stableKey = mapping[docKeyOrLabel] ? docKeyOrLabel : reverse[docKeyOrLabel];
		
		//     if (!stableKey || !mapping[stableKey]) {
		//         jQuery.sap.log.error("Invalid document key or label: " + docKeyOrLabel);
		//         throw `Invalid document key: "${docKeyOrLabel}". Must be one of: ${Object.keys(mapping).join(", ")}.`;
		//     }
		
		//     jQuery.sap.log.info("Resolved docKey '" + docKeyOrLabel + "' to stable key '" + stableKey + "' and type '" + mapping[stableKey].type + "'");
		//     return mapping[stableKey];
		// },
		_getDocMapping: function ( reqDocList, docKeyOrLabel) {
		    // Stable mapping table
		    var mapping = new Map();
			var reverse = new Map();
				
			$.each(reqDocList, function(i, item){
				mapping.set( item.Doc_Type , { doc_type: item.Doc_Type, doc_name: item.Doc_type_txt } );
			});
			
			$.each(reqDocList, function(i, item){
				reverse.set( item.Doc_type_txt , { doc_type: item.Doc_Type, doc_name: item.Doc_type_txt } );
			});
			
		    // Resolve stable key
		    var stableKey = mapping.get(docKeyOrLabel) ? mapping.get(docKeyOrLabel).doc_type : reverse.get(docKeyOrLabel).doc_type;

		    if (!stableKey) {
		        jQuery.sap.log.error("Invalid document key or label: " + docKeyOrLabel);
		        throw `Invalid document key: "${docKeyOrLabel}". Must be one of: ${Object.keys(mapping).join(", ")}.`;
		    }
		
		    jQuery.sap.log.info("Resolved docKey '" + docKeyOrLabel + "' to stable key '" + stableKey + "'");
		    return mapping.get(stableKey);
		},


        // ================== NAVIGATION ==================

        onNavBack: function () {
            var oHistory = History.getInstance();
            var sPreviousHash = oHistory.getPreviousHash();
            if (sPreviousHash !== undefined) {
                window.history.go(-1);
            } else {
                var oRouter = UIComponent.getRouterFor(this);
                oRouter.navTo("RouteEmployee", {}, true);
            }
        },

        onNotifications: function () {
            MessageToast.show("Notifications feature coming soon");
        },

        onUserProfile: function () {
            MessageToast.show("User profile feature coming soon");
        }

    });
});