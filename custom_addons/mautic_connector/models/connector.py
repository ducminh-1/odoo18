import logging

import requests

from odoo import _

_logger = logging.getLogger(__name__)


class MauticBasicAuthClient:
    def __init__(self, base_url, username, password):
        """
        :param base_url: str Base URL for Mautic API E.g. `https://<your-domain>.mautic.net`
        :param username: str Mautic Username
        :param password: str Mautic Password
        """
        self.base_url = base_url.strip(" /")
        self.session = requests.Session()
        self.session.auth = (username, password)


class API:
    _endpoint = ""

    def __init__(self, client):
        self._client = client
        self.endpoint_url = "{base_url}/api/{endpoint}".format(
            base_url=self._client.base_url, endpoint=self._endpoint.strip(" /")
        )

    @staticmethod
    def process_response(response):
        _logger.info("Processing response from Mautic API: %s", response.url)
        if response.ok:
            return True, response.json()
        else:
            # _logger.error(
            #     "Fail to request to Mautic API. Cause: %s ." % response.content
            # )
            _logger.error(
                _("Failed to request Mautic API. Cause: {response_content}").format(
                    response_content=response.content.decode("utf-8")
                )
            )
            return False, response.content

    @staticmethod
    def action_not_supported(action):
        """
        Returns a not supported error
        :param action: str
        :return: dict
        """
        return {
            "error": {"code": 500, "message": f"{action} is not supported at this time"}
        }

    def get(self, obj_id):
        """
        Get a single item
        :param obj_id: int
        :return: dict|str
        """
        response = self._client.session.get(f"{self.endpoint_url}/{obj_id}")
        return self.process_response(response)

    def get_list(
        self,
        search="",
        start=0,
        limit=0,
        order_by="",
        order_by_dir="ASC",
        published_only=False,
        minimal=False,
        where="",
    ):
        """
        Get a list of items
        :param search: str
        :param start: int
        :param limit: int
        :param order_by: str
        :param order_by_dir: str
        :param published_only: bool
        :param minimal: bool
        :param where: str
        :return: dict|str
        """

        parameters = {}
        args = ["search", "start", "limit", "minimal"]
        for arg in args:
            if arg in locals() and locals()[arg]:
                parameters[arg] = locals()[arg]
        if where:
            parameters["where"] = where
        if order_by:
            parameters["orderBy"] = order_by
        if order_by_dir:
            parameters["orderByDir"] = order_by_dir
        if published_only:
            parameters["publishedOnly"] = "true"

        response = self._client.session.get(self.endpoint_url, params=parameters)
        _logger.info("Request URL: %s", response.url)
        return self.process_response(response)

    def get_published_list(
        self, search="", start=0, limit=0, order_by="", order_by_dir="ASC"
    ):
        """
        Proxy function to get_list with published_only set to True
        :param search: str
        :param start: int
        :param limit: int
        :param order_by: str
        :param order_by_dir: str
        :return: dict|str
        """
        return self.get_list(
            search=search,
            start=start,
            limit=limit,
            order_by=order_by,
            order_by_dir=order_by_dir,
            published_only=True,
        )

    def create(self, parameters):  # noqa
        """
        Create a new item (if supported)
        :param parameters: dict
        :return: dict|str
        """
        response = self._client.session.post(
            f"{self.endpoint_url}/new", data=parameters
        )
        return self.process_response(response)

    def edit(self, obj_id, parameters, create_if_not_exists=False):
        """
        Edit an item with option to create if it doesn't exist
        :param obj_id: int
        :param create_if_not_exists: bool
        :param parameters: dict
        :return: dict|str
        """
        if create_if_not_exists:
            response = self._client.session.put(
                f"{self.endpoint_url}/{obj_id}/edit", data=parameters
            )
        else:
            response = self._client.session.patch(
                f"{self.endpoint_url}/{obj_id}/edit", data=parameters
            )
        return self.process_response(response)

    def delete(self, obj_id):
        """
        Delete an item
        :param obj_id: int
        :return: dict|str
        """
        response = self._client.session.delete(f"{self.endpoint_url}/{obj_id}/delete")
        return self.process_response(response)
