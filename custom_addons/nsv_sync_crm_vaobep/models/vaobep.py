from markupsafe import Markup

from odoo import api, fields, models


class VaoBepEvent(models.Model):
    _name = "vaobep.event"

    name = fields.Char()
    data = fields.Text()


class VaoBepCRM(models.Model):
    _name = "vaobep.crm"

    name = fields.Char()
    data = fields.Text()


class GuaranteeRegisters(models.Model):
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _name = "guarantee.registers"
    _description = "Guarantee Registers"
    _order = "id desc"

    state = fields.Selection(
        [
            ("new", "New"),
            ("confirmed", "Confirmed"),
            ("manager_confirmed", "Manager Confirmed"),
            ("cancel", "Cancel"),
        ],
        default="new",
        tracking=True,
    )
    name = fields.Char(compute="_compute_name", store=True)
    contact_name = fields.Char(tracking=True)
    phone = fields.Char(tracking=True)
    email = fields.Char(tracking=True)
    country_id = fields.Many2one("res.country")
    city_id = fields.Many2one("res.city", domain="[('country_id', '=?', country_id)]")
    district_id = fields.Many2one("res.district", domain="[('city_id', '=?', city_id)]")
    ward_id = fields.Many2one("res.ward", domain="[('district_id', '=?', district_id)]")
    street = fields.Char(tracking=True)
    full_address = fields.Char(compute="_compute_full_address", store=True)
    buy_date = fields.Date(tracking=True)
    birthday = fields.Date(tracking=True)
    buy_at = fields.Char(tracking=True)
    description = fields.Text(tracking=True)
    sku = fields.Char(tracking=True)
    lot_name = fields.Char(tracking=True)
    product_id = fields.Many2one("product.product", tracking=True)
    partner_id = fields.Many2one("res.partner", tracking=True)
    total_amount = fields.Float(tracking=True)
    filename = fields.Char()
    bill_img = fields.Binary()
    is_add_loyalty = fields.Boolean(default=False)

    @api.depends("phone", "sku")
    def _compute_name(self):
        for gua in self:
            gua.name = "%s - %s" % (gua.phone, gua.sku)

    @api.depends("street", "ward_id", "district_id", "city_id", "country_id")
    def _compute_full_address(self):
        for record in self:
            street = record.street or ""
            ward = record.ward_id.name or ""
            district = record.district_id.name or ""
            city = record.city_id.name or ""
            country = record.country_id.name or ""
            record.full_address = ", ".join(
                [el for el in [street, ward, district, city, country] if el != ""]
            )

    def btn_create_contact(self):
        regis_to_action = self - self.filtered(lambda g: g.partner_id)

        partners = self.env["res.partner"]
        for regis in regis_to_action:
            val = {
                "name": regis.contact_name,
                "street": regis.street or "",
                "phone": regis.phone or "",
                "email": regis.email or "",
                "birthday": regis.birthday,
                "comment": "From Guarantee Register Form: %s\n%s\n%s"
                % (regis.buy_at, regis.sku, regis.lot_name),
            }
            partner = self.env["res.partner"].create(val)
            regis.partner_id = partner
            partners |= partner

        if len(partners) > 1:
            action = self.env["ir.actions.actions"]._for_xml_id(
                "contacts.action_contacts"
            )
            action["context"] = {}
            action["res_id"] = partners.ids
            action["views"] = [(self.env.ref("base.view_partner_tree").id, "tree")]
            action["domain"] = [("id", "in", partners.ids)]
            return action
        return True

    def get_product_related(self):
        for regis in self:
            product = self.env["product.product"].search(
                [("default_code", "=", regis.sku)], limit=1
            )
            if product:
                regis.product_id = product.id
            if not regis.partner_id:
                partner = self.env["res.partner"].search(
                    [
                        "|",
                        "|",
                        ("email", "=", regis.email),
                        ("phone", "=", regis.phone),
                        ("mobile", "=", regis.phone),
                    ],
                    limit=1,
                )
                regis.partner_id = partner and partner.id or False

    def btn_confirm(self):
        self.get_product_related()
        for regis in self:
            regis.write({"state": "confirmed"})

    def btn_manager_confirm(self):
        IrConfigParam = self.env["ir.config_parameter"].sudo()
        get_param = IrConfigParam.get_param
        guarantee_registers_sms_brand_name_id = get_param(
            "guarantee_registers_sms_brand_name_id"
        )
        sms_template = self.env["ir.ui.view"]
        zns_template = self.env["ir.ui.view"]
        zns_template_zalo_id = 0
        if guarantee_registers_sms_brand_name_id:
            sms_brandname_id = self.env["sms.brandname"].browse(
                int(guarantee_registers_sms_brand_name_id)
            )
            zalo_oa_id = sms_brandname_id.zalo_oa_id
            sms_template = zns_template = zalo_oa_id.guarantee_register_zns_template_id
            zns_template_zalo_id = zns_template.zns_template_id
        for regis in self:
            if regis.is_add_loyalty == False:
                regis.partner_id.loyalty_point_amount += regis.total_amount / 1000
                regis.is_add_loyalty = True
            regis.write({"state": "manager_confirmed"})
            if sms_template:
                body_sms = ""
                zns_template_vals = []
                try:
                    body_sms = self.env["sms.template"]._render_template(
                        sms_template.xml_id, regis._name, regis.ids, engine="qweb_view"
                    )[regis.id]
                    if zns_template and zns_template_zalo_id:
                        key_value_list = zns_template.get_val_esc_in_xml_zns()
                        for item in key_value_list:
                            val = {
                                "name": item["name"],
                                "value": eval(
                                    item["value"].replace("object.", "regis.")
                                ),
                            }
                            zns_template_vals.append((0, 0, val))
                except Exception as e:
                    regis.message_post(body="Render body SMS fail: %s" % e)
                sms = (
                    self.env["sms.sms"]
                    .sudo()
                    .create(
                        {
                            "sms_brandname_id": sms_brandname_id.id,
                            "body": body_sms,
                            "partner_id": regis.partner_id.id,
                            "number": regis.phone
                            or regis.partner_id.phone
                            or regis.partner_id.mobile,
                            "zns_template_id": zns_template_zalo_id
                            if zns_template_zalo_id
                            else False,
                            "zns_template_val_ids": zns_template_vals,
                        }
                    )
                )
                regis.message_post(
                    body=Markup(
                        "Create SMS in queue: <a href='#' data-oe-model='sms.sms' data-oe-id='{sms_id}'>{sms_name}</a>"
                    ).format(
                        sms_id=sms.id,
                        sms_name="%s-%s" % (sms.partner_id.name, sms.number),
                    )
                )

    def btn_cancel(self):
        for regis in self:
            if regis.is_add_loyalty == True:
                regis.partner_id.loyalty_point_amount -= regis.total_amount / 1000
                regis.is_add_loyalty = False
            regis.write({"state": "cancel"})

    def btn_set_to_draft(self):
        for regis in self:
            regis.write({"state": "new"})
