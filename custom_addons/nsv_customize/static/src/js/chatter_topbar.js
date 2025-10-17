// Odoo.define('nsv_customize/static/src/js/chatter_topbar.js', function (require) {
//    'use strict';
//
//    const components = {
//        ChatterTopbar: require('mail/static/src/components/chatter_topbar/chatter_topbar.js'),
//    };
//
//    const { patch } = require('web.utils');
//
//    patch(components.ChatterTopbar, 'chatter_topbar', {
//
//        //--------------------------------------------------------------------------
//        // Public
//        //--------------------------------------------------------------------------
//
//        /**
//         * @override
//         */
//        _onClickSendMessage(ev) {
//            if (!this.chatter.composer) {
//                return;
//            }
//            if (this.chatter.isComposerVisible && !this.chatter.composer.isLog) {
//                this.chatter.update({ isComposerVisible: false });
//            } else {
//                console.log('customize NSV_Odoo14 chatter topbar')
//                this.chatter.composer.openFullComposer()
//
//            }
//        }
//
//    });
//
// });
//
