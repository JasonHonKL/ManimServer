import pytest
from fastapi.testclient import TestClient


class TestLandingPage:
    def test_shows_name_form_when_no_cookie(self, client: TestClient):
        r = client.get("/")
        assert r.status_code == 200
        html = r.text
        assert "First name" in html
        assert "Last name" in html
        assert "Get Started" in html
        assert "seats remaining" in html

    def test_shows_welcome_back_when_cookie_matches_assigned_name(self, client: TestClient):
        client.get("/assign?first_name=Alice&last_name=Smith", follow_redirects=False)
        r = client.get("/")
        assert r.status_code == 200
        assert "Welcome back" in r.text
        assert "Enter Your Room" in r.text
        assert "Not Alice Smith" in r.text

    def test_shows_form_when_cookie_name_not_assigned(self, client: TestClient):
        client.cookies.set("manim_name", "Ghost")
        r = client.get("/")
        assert r.status_code == 200
        assert "get started" in r.text.lower()


class TestAssign:
    def test_assigns_new_name_to_first_room(self, client: TestClient):
        r = client.get("/assign?first_name=Alice&last_name=Smith", follow_redirects=False)
        assert r.status_code == 302
        assert "/s/student-01/" in r.headers["location"]
        assert r.cookies.get("manim_name").strip('"') == "Alice Smith"

    def test_same_name_returns_same_room(self, client: TestClient):
        r1 = client.get("/assign?first_name=Alice&last_name=Smith", follow_redirects=False)
        r2 = client.get("/assign?first_name=Alice&last_name=Smith", follow_redirects=False)
        assert r1.headers["location"] == r2.headers["location"]

    def test_different_names_get_different_rooms(self, client: TestClient):
        r1 = client.get("/assign?first_name=Alice&last_name=Smith", follow_redirects=False)
        r2 = client.get("/assign?first_name=Bob&last_name=Jones", follow_redirects=False)
        assert r1.headers["location"] != r2.headers["location"]

    def test_redirects_home_on_missing_name(self, client: TestClient):
        r = client.get("/assign", follow_redirects=False)
        assert r.status_code in (302, 307)
        assert r.headers["location"] == "/"

    def test_redirects_home_on_whitespace_name(self, client: TestClient):
        r = client.get("/assign?first_name=   &last_name=   ", follow_redirects=False)
        assert r.status_code in (302, 307)
        assert r.headers["location"] == "/"

    def test_redirects_home_when_only_first_name(self, client: TestClient):
        r = client.get("/assign?first_name=Alice&last_name=", follow_redirects=False)
        assert r.status_code in (302, 307)
        assert r.headers["location"] == "/"

    def test_redirects_home_when_only_last_name(self, client: TestClient):
        r = client.get("/assign?first_name=&last_name=Smith", follow_redirects=False)
        assert r.status_code in (302, 307)
        assert r.headers["location"] == "/"

    def test_all_three_rooms_fill_up(self, client: TestClient):
        for first, last in [("Alice", "Smith"), ("Bob", "Jones"), ("Carol", "White")]:
            r = client.get(f"/assign?first_name={first}&last_name={last}", follow_redirects=False)
            assert r.status_code == 302

        r = client.get("/assign?first_name=Dave&last_name=Brown", follow_redirects=False)
        assert r.status_code == 503
        assert "All rooms are full" in r.text

    def test_sets_cookie_with_correct_attributes(self, client: TestClient):
        r = client.get("/assign?first_name=Alice&last_name=Smith", follow_redirects=False)
        cookie = r.cookies.get("manim_name")
        assert cookie.strip('"') == "Alice Smith"

    def test_trims_whitespace_from_name(self, client: TestClient):
        r = client.get("/assign?first_name=  Alice  &last_name=  Smith  ", follow_redirects=False)
        assert r.status_code == 302
        assert r.cookies.get("manim_name").strip('"') == "Alice Smith"


class TestLeave:
    def test_leave_clears_cookie(self, client: TestClient):
        client.get("/assign?first_name=Alice&last_name=Smith", follow_redirects=False)
        r = client.post("/leave", follow_redirects=False)
        assert r.status_code == 302
        assert r.headers["location"] == "/"
        assert 'manim_name=""' in r.headers.get("set-cookie", "").lower() or \
               "manim_name=" in r.headers.get("set-cookie", "")

    def test_leave_frees_room(self, client: TestClient):
        client.get("/assign?first_name=Alice&last_name=Smith", follow_redirects=False)
        client.post("/leave", follow_redirects=False)
        r = client.get("/assign?first_name=Bob&last_name=Jones", follow_redirects=False)
        assert r.status_code == 302
        assert "/s/student-01/" in r.headers["location"]

    def test_leave_with_no_cookie_is_harmless(self, client: TestClient):
        r = client.post("/leave", follow_redirects=False)
        assert r.status_code == 302

    def test_leave_then_rejoin_same_name(self, client: TestClient):
        client.get("/assign?first_name=Alice&last_name=Smith", follow_redirects=False)
        client.post("/leave", follow_redirects=False)
        r = client.get("/assign?first_name=Alice&last_name=Smith", follow_redirects=False)
        assert r.status_code == 302


class TestAuth:
    def test_auth_allows_correct_name_for_room(self, client: TestClient):
        client.get("/assign?first_name=Alice&last_name=Smith", follow_redirects=False)
        r = client.get("/auth/student-01")
        assert r.status_code == 200

    def test_auth_rejects_wrong_name_for_room(self, client: TestClient):
        client.get("/assign?first_name=Alice&last_name=Smith", follow_redirects=False)
        client.cookies.clear()
        client.cookies.set("manim_name", "Bob Jones")
        r = client.get("/auth/student-01")
        assert r.status_code == 403

    def test_auth_rejects_missing_cookie(self, client: TestClient):
        client.get("/assign?first_name=Alice&last_name=Smith", follow_redirects=False)
        client.cookies.clear()
        r = client.get("/auth/student-01")
        assert r.status_code == 403

    def test_auth_rejects_unassigned_room(self, client: TestClient):
        client.cookies.set("manim_name", "Alice Smith")
        r = client.get("/auth/student-01")
        assert r.status_code == 403

    def test_auth_rejects_unknown_room(self, client: TestClient):
        client.cookies.set("manim_name", "Alice Smith")
        r = client.get("/auth/student-99")
        assert r.status_code == 403


class TestLockedPage:
    def test_locked_returns_html(self, client: TestClient):
        r = client.get("/locked")
        assert r.status_code == 200
        assert "Room Locked" in r.text


class TestAdmin:
    def test_admin_requires_auth(self, client: TestClient):
        r = client.get("/admin")
        assert r.status_code == 401

    def test_admin_with_valid_credentials(self, client: TestClient):
        import base64
        creds = base64.b64encode(b"admin:testpass").decode()
        r = client.get("/admin", headers={"Authorization": f"Basic {creds}"})
        assert r.status_code == 200
        assert "occupied" in r.text

    def test_admin_with_wrong_password(self, client: TestClient):
        import base64
        creds = base64.b64encode(b"admin:wrong").decode()
        r = client.get("/admin", headers={"Authorization": f"Basic {creds}"})
        assert r.status_code == 401

    def test_admin_shows_all_rooms(self, client: TestClient):
        import base64
        client.get("/assign?first_name=Alice&last_name=Smith", follow_redirects=False)
        creds = base64.b64encode(b"admin:testpass").decode()
        r = client.get("/admin", headers={"Authorization": f"Basic {creds}"})
        assert "student-01" in r.text
        assert "student-02" in r.text
        assert "student-03" in r.text
        assert "Alice Smith" in r.text
        assert "1 occupied" in r.text

    def test_admin_with_wrong_username(self, client: TestClient):
        import base64
        creds = base64.b64encode(b"root:testpass").decode()
        r = client.get("/admin", headers={"Authorization": f"Basic {creds}"})
        assert r.status_code == 401


class TestReset:
    def test_reset_from_localhost(self, client: TestClient):
        client.get("/assign?first_name=Alice&last_name=Smith", follow_redirects=False)
        r = client.post("/reset/student-01")
        assert r.status_code == 200
        assert r.json() == {"status": "ok", "room": "student-01"}

    def test_reset_frees_room(self, client: TestClient):
        client.get("/assign?first_name=Alice&last_name=Smith", follow_redirects=False)
        client.post("/reset/student-01")
        client.cookies.clear()
        r = client.get("/auth/student-01")
        assert r.status_code == 403

    def test_reset_nonexistent_room_returns_ok(self, client: TestClient):
        r = client.post("/reset/student-99")
        assert r.status_code == 200
        assert r.json()["room"] == "student-99"


class TestHealth:
    def test_health_returns_stats(self, client: TestClient):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["rooms_total"] == 3
        assert data["rooms_occupied"] == 0

    def test_health_reflects_occupancy(self, client: TestClient):
        client.get("/assign?first_name=Alice&last_name=Smith", follow_redirects=False)
        r = client.get("/health")
        assert r.json()["rooms_occupied"] == 1
