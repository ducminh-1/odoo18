import json
import logging

from odoo import http
from odoo.http import Response, request

_logger = logging.getLogger(__name__)


class Mautictest(http.Controller):
    @http.route("/mautic-test", type="http")
    def mautic_test(self):
        # content = self._test_filter_contact()
        Config = request.env["mautic.migrate.config"]
        data = Config.browse([1]).get_contact_data_from_mautic()
        _logger.info("Data from Mautic: %s", data)
        content = Config.process_contact_data(data)

        _logger.info("Processed content: %s", content)
        headers = [("Content-Type", "application/json")]
        # return request.make_response(content, headers=headers)
        return Response(json.dumps(content), headers=headers)

    def _test_filter_contact(self):
        contact = request.env["mautic.contact"]
        request.env["mautic.segment"].cron_migrate_segment_list_to_Odoo()
        cmd = (
            self._get_search_str_by_segment(
                common=True, segments_alias=["email", "gmail"]
            )
            + " "
            + self._get_search_str_by_tag("tag")
        )
        _logger.info("Search command: %s", cmd)
        return contact.Contact.get_list(search=cmd)
