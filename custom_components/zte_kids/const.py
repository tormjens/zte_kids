"""Constants for the ZTE Kids Watch integration."""

DOMAIN = "zte_kids"

# Default poll interval (seconds). These watches don't report faster than ~1-2 min.
DEFAULT_SCAN_INTERVAL = 180

# International (care-api.nubia.com) build constants, from decompiled com.nubia.care
# v2.7.7.A (eb/b.java, else / ".com" branch). Used only to speak the app's own protocol
# against the user's own account.
BASE = "https://care-api.nubia.com/"
APP_KEY = "U7yJRy5eO0DKTlNVrnx4z5ICm5y16a4S"   # eb.b.f()
APP_SALT = "fR1gX2AEiYxflz8sVsLFzfwTOfk8NzBu"  # eb.b.g()
AES_KEY = b"YNSSFWTeip5M2hSzmpoW4dXr0rWTc0Wr"  # eb.b.a(), AES-256
USER_AGENT = "ChildrenWatchAbroad/2.1.1 (Android)"
