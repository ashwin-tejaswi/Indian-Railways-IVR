import pytest
from fastapi import Response
from ivr_backend import detect_intent_regex, next_step, session_context

# UNIT TESTS FOR INTENT DETECTION

def test_detect_intent_book_ticket():
    assert detect_intent_regex("I want to book a ticket") == "book_ticket"

def test_detect_intent_check_pnr():
    assert detect_intent_regex("check my PNR status") == "check_pnr"

def test_detect_intent_cancel():
    assert detect_intent_regex("cancel my reservation") == "cancel_ticket"

def test_detect_intent_fare():
    assert detect_intent_regex("what is the fare") == "fare_enquiry"

def test_detect_intent_tatkal():
    assert detect_intent_regex("tatkal details please") == "tatkal_info"

def test_detect_intent_agent():
    assert detect_intent_regex("connect me to customer care") == "talk_agent"

def test_detect_intent_assistance():
    assert detect_intent_regex("I need assistance") == "special_assistance"

def test_detect_intent_unknown():
    assert detect_intent_regex("completely random text") == "unknown"


# UNIT TESTS FOR next_step()

@pytest.mark.asyncio
async def test_next_step_ac_class():
    call_id = "u1"
    session_context[call_id] = {"last_intent": "book_ticket"}

    resp = next_step(call_id, "AC")

    assert isinstance(resp, Response)
    body = resp.body.decode()
    assert "A C class" in body
    assert session_context[call_id]["booking_class"] == "AC"


@pytest.mark.asyncio
async def test_next_step_sleeper_class():
    call_id = "u2"
    session_context[call_id] = {"last_intent": "book_ticket"}

    resp = next_step(call_id, "sleeper")
    body = resp.body.decode()

    assert "Sleeper class" in body
    assert session_context[call_id]["booking_class"] == "Sleeper"


@pytest.mark.asyncio
async def test_next_step_booking_date():
    call_id = "u3"
    session_context[call_id] = {"last_intent": "book_ticket"}

    resp = next_step(call_id, "15 November")
    body = resp.body.decode()

    assert "Booking date" in body
    assert session_context[call_id]["booking_date"] == "15 november"


@pytest.mark.asyncio
async def test_next_step_invalid_booking_reply():
    call_id = "u4"
    session_context[call_id] = {"last_intent": "book_ticket"}

    resp = next_step(call_id, "blah blah")
    body = resp.body.decode()
    assert "Please specify your class" in body

# UNIT TESTS FOR PNR FOLLOW-UP LOGIC

@pytest.mark.asyncio
async def test_valid_pnr_followup():
    call_id = "u5"
    session_context[call_id] = {"last_intent": "check_pnr"}

    resp = next_step(call_id, "1234567890")
    body = resp.body.decode()

    assert "confirmed" in body.lower()
    assert "pnr" in body.lower()


@pytest.mark.asyncio
async def test_invalid_pnr_short():
    call_id = "u6"
    session_context[call_id] = {"last_intent": "check_pnr"}

    resp = next_step(call_id, "123")
    body = resp.body.decode()
    assert "valid ten digit P N R" in body


@pytest.mark.asyncio
async def test_invalid_pnr_non_numeric():
    call_id = "u7"
    session_context[call_id] = {"last_intent": "check_pnr"}

    resp = next_step(call_id, "ABC123")
    body = resp.body.decode()
    assert "valid ten digit P N R" in body

# UNIT TESTS FOR ENDING CONVERSATION

@pytest.mark.asyncio
async def test_end_conversation_thank_you():
    call_id = "u8"
    session_context[call_id] = {"last_intent": "book_ticket"}

    resp = next_step(call_id, "thank you")
    body = resp.body.decode()

    assert "Thank you for using Indian Railways" in body
    assert "<Hangup" in body


@pytest.mark.asyncio
async def test_end_conversation_bye():
    call_id = "u9"
    session_context[call_id] = {"last_intent": "check_pnr"}

    resp = next_step(call_id, "bye")
    body = resp.body.decode()
    assert "<Hangup" in body


# =========================================================
# UNKNOWN / FALLBACK BEHAVIOR
# =========================================================

@pytest.mark.asyncio
async def test_next_step_no_context_unknown():
    call_id = "u10"
    session_context[call_id] = {}

    resp = next_step(call_id, "nonsense words")
    body = resp.body.decode()
    assert "didn’t understand" in body


@pytest.mark.asyncio
async def test_next_step_unknown_with_context():
    call_id = "u11"
    session_context[call_id] = {"last_intent": "book_ticket"}

    resp = next_step(call_id, "??")
    body = resp.body.decode()
    assert "Please specify your class" in body
