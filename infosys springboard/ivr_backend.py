#MODULE 3

# Indian Railways IVR Backend (FastAPI + Twilio + Conversational AI)

# Importing Dependencies
#========================================
from fastapi import FastAPI, Request, Response, Body
from fastapi.middleware.cors import CORSMiddleware
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import os, re


# Configuration 
#=========================================
NGROK_URL = ""                
TWILIO_ACCOUNT_SID = ""      
TWILIO_AUTH_TOKEN = ""       
TWILIO_PHONE_NUMBER = ""     

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

#==============================================
# Initialize FastAPI App
app = FastAPI(title="Indian Railways Conversational IVR")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#========================================
# Regex-based Intent Recognition (Enhanced NLU)
#========================================
def detect_intent_regex(text: str) -> str:
    """
    It Detects user intent using regular expressions (regex).
    More robust than simple keyword matching.
    """
    text = text.lower()

    if re.search(r"\b(book|reserve|ticket|reservation)\b", text):
        return "book_ticket"
    elif re.search(r"\bpnr|status\b", text):
        return "check_pnr"
    elif re.search(r"\bcancel|refund\b", text):
        return "cancel_ticket"
    elif re.search(r"\bfare|cost|price|how much\b", text):
        return "fare_enquiry"
    elif re.search(r"\btatkal\b", text):
        return "tatkal_info"
    elif re.search(r"\b(agent|operator|representative|customer care)\b", text):
        return "talk_agent"
    elif re.search(r"\bassistance|help|support\b", text):
        return "special_assistance"
    else:
        return "unknown"

# ============================================================
# Context Memory (for per-call tracking)
# ============================================================
session_context = {}

# ============================================================
# Contextual Dialogue & Follow-Up Logic
# ============================================================
def next_step(call_id: str, user_text: str):
    """
    Handles follow-up conversation based on previous intent.
    """
    user_text = user_text.lower()
    context = session_context.get(call_id, {"last_intent": None})
    last_intent = context.get("last_intent")

    if last_intent == "book_ticket":
        if "ac" in user_text:
            response_text = "Booking in A C class selected. Please confirm your travel date."
            context["booking_class"] = "AC"
        elif "sleeper" in user_text:
            response_text = "Booking in Sleeper class selected. Please confirm your travel date."
            context["booking_class"] = "Sleeper"
        elif "tomorrow" in user_text or "today" in user_text:
            response_text = f"Booking date {user_text} noted. Your ticket will be processed soon. Thank you."
            context["booking_date"] = user_text
        else:
            response_text = "Please specify your class — Sleeper or A C."

    elif last_intent == "check_pnr":
        if user_text.isdigit() and len(user_text) == 10:
            response_text = f"PNR {user_text} is confirmed and the train is running on time."
        else:
            response_text = "Please provide a valid ten digit P N R number."

    else:
        response_text = "Sorry, I didn’t understand that. Could you please repeat?"

    # Save updated context
    session_context[call_id] = context

    # Respond using Twilio VoiceResponse
    resp = VoiceResponse()
    resp.say(response_text)
    return Response(content=str(resp), media_type="application/xml")

# ============================================================
# Conversational Endpoint(IVR LOGIC MAIN PART)
# ============================================================
@app.post("/conversation")
async def conversation(request: Request):
    """
    Handles speech-based or keypad-based user input during an active call.
    """
    form = await request.form()
    call_id = form.get("CallSid")
    user_text = form.get("SpeechResult", "") or form.get("Digits", "")

    print(f" Received speech from Call {call_id}: {user_text}")

    # Detecting intent using regex
    intent = detect_intent_regex(user_text)
    context = session_context.get(call_id, {})

    # Storing last intent for context
    if intent != "unknown":
        context["last_intent"] = intent
        session_context[call_id] = context

    resp = VoiceResponse()

    # Mapping the detected intents to responses
    if intent == "book_ticket":
        resp.say("You want to book a ticket. Which class would you prefer, Sleeper or A C?")
    elif intent == "check_pnr":
        resp.say("Please tell me your ten digit P N R number.")
    elif intent == "cancel_ticket":
        resp.say("Your ticket cancellation request has been received. Refunds take five to seven days.")
    elif intent == "fare_enquiry":
        resp.say("Train fare enquiry. Please tell me your train number.")
    elif intent == "tatkal_info":
        resp.say("Tatkal booking opens one day in advance at ten A M for A C and eleven A M for non A C classes.")
    elif intent == "talk_agent":
        resp.say("Connecting you to our support agent.")
        resp.dial("+911234567890")
    elif intent == "special_assistance":
        resp.say("Our assistance team will help you shortly.")
    else:
        # Fallback: handle follow-ups or repeat queries
        return next_step(call_id, user_text)

    return Response(content=str(resp), media_type="application/xml")

# ============================================================
# Start Outbound Call Endpoint
# ============================================================
@app.post("/call/start")
def start_real_call(payload: dict = Body(...)):
    """
    Initiates an outbound call via Twilio API.
    """
    to_number = payload.get("to")
    if not to_number:
        return {"error": "Missing 'to' number"}

    try:
        call = client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f"{NGROK_URL}/conversation"
        )
        print(f" Outbound call started — SID: {call.sid}, To: {to_number}")
        return {
            "status": call.status,
            "sid": call.sid,
            "to": to_number,
            "from": TWILIO_PHONE_NUMBER
        }
    except Exception as e:
        print(" Twilio call error:", e)
        return {"error": str(e)}
