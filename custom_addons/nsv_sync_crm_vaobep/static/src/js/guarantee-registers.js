/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import {_t} from "@web/core/l10n/translation";
import {getDataURLFromFile} from "@web/core/utils/urls";
import {useService} from "@web/core/utils/hooks";
import {rpc} from "@web/core/network/rpc";

publicWidget.registry.GuaranteeRegisters = publicWidget.Widget.extend({
    selector: "#form-guarantee-registers",
    events: {
        "click .js_btn_submit_guarantee": "_onSubmitForm",
        'change select[name="country_id"]': "_onChangeCountry",
        'change select[name="city_id"]': "_onChangeCity",
        'change select[name="district_id"]': "_onChangeDistrict",
    },
    init: function () {
        this._super(...arguments);
        this.notification = this.bindService("notification");
    },
    _onSubmitForm: async function () {
        if (
            this._checkIsValid("#contact_name") ||
            this._checkIsValid("#phone") ||
            this._checkIsValid("#buy_date") ||
            this._checkIsValid("#sku") ||
            this._checkIsValid("#buy_at") ||
            this._checkIsValid("#bill_img")
        ) {
            this.notification.add(_t("Cân điền đủ thông tin các trường bắt buộc"), {
                type: "danger",
            });

            return;
        } else {
            $(".js_notify").remove();
            const imageUrl = await getDataURLFromFile(
                document.getElementById("bill_img").files[0]
            );
            var button = $("#submit");
            button.attr("disabled", true);
            rpc("/js/guarantee-registers", {
                contact_name: $("#contact_name").val(),
                phone: $("#phone").val(),
                email: $("#email").val(),
                city_id: $("#city_id").val(),
                district_id: $("#district_id").val(),
                ward_id: $("#ward_id").val(),
                street: $("#street").val(),
                buy_date: $("#buy_date").val(),
                buy_at: $("#buy_at").val(),
                sku: $("#sku").val(),
                birthday: $("#birthday").val(),
                total_amount: $("#total_amount").val(),
                bill_img: imageUrl.split(",")[1],
                img_name: document.getElementById("bill_img").files[0].name,
            }).then(function (res) {
                if (res == true) {
                    $("form").html(
                        '<div class="row"><div class="col-12 text-center"> <h3>Gửi thông tin thành công!</h3> <p>Cảm ơn bạn đã đăng ký bào hành điện tử online, phiếu đăng ký của bạn đã được gửi thành công, sau khi nhân viên xác nhận bạn sẽ được cộng điểm tích lũy và thêm 3 tháng bảo hành.</p></div></div>'
                    );
                    button.attr("disabled", false);
                } else {
                    $(".form-inputs").after(
                        '<div class="js_notify alert alert-warning alert-dismissible fade show" role="alert"><strong>Thông báo!</strong> Vui lòng điền chính xác thông tin!<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button></div>'
                    );
                    button.attr("disabled", false);
                }
            });
        }
    },
    _checkIsValid: function (required) {
        var counter = 0;
        var isValid = false;
        $(required).each(function (index, ele) {
            if ($(ele).val() === "") {
                ++counter;
                $(ele).css({
                    border: "1px solid #ff0000",
                });
                setTimeout(function () {
                    $(ele).css({
                        border: "1px solid #dee2e6",
                    });
                }, 2000);
                isValid = true;
            }
        });
        if (counter == 0) {
            isValid = false;
        }
        return isValid;
    },
    _changeCountry: function () {
        if (!$("#country_id").val()) {
            return;
        }
        rpc("/shop/custom_country_infos/" + $("#country_id").val()).then(
            function (data) {
                $("input[name='phone']").attr(
                    "placeholder",
                    data.phone_code !== 0 ? "+" + data.phone_code : ""
                );
                var selectCities = $("select[name='city_id']");
                var selectDistricts = $("select[name='district_id']");
                var selectWards = $("select[name='ward_id']");
                if (data.cities.length) {
                    selectCities.html("");
                    selectCities.append(
                        $("<option>").text("City / Province").attr("value", "")
                    );
                    _.each(data.cities, function (x) {
                        var opt = $("<option>")
                            .text(x[1])
                            .attr("value", x[0])
                            .attr("data-code", x[2]);
                        selectCities.append(opt);
                    });
                    selectCities.parent("div").show();
                } else {
                    selectCities.val("").parent("div").hide();
                    selectDistricts.val("").parent("div").hide();
                    selectWards.val("").parent("div").hide();
                }
            }
        );
    },
    _changeCity: function () {
        var selectDistricts = $("select[name='district_id']");
        var selectWards = $("select[name='ward_id']");
        if (!$("#city_id").val()) {
            selectDistricts.html("");
            selectDistricts.append($("<option>").text("District").attr("value", ""));
            selectWards.html("");
            selectWards.append($("<option>").text("Ward").attr("value", ""));
            return;
        }
        rpc("/shop/city_infos/" + $("#city_id").val()).then(function (data) {
            if (data.districts.length) {
                selectDistricts.html("");
                selectWards.html("");
                selectDistricts.append(
                    $("<option>").text("District").attr("value", "")
                );
                selectWards.append($("<option>").text("Ward").attr("value", ""));
                data.districts.forEach(function (x) {
                    var opt = document.createElement("option");
                    opt.textContent = x[1];
                    opt.value = x[0];
                    opt.setAttribute("data-code", x[2]);
                    selectDistricts.append(opt);
                });
                selectDistricts.parent("div").show();
            } else {
                selectDistricts.val("").parent("div").hide();
                selectWards.val("").parent("div").hide();
            }
        });
    },
    _changeDistrict: function () {
        if (!$("#district_id").val()) {
            return;
        }
        rpc("/shop/district_infos/" + $("#district_id").val()).then(function (data) {
            var selectWards = $("select[name='ward_id']");
            if (data.wards.length) {
                selectWards.html("");
                selectWards.append($("<option>").text("Ward").attr("value", ""));
                data.wards.forEach(function (x) {
                    var opt = document.createElement("option");
                    opt.textContent = x[1];
                    opt.value = x[0];
                    opt.setAttribute("data-code", x[2]);
                    selectWards.append(opt);
                });
                selectWards.parent("div").show();
            } else {
                selectWards.val("").parent("div").hide();
            }
        });
    },
    _onChangeCountry: function (ev) {
        if (!this.$(".checkout_autoformat").length) {
            return;
        }
        this._changeCountry();
    },
    _onChangeCity: function (ev) {
        if (!this.$(".checkout_autoformat").length) {
            return;
        }
        this._changeCity();
    },
    _onChangeDistrict: function (ev) {
        if (!this.$(".checkout_autoformat").length) {
            return;
        }
        this._changeDistrict();
    },
});

export default publicWidget.registry.GuaranteeRegisters;
