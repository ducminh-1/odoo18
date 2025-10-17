/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import Fullscreen from "@website_slides/js/slides_course_fullscreen_player";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";

var findSlide = function(slideData, matcher){
    return slideData.find((slide) => {
        return Object.keys(matcher).every((key) => matcher[key] === slide[key]);
    });
}
patch(Fullscreen.prototype, {


    _onChangeSlideRequest: async function (ev) {
        var slideData = ev.data;
        const { id, canAccess, slideComplete, isQuiz } = slideData;
        var newSlide = findSlide(this.slides, {
            id: slideData.id,
            isQuiz: slideData.isQuiz || false,
        });
        const currentSlide = this._slideValue;
        const currentSlideId = currentSlide.id;
        if (isQuiz) {
            // true and  false and true
            // alert(_t('Bạn phải hoàn thành khóa học trước!!!'))
            return this._updateSlideValue(newSlide);
        }

        try{
            const result = await this._markSlideComplete(id);
            // const nextSlide = this.slides.find(s => s.id === result.next_slide_id);
            if (result.completed || newSlide.slideComplete){
                newSlide.slideComplete = true;
                this._updateSlideValue(newSlide);
            }
            else{
                alert(_t('Bạn phải hoàn thành khóa học trước!!!'))
            }
            // if (nextSlide) {
            //     $next.attr("data-slide-complete", "True").removeClass("locked");
            //     const $next = $(`.o_wslides_fs_sidebar_list_item[data-id="${result.next_slide_id}"]`);
            //     this._updateSlideValue(newSlide);
            // }
            // else{
            //     alert(_t('Bạn phải hoàn thành khóa học trước!!!'))
            // }
        }catch(err) {
            console.log('error')
        } 
    },
    async _markSlideComplete(slideId) {
        return rpc("/slides/mark_complete", { slide_id: slideId });
    },

})

