sap.ui.define([
  "sap/ui/core/UIComponent",
  "sap/ui/Device",
  "sap/ui/model/json/JSONModel"
], function (UIComponent, Device, JSONModel) {
  "use strict";

  return UIComponent.extend("com.hr.unesco.yhrappoffboardingemp.Component", {
    metadata: {
      manifest: "json"
    },

    init: function () {
      // Call the base component's init function
      UIComponent.prototype.init.apply(this, arguments);

      // Device model for responsiveness
      var oDeviceModel = new JSONModel(Device);
      oDeviceModel.setDefaultBindingMode("OneWay");
      this.setModel(oDeviceModel, "device");
      
      // Le modèle OData est déjà configuré dans le manifest.json
      // Pas besoin de le recréer ici
    },

    getContentDensityClass: function () {
      if (!this._sContentDensityClass) {
        var bCozy = !!Device.support.touch;
        this._sContentDensityClass = bCozy ? "sapUiSizeCozy" : "sapUiSizeCompact";
      }
      return this._sContentDensityClass;
    }
  });
});