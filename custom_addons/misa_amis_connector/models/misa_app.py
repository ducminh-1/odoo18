import json
import logging
import pprint
from datetime import datetime, timedelta, timezone

import pytz
import requests

from odoo import _, fields, models, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MisaApp(models.Model):
    _name = "misa.app"
    _rec_name = "org_company_code"

    access_code = fields.Char()
    org_company_code = fields.Char()
    app_id = fields.Char()
    access_token = fields.Char()
    access_token_expiry = fields.Datetime()
    tenant_code = fields.Char()
    app_name = fields.Char()
    branch_ids = fields.One2many("misa.branch", "misa_app_id")
    last_product_sync_time = fields.Datetime(string="Last Product Sync Time")
    active = fields.Boolean(default=True)

    def _get_api_url(self):
        return "https://actapp.misa.vn"

    def _make_request(
        self, endpoint, data=None, payload=None, method="POST", is_refresh=False
    ):
        url = self._get_api_url() + endpoint
        headers = {"Content-Type": "application/json"}
        # if not is_refresh_token_request:
        #     headers['Authorization'] = f'Bearer {self._paypal_fetch_access_token()}'
        if not is_refresh:
            headers["X-MISA-AccessToken"] = self._fetch_access_token()
        try:
            _logger.debug(
                "Request to %s with data:\n%s\nPayload:\n%s",
                url,
                pprint.pformat(data),
                pprint.pformat(payload),
            )
            response = requests.request(
                method, url, data=data, json=payload, headers=headers, timeout=60
            )
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                # payload = data or json_payload
                # PayPal errors https://developer.paypal.com/api/rest/reference/orders/v2/errors/
                _logger.exception(
                    "Invalid API request at %s with data:\n%s",
                    url,
                    pprint.pformat(payload),
                )
                msg = response.json()
                raise ValidationError(  # noqa: B904
                    _("The communication with the API failed. Details: %s", msg)
                )
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            _logger.exception("Unable to reach endpoint at %s", url)
            raise ValidationError(  # noqa: B904
                _("Could not establish the connection to the API.")
            )
        _logger.debug("Response from %s: %s", url, response.text)
        return response.json()

    def _fetch_access_token(self):
        def ticks_to_datetime(ticks: int) -> datetime:
            """Chuyển ticks (.NET) thành datetime (UTC)"""
            base_date = datetime(1, 1, 1, tzinfo=pytz.timezone('Asia/Ho_Chi_Minh'))
            delta = timedelta(microseconds=ticks // 10)
            dt = (base_date + delta)
            return dt.astimezone(pytz.UTC).replace(tzinfo=None)

        if (
            fields.Datetime.now() > self.access_token_expiry - timedelta(minutes=5)
        ) or not self.access_token:
            payload = {
                "access_code": self.access_code,
                "org_company_code": self.org_company_code,
                "app_id": self.app_id,
            }
            response_content = self._make_request(
                "/api/oauth/actopen/connect",
                payload=payload,
                is_refresh=True,
            )
            data = json.loads(response_content["Data"])
            access_token = data.get("access_token")
            if not access_token:
                raise ValidationError(_("Access token not found in the response."))
            self.write(
                {
                    "access_token": access_token,
                    # 'access_token_expiry': data['expired_time']
                    "access_token_expiry": ticks_to_datetime(
                        data["expired_time_ticks"]
                    ),
                }
            )
        return self.access_token

    def action_get_branches(self):
        """Fetch branches from the MISA API and update or create records."""
        payload = {
            "app_id": self.app_id,
            "data_type": 6,
            "skip": 0,
            "take": 1000,
            # "last_sync_time": False,
        }
        response = self._make_request(
            "/apir/sync/actopen/get_dictionary", payload=payload
        )
        data = json.loads(response.get("Data", []))
        _logger.debug("Branches data fetched: %s", pprint.pformat(data))
        if not data:
            raise ValidationError(_("No branches found in the MISA API."))
        for branch in data:
            branch_id = branch.get("branch_id")
            existing_branch = self.env["misa.branch"].search(
                [("misa_id", "=", branch_id)], limit=1
            )
            if existing_branch:
                existing_branch.write(
                    {
                        "name": branch.get("organization_unit_name", "123"),
                        "misa_app_id": self.id,
                    }
                )
            else:
                self.env["misa.branch"].create(
                    {
                        "misa_id": branch_id,
                        "name": branch.get("organization_unit_name", "123"),
                        "misa_app_id": self.id,
                    }
                )
        return True

    def action_test_connection(self):
        """Test the connection to the MISA API."""
        return self._fetch_access_token()

    def action_sync_products(self):
        """Sync products from MISA API and map with Odoo products"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sync Products from MISA',
            'res_model': 'misa.product.sync.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_misa_app_id': self.id,
            }
        }
        
    @api.model
    def cron_sync_products(self):
        """Scheduled action to sync products for all active apps"""
        apps = self.search([('active', '=', True)])
        for app in apps:
            app.sync_products_from_api(
                branch_id=None,
                last_sync_time=app.last_product_sync_time or None
            )

    def sync_products_from_api(self, branch_id=None, last_sync_time=None):
        if isinstance(last_sync_time, str):
            last_sync_time = fields.Datetime.to_datetime(last_sync_time)

        # ISO8601 +07:00 for MISA
        misa_last_sync_time = None
        if last_sync_time:
            if last_sync_time.tzinfo is None:
                last_sync_time = last_sync_time.replace(tzinfo=timezone.utc)
            misa_last_sync_time = last_sync_time.astimezone(
                timezone(timedelta(hours=7))
            ).isoformat()

        self.env['misa.product'].sync_products_from_misa(
            misa_app_id=self.id,
            branch_id=branch_id,
            last_sync_time=misa_last_sync_time,
        )

        self.last_product_sync_time = fields.Datetime.now()
        return self.last_product_sync_time

