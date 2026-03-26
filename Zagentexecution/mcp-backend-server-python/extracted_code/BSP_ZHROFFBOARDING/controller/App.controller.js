sap.ui.define([
    "sap/ui/core/mvc/Controller"
], function (Controller) {
    "use strict";

    return Controller.extend("com.hr.unesco.yhrappoffboarding.controller.App", {

        onInit: function () {
            console.log("App Controller initialized");
            
            // Initialiser le router
            this.getRouter().initialize();
        },

        /**
         * Convenience method for getting the router
         * @returns {sap.ui.core.routing.Router} Router instance
         */
        getRouter: function () {
            return this.getOwnerComponent().getRouter();
        }
    });
});