import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ratingWebsiteForm = publicWidget.Widget.extend({
    selector: ".o_rating_page_submit",
    read_events: {
        "click .o_rating_label": "_onClickRatingLabel",
    },

    /**
     * @private
     */
    _onClickRatingLabel: function (ev) {
        this.$(".form_rating").find(".warning_required").addClass("d-none");
        this.$(".form_rating").find(".js_btn_submit").removeClass("d-none");
        const $label = $(ev.currentTarget);
        const $input = $label.find('input[type="radio"]');
        if ($input.length) {
            $input.prop("checked", true);
        }
        // Remove 'active' from all siblings
        this.$(".o_rating_label").removeClass("active");

        // Add 'active' to clicked label
        $label.addClass("active");

        // Show submit button, hide warning
        this.$(".form_rating").find(".warning_required").addClass("d-none");
        this.$(".form_rating").find(".js_btn_submit").removeClass("d-none");
    },
});
