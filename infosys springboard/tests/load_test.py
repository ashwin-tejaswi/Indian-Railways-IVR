from locust import HttpUser, task, between

class IVRUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def simulate_call_flow(self):
        call_id = "loadtest" + str(self.environment.runner.user_count)
        self.client.post("/voice")

        self.client.post("/conversation", data={"CallSid": call_id, "SpeechResult": "book ticket"})
        self.client.post("/conversation", data={"CallSid": call_id, "SpeechResult": "AC"})
        self.client.post("/conversation", data={"CallSid": call_id, "SpeechResult": "thank you"})
        self.client.post("/call/end", data={"CallSid": call_id})
