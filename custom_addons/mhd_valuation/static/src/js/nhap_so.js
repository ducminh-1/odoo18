odoo.define('mhd_valuation.nhaptoado', function (require) {
    "use strict";
    // import packages
    var basic_fields = require('web.basic_fields');
    var registry = require('web.field_registry');

    // widget implementation
    var NhapToaDo = basic_fields.FieldFloat.extend({
        _prepareInput: function ($input) {
            this._super.apply(this, arguments);
            this.$input.mask("990,999999999", {reverse: true});
            return this.$input;
        },

    });

    registry.add('nhap_toado', NhapToaDo); // add our "bold" widget to the widget registry
});