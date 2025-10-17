// Odoo.define('nsv_customize/static/src/js/thread_needaction_preview.js', function (require) {
//    'use strict';
//
//    const components = {
//        ThreadNeedactionPreview: require('mail/static/src/components/thread_needaction_preview/thread_needaction_preview.js'),
//    };
//
//    const { patch } = require('web.utils');
//
//    patch(components.ThreadNeedactionPreview, 'thread_needaction_preview', {
//
//        //--------------------------------------------------------------------------
//        // Public
//        //--------------------------------------------------------------------------
//
//        /**
//         * @override
//         */
//        _onClick(ev) {
//            const markAsRead = this._markAsReadRef.el;
//            if (markAsRead && markAsRead.contains(ev.target)) {
//                // handled in `_onClickMarkAsRead`
//                return;
//            }
//            console.log('customize NSV_Odoo14')
//            this.thread.open({ expanded: true });
//            if (!this.env.messaging.device.isMobile) {
//                this.env.messaging.messagingMenu.close();
//            }
//        }
//
//    });
//
// });
// TODO: open by click on the message
