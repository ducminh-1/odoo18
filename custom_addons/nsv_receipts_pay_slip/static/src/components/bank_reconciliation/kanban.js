/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";

import {BankRecKanbanController} from "@account_accountant/components/bank_reconciliation/kanban";

patch(BankRecKanbanController.prototype, {
    async onClickPrint() {
        return this.actionService.doAction({
            type: "ir.actions.report",
            report_type: "qweb-pdf",
            report_name: `nsv_receipts_pay_slip.print_receipts_pay_slip/${this.state.bankRecStLineId}`,
        });
    },
});
