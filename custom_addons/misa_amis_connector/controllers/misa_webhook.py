from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)


class MisaWebhookController(http.Controller):

    @http.route('/misa/webhook', type='http', auth='none', methods=['GET', 'POST'], csrf=False, cors='*')
    def misa_webhook(self, **kwargs):
        """
        MISA webhook endpoint to receive callbacks
        Log all incoming data for debugging
        """
        try:
            # Log request method and headers
            _logger.info("=== MISA Webhook Received ===")
            _logger.info("Method: %s", request.httprequest.method)
            _logger.info("Headers: %s", dict(request.httprequest.headers))
            _logger.info("URL Parameters: %s", kwargs)

            # Log request body for POST requests
            if request.httprequest.method == 'POST':
                try:
                    # Try to get JSON data
                    if request.httprequest.content_type and 'json' in request.httprequest.content_type:
                        json_data = request.get_json_data()
                        _logger.info("JSON Body: %s", json.dumps(json_data, indent=2, ensure_ascii=False))
                    else:
                        # Get raw data
                        raw_data = request.httprequest.get_data()
                        _logger.info("Raw Body: %s", raw_data.decode('utf-8', errors='ignore'))

                    # Also log form data if present
                    if request.httprequest.form:
                        _logger.info("Form Data: %s", dict(request.httprequest.form))

                except Exception as e:
                    _logger.warning("Error parsing request body: %s", str(e))
                    try:
                        raw_data = request.httprequest.get_data()
                        _logger.info("Raw Body (fallback): %s", raw_data)
                    except:
                        _logger.warning("Could not read request body")

            # Log remote address
            _logger.info("Remote Address: %s", request.httprequest.remote_addr)
            _logger.info("User Agent: %s", request.httprequest.headers.get('User-Agent', 'Unknown'))

            _logger.info("=== End MISA Webhook ===")

            return http.Response(
                json.dumps({"status": "success", "message": "Webhook received"}),
                content_type='application/json',
                status=200
            )

        except Exception as e:
            _logger.error("Error in MISA webhook: %s", str(e), exc_info=True)
            return http.Response(
                json.dumps({"status": "error", "message": str(e)}),
                content_type='application/json',
                status=500
            )