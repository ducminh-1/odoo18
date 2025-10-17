from ..models import connector


class Contacts(connector.API):
    # Contact unsubscribed themselves.
    UNSUBSCRIBED = 1
    # Contact was unsubscribed due to an unsuccessful send.
    BOUNCED = 2
    # Contact was manually unsubscribed by user.
    MANUAL = 3

    _endpoint = "contacts"

    def get_owners(self):
        """
        Get a list of users available as contact owners
        :return: dict|str
        """
        response = self._client.session.get(f"{self.endpoint_url}/list/owners")
        return self.process_response(response)

    def get_field_list(self):
        """
        Get a list of custom fields
        :return: dict|str
        """
        response = self._client.session.get(f"{self.endpoint_url}/list/fields")
        return self.process_response(response)

    def get_segments(self):
        """
        Get a list of contact segments
        :return: dict|str
        """
        response = self._client.session.get(f"{self.endpoint_url}/list/segments")
        return self.process_response(response)

    def get_events(
        self,
        obj_id,
        search="",
        include_events=None,
        exclude_events=None,
        order_by="",
        order_by_dir="ASC",
        page=1,
    ):
        """
        Get a list of a contact's engagement events
        :param obj_id: int Contact ID
        :param search: str
        :param include_events: list|tuple
        :param exclude_events: list|tuple
        :param order_by: str
        :param order_by_dir: str
        :param page: int
        :return: dict|str
        """
        if include_events is None:
            include_events = []
        if exclude_events is None:
            exclude_events = []

        parameters = {
            "search": search,
            "includeEvents": include_events,
            "excludeEvents": exclude_events,
            "orderBy": order_by,
            "orderByDir": order_by_dir,
            "page": page,
        }
        response = self._client.session.get(
            f"{self.endpoint_url}/{obj_id}/events", params=parameters
        )
        return self.process_response(response)

    def get_contact_notes(
        self, obj_id, search="", start=0, limit=0, order_by="", order_by_dir="ASC"
    ):
        """
        Get a list of a contact's notes
        :param obj_id: int Contact ID
        :param search: str
        :param start: int
        :param limit: int
        :param order_by: str
        :param order_by_dir: str
        :return: dict|str
        """
        parameters = {
            "search": search,
            "start": start,
            "limit": limit,
            "orderBy": order_by,
            "orderByDir": order_by_dir,
        }
        response = self._client.session.get(
            f"{self.endpoint_url}/{obj_id}/notes", params=parameters
        )
        return self.process_response(response)

    def get_contact_segments(self, obj_id):
        """
        Get a segment of smart segments the contact is in
        :param obj_id: int
        :return: dict|str
        """

        response = self._client.session.get(f"{self.endpoint_url}/{obj_id}/segments")
        return self.process_response(response)

    def get_contact_campaigns(self, obj_id):
        """
        Get a segment of campaigns the contact is in
        :param obj_id: int
        :return: dict|str
        """

        response = self._client.session.get(f"{self.endpoint_url}/{obj_id}/campaigns")
        return self.process_response(response)

    def add_points(self, obj_id, points, **kwargs):
        """
        Add the points to a contact
        :param obj_id: int
        :param points: int
        :param kwargs: dict 'eventname' and 'actionname'
        :return: dict|str
        """

        response = self._client.session.post(
            f"{self.endpoint_url}/{obj_id}/points/plus/{points}", data=kwargs
        )
        return self.process_response(response)

    def subtract_points(self, obj_id, points, **kwargs):
        """
        Subtract points from a contact
        :param obj_id: int
        :param points: int
        :param kwargs: dict 'eventname' and 'actionname'
        :return: dict|str
        """

        response = self._client.session.post(
            f"{self.endpoint_url}/{obj_id}/points/minus/{points}", data=kwargs
        )
        return self.process_response(response)

    def add_dnc(
        self,
        obj_id,
        channel="email",
        reason=MANUAL,
        channel_id=None,
        comments="via API",
    ):
        """
        Adds Do Not Contact
        :param obj_id: int
        :param channel: str
        :param reason: str
        :param channel_id: int
        :param comments: str
        :return: dict|str
        """
        data = {"reason": reason, "channelId": channel_id, "comments": comments}
        response = self._client.session.post(
            f"{self.endpoint_url}/{obj_id}/dnc/add/{channel}", data=data
        )
        return self.process_response(response)

    def remove_dnc(self, obj_id, channel):
        """
        Removes Do Not Contact
        :param obj_id: int
        :param channel: str
        :return: dict|str
        """
        response = self._client.session.post(
            f"{self.endpoint_url}/{obj_id}/dnc/remove/{channel}"
        )
        return self.process_response(response)

    def get_info(self, id):  # noqa
        """
        Get a list of custom fields
        :return: dict|str
        """
        response = self._client.session.get(f"{self.endpoint_url}/{id}")
        return self.process_response(response)


class Segments(connector.API):
    _endpoint = "segments"

    def add_contact(self, segment_id, contact_id):
        """
        Add a contact to the segment

        :param segment_id: int Segment ID
        :param contact_id: int Contact ID
        :return: dict|str
        """

        response = self._client.session.post(
            f"{self.endpoint_url}/{segment_id}/contact/add/{contact_id}"
        )
        return self.process_response(response)
