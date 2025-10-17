from odoo import fields, models, tools


class ProductFailureReport(models.Model):
    _name = "product.failure.report"
    _description = "Product Failure Report"
    _auto = False
    _rec_name = "ticket_id"

    def _get_ticket_type(self):
        ticket_type_sudo = self.env["helpdesk.ticket.type"].sudo()
        return (
            ticket_type_sudo.search([("filter_failure_report", "=", True)]).ids
            or ticket_type_sudo.search([]).ids
        )

    def _get_ticket_team(self):
        team_sudo = self.env["helpdesk.team"].sudo()
        res = (
            team_sudo.search([("filter_failure_report", "=", True)]).ids
            or team_sudo.search([]).ids
        )
        return res + [0]

    product_id = fields.Many2one("product.product", "Product", readonly=True)
    # sale_id = fields.Many2one('sale.order', 'Sale Order', readonly=True)
    ticket_id = fields.Many2one("helpdesk.ticket", "Ticket", readonly=True)
    failure_rate = fields.Float("Failure Rate", readonly=True, group_operator="sum")
    date = fields.Date("Date", readonly=True)
    # date_order = fields.Date('Date Order', readonly=True)
    sold_qty = fields.Float("Quantity Sold", readonly=True, group_operator="avg")
    qty_maintenance = fields.Float(
        "Maintenance Quantity", group_operator="sum", readonly=True
    )

    def _query(self):
        return """
            WITH product_sold AS (
		SELECT sol.product_id AS product, sum(sol.qty_delivered) AS quantity_sold, DATE(so.date_order) AS date_order
		FROM sale_order_line AS sol
			left join sale_order so ON so.id = sol.order_id
		WHERE sol.state in ('sale','done') AND sol.product_id IS NOT NULL
		group by sol.product_id, DATE(so.date_order)
		order by DATE(so.date_order) desc
	), product_maintenance AS (
		SELECT ticket.id as ticket_id, ticket.product_id AS product, count(ticket.id) AS quantity_maintenance, DATE(ticket.create_date) AS create_date
		FROM helpdesk_ticket AS ticket
		WHERE ticket.ticket_type_id in %s and ticket.team_id in %s AND ticket.product_id IS NOT NULL
		group by ticket.product_id, DATE(ticket.create_date), ticket.id
	)

	select
		row_number() OVER () AS id,
		pm.product product_id,
		pm.create_date date,
		pm.ticket_id ticket_id,
-- 		product_sold.date_order date_order,
		sum(product_sold.quantity_sold) sold_qty,
		pm.quantity_maintenance qty_maintenance,
		CASE COALESCE(sum(product_sold.quantity_sold), 0)
                        WHEN 0 THEN 100.0
                        ELSE (pm.quantity_maintenance/sum(product_sold.quantity_sold))*100 END
                        AS failure_rate
	from product_maintenance pm
		 inner join product_sold on (product_sold.product = pm.product AND DATE_PART('year', pm.create_date) = DATE_PART('year', product_sold.date_order)
                                            AND	DATE_PART('month', pm.create_date) - 1 = DATE_PART('month', product_sold.date_order))
	group by pm.product, pm.create_date, pm.ticket_id, pm.quantity_maintenance
        """ % (tuple(self._get_ticket_type()), tuple(self._get_ticket_team()))

    #
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """CREATE or REPLACE VIEW %s AS (%s)""" % (self._table, self._query())
        )
