from __future__ import annotations

from enum import Enum


class UserRequest(Enum):
    HASH = "hash"
    DIFF = "diff"

    @staticmethod
    def get_user_request_from_str(
        user_request_candidate: str,
    ) -> UserRequest:
        requests = list(UserRequest)
        user_request_candidate = user_request_candidate.lower()

        for request in requests:
            if (
                user_request_candidate == request.value
                or user_request_candidate.replace("_", " ") == request.value
            ):
                return request

        raise ValueError("Request not supported: " + user_request_candidate)
