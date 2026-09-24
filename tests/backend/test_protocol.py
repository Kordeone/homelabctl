from homelabctl.backend.protocol import (
    Request,
    Response,
    decode_request,
    decode_response,
    encode_message,
)


def test_request_round_trip():
    request = Request(
        action="ping",
        payload={
            "hello": "world",
        },
    )

    decoded = decode_request(
        encode_message(request)
    )

    assert decoded.action == "ping"
    assert decoded.payload == {
        "hello": "world",
    }


def test_response_round_trip():
    response = Response(
        ok=True,
        data={
            "mode": "read-only",
        },
    )

    decoded = decode_response(
        encode_message(response)
    )

    assert decoded.ok is True
    assert decoded.data["mode"] == "read-only"
