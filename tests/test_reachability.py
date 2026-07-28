"""The dashboard has to answer "where do I send this?", not just "is it good?".

Approving a draft with no channel wastes the only scarce thing in this system —
Manan's morning. So each card carries its channel, and the unreachable ones say
so instead of looking identical to the sendable ones.
"""

from backend.api.dashboard import contact_channel


def test_email_is_the_channel_when_there_is_one():
    c = contact_channel(email="hi@cafe.ie", contact_url=None, phone=None)
    assert c == {"kind": "email", "value": "hi@cafe.ie", "reachable": True}


def test_email_wins_over_a_form():
    c = contact_channel(email="hi@cafe.ie", contact_url="https://cafe.ie/contact",
                        phone="+353 1 234")
    assert c["kind"] == "email"


def test_a_form_is_used_when_there_is_no_address():
    c = contact_channel(email=None, contact_url="https://firm.com/contact", phone=None)
    assert c == {"kind": "form", "value": "https://firm.com/contact", "reachable": True}


def test_phone_is_the_last_resort_and_still_counts():
    """The no-website segment is a phone segment — measured 7.5% phone, 0% email.
    A phone number is a real channel; it just costs a call instead of a paste."""
    c = contact_channel(email=None, contact_url=None, phone="+1 512 555 0100")
    assert c == {"kind": "phone", "value": "+1 512 555 0100", "reachable": True}


def test_nothing_at_all_is_marked_unreachable():
    c = contact_channel(email=None, contact_url=None, phone=None)
    assert c == {"kind": "none", "value": None, "reachable": False}


def test_blank_strings_are_not_a_channel():
    """Overpass returns "" as readily as it returns None."""
    assert contact_channel(email="", contact_url="", phone="")["reachable"] is False


def test_sendable_drafts_come_first_then_the_best_scoring():
    """Manan works this list top-down in one morning. An unreachable 9/10 above a
    sendable 7/10 costs him the only scarce resource here — his attention."""
    from backend.api.dashboard import send_order

    rows = [
        {"score": 9.0, "contact": {"reachable": False}},
        {"score": 6.0, "contact": {"reachable": True}},
        {"score": 8.0, "contact": {"reachable": True}},
    ]
    assert [r["score"] for r in send_order(rows)] == [8.0, 6.0, 9.0]
