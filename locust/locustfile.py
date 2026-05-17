import random
import uuid
from locust import HttpUser, task, between, events


DEVICE_IDS: list[str] = []
USER_IDS: list[str] = []


class DeviceAnalyticsUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self):

        # Create user
        username = f"user_{uuid.uuid4().hex[:8]}"
        resp = self.client.post(
            "/api/v1/users/",
            json={"username": username, "email": f"{username}@test.com"},
        )
        if resp.status_code == 201:
            user_id = resp.json()["id"]
            USER_IDS.append(user_id)
            self.user_id = user_id
        else:
            self.user_id = None

        # Create device
        resp = self.client.post(
            "/api/v1/devices/",
            json={
                "name": f"Device-{uuid.uuid4().hex[:6]}",
                "owner_id": self.user_id,
            },
        )
        if resp.status_code == 201:
            device_id = resp.json()["id"]
            DEVICE_IDS.append(device_id)
            self.device_id = device_id

            for _ in range(10):
                self._post_measurement()
        else:
            self.device_id = None

    def _post_measurement(self):
        if not self.device_id:
            return
        self.client.post(
            f"/api/v1/devices/{self.device_id}/measurements",
            json={
                "x": random.uniform(-100, 100),
                "y": random.uniform(-100, 100),
                "z": random.uniform(-100, 100),
            },
            name="/api/v1/devices/{id}/measurements [POST]",
        )

    @task(5)
    def post_measurement(self):
        self._post_measurement()

    @task(3)
    def get_device_analytics(self):
        device_id = self.device_id or (DEVICE_IDS[0] if DEVICE_IDS else None)
        if not device_id:
            return
        self.client.get(
            f"/api/v1/analytics/devices/{device_id}",
            name="/api/v1/analytics/devices/{id}",
        )

    @task(2)
    def get_user_analytics(self):
        user_id = self.user_id or (USER_IDS[0] if USER_IDS else None)
        if not user_id:
            return
        self.client.get(
            f"/api/v1/analytics/users/{user_id}",
            name="/api/v1/analytics/users/{id}",
        )

    @task(2)
    def post_device_analytics_async(self):
        device_id = self.device_id or (DEVICE_IDS[0] if DEVICE_IDS else None)
        if not device_id:
            return
        resp = self.client.post(
            f"/api/v1/analytics/devices/{device_id}/async",
            name="/api/v1/analytics/devices/{id}/async [POST]",
        )
        if resp.status_code == 200:
            task_id = resp.json().get("task_id")
            if task_id:
                self.client.get(
                    f"/api/v1/analytics/tasks/{task_id}",
                    name="/api/v1/analytics/tasks/{task_id}",
                )

    @task(1)
    def list_devices(self):
        self.client.get("/api/v1/devices/", name="/api/v1/devices/")

    @task(1)
    def health_check(self):
        self.client.get("/health", name="/health")
