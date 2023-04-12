import uuid
from unittest import mock

from django.test import TestCase
from httmock import HTTMock, all_requests


class RenderViewTest(TestCase):
    def test_render_view(self):
        mock_user_id = uuid.uuid4()
        uuid.uuid4()
        mock_device_id = uuid.uuid4()
        mock_device = mock.Mock()

        # Mock the http request to the lorem picsum API
        test_image_path = "third_party_app_example/tests/assets/800.jpg"
        with open(test_image_path, "rb") as file:
            image_file = file.read()

        @all_requests
        def response_content(url, request):
            return {"status_code": 200, "content": image_file}

        path = (
            f"/image-gallery/render/"
            f"?device-type=BLACK_AND_WHITE_SCREEN_880X528&device-id={mock_device_id}"
        )
        with mock.patch(
            "third_party_app_example.views.authenticate_jwt"
        ) as mock_authenticate_jwt:
            mock_authenticate_jwt.return_value = (mock_user_id, mock_device)

            # Query the first time, expecting an HTTP request to the lorem picsum API
            with HTTMock(response_content):
                response = self.client.get(path=path)
                assert response.status_code == 200
            # Query the second time, expecting a cache hit
            response = self.client.get(
                path=path,
            )

            assert response.status_code == 200
