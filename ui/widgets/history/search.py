# ui/widgets/history/search.py
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Input, Static
from textual.reactive import reactive
import re
from datetime import datetime, timedelta


class SearchBar(Horizontal):
    """The single search row that filters the whole table as you type."""

    def compose(self) -> ComposeResult:
        yield Static("/ Search:", id="search_label")
        yield Input(
            placeholder='type to filter... e.g. pass, fail, grep, :pass, :fail, title:hello, /regex/, ago:>3d',
            id="search_box"
        )

    def parse_query(self, query: str) -> dict:
        """Parse search query into structured filters."""
        if not query.strip():
            return {"filters": [], "regex": None, "bare": []}

        result = {
            "filters": [],      # list of (field, operator, value)
            "regex": None,      # compiled regex pattern
            "bare": []          # bare words to search across all fields
        }

        # Tokenize on whitespace
        tokens = query.split()

        for token in tokens:
            # --- STATUS SHORTCUT: :pass or :fail ---
            if token.startswith(":"):
                status_value = token[1:].upper()
                if status_value in ["PASS", "FAIL"]:
                    result["filters"].append({
                        "field": "status",
                        "operator": "=",
                        "value": status_value
                    })
                continue

            # --- Field filter: field:value or field:>value ---
            if ":" in token:
                field, _, value = token.partition(":")

                # --- DATE/TIME FILTERS: ago:>3d, date:2026-07-31 ---
                if field in ["ago", "since", "date", "after", "before"]:
                    parsed_date = self._parse_date_filter(field, value)
                    if parsed_date is not None:
                        result["filters"].append({
                            "field": "started_at",
                            "operator": "=",  # Will be handled specially in matches_session
                            "value": parsed_date,
                            "date_type": field
                        })
                    continue

                # Scoped regex: field:/pattern/
                if value.startswith("/") and value.endswith("/") and len(value) > 2:
                    try:
                        pattern = re.compile(value[1:-1], re.IGNORECASE)
                        result["filters"].append({
                            "field": field.lower(),
                            "operator": "regex",
                            "value": pattern
                        })
                    except re.error:
                        pass
                    continue

                # Operators: >, <, >=, <=, =
                operators = [">=", "<=", ">", "<", "="]
                op = "="
                for o in operators:
                    if value.startswith(o):
                        op = o
                        value = value[len(o):]
                        break

                result["filters"].append({
                    "field": field.lower(),
                    "operator": op,
                    "value": value
                })
                continue

            # --- Global regex: /pattern/ ---
            if token.startswith("/") and token.endswith("/") and len(token) > 2:
                try:
                    result["regex"] = re.compile(token[1:-1], re.IGNORECASE)
                except re.error:
                    pass
                continue

            # --- Bare word ---
            result["bare"].append(token.lower())

        return result

    def _parse_date_filter(self, field: str, value: str) -> float | None:
        """Parse date filters into a timestamp."""
        try:
            # --- ago:>3d, ago:<2h, ago:>1w ---
            if field == "ago":
                # Match patterns like: 3d, 2h, 5m, 1w, 30s
                import re
                match = re.match(r'([<>]?)(\d+)([dhmsw])', value)
                if not match:
                    return None
                
                op = match.group(1) or "="
                num = int(match.group(2))
                unit = match.group(3)
                
                now = datetime.now()
                if unit == 'd':
                    delta = timedelta(days=num)
                elif unit == 'h':
                    delta = timedelta(hours=num)
                elif unit == 'm':
                    delta = timedelta(minutes=num)
                elif unit == 's':
                    delta = timedelta(seconds=num)
                elif unit == 'w':
                    delta = timedelta(weeks=num)
                else:
                    return None
                
                target_time = now - delta
                return target_time.timestamp()
            
            # --- date:2026-07-31 ---
            elif field == "date":
                dt = datetime.strptime(value, "%Y-%m-%d")
                return dt.timestamp()
            
            # --- since:2026-07-30 ---
            elif field == "since":
                dt = datetime.strptime(value, "%Y-%m-%d")
                return dt.timestamp()
            
            # --- after:2026-07-30, before:2026-07-30 ---
            elif field in ["after", "before"]:
                dt = datetime.strptime(value, "%Y-%m-%d")
                return dt.timestamp()
            
        except (ValueError, TypeError):
            pass
        
        return None

    def matches_session(self, session: dict, parsed: dict) -> bool:
        """Check if a session matches the parsed query."""
        # Check bare words (AND logic)
        if parsed["bare"]:
            haystack = " ".join([
                session.get("challenge_code", ""),
                session.get("challenge_title", ""),
                session.get("status", ""),
                session.get("started_at", ""),
            ]).lower()

            for word in parsed["bare"]:
                if word not in haystack:
                    return False

        # Check field filters (AND logic)
        for filter in parsed["filters"]:
            field = filter["field"]
            operator = filter["operator"]
            value = filter["value"]
            date_type = filter.get("date_type")
            session_value = self._get_field_value(session, field)

            if session_value is None:
                return False

            # --- Special handling for date filters ---
            if date_type:
                # Convert session timestamp to datetime
                try:
                    from datetime import datetime
                    session_dt = datetime.fromisoformat(session_value.replace('Z', '+00:00'))
                    session_ts = session_dt.timestamp()
                except:
                    return False
                
                # ago:>3d, ago:<2h, etc.
                if date_type == "ago":
                    # The value is already a timestamp
                    if operator == ">" or operator == "=":
                        if session_ts > value:
                            return False
                    elif operator == "<":
                        if session_ts < value:
                            return False
                    # For "ago:3d" (no operator), meaning "exactly 3 days ago" - approximate
                    else:
                        # Check if within ±12 hours of the target
                        if abs(session_ts - value) > 43200:  # 12 hours in seconds
                            return False
                # since:2026-07-30 (sessions from this date onward)
                elif date_type == "since" or date_type == "after":
                    if session_ts < value:
                        return False
                # before:2026-07-30 (sessions before this date)
                elif date_type == "before":
                    if session_ts > value:
                        return False
                # date:2026-07-31 (sessions from this exact date)
                elif date_type == "date":
                    # Check if session is on this date (within 24 hours)
                    if abs(session_ts - value) > 86400:  # 24 hours in seconds
                        return False
                continue

            # --- Regular field filters ---
            if operator == "regex":
                if not value.search(str(session_value)):
                    return False
            elif operator == "=":
                # Special handling for status (case-insensitive exact match -
                # "PASS" shouldn't match a session whose status merely
                # contains "pass" as a substring of something else).
                if field == "status":
                    if str(session_value).upper() != str(value).upper():
                        return False
                # Text fields use substring/contains matching, matching how
                # the regex and bare-word paths already behave - title:hello
                # should match "Hello CLICE Challenge" the same way a bare
                # "hello" search would, not require the whole title to be
                # exactly "hello". Numeric/other fields keep exact matching,
                # since exact comparison is what those actually mean.
                elif field in ("title", "challenge", "code"):
                    if str(value).lower() not in str(session_value).lower():
                        return False
                else:
                    if str(session_value).lower() != str(value).lower():
                        return False
            elif operator == ">":
                try:
                    if float(session_value) <= float(value):
                        return False
                except:
                    return False
            elif operator == "<":
                try:
                    if float(session_value) >= float(value):
                        return False
                except:
                    return False
            elif operator == ">=":
                try:
                    if float(session_value) < float(value):
                        return False
                except:
                    return False
            elif operator == "<=":
                try:
                    if float(session_value) > float(value):
                        return False
                except:
                    return False

        # Check global regex
        if parsed["regex"]:
            haystack = " ".join([
                session.get("challenge_code", ""),
                session.get("challenge_title", ""),
                session.get("status", ""),
                session.get("started_at", ""),
            ])
            if not parsed["regex"].search(haystack):
                return False

        return True

    def _get_field_value(self, session: dict, field: str) -> any:
        """Get a field value from a session for filtering."""
        field_map = {
            "challenge": "challenge_code",
            "code": "challenge_code",
            "title": "challenge_title",
            "status": "status",
            "commands": "command_count",
            "cmds": "command_count",
            "duration": "duration_seconds",
            "time": "duration_seconds",
            "date": "started_at",
            "timestamp": "started_at",
        }

        key = field_map.get(field, field)
        return session.get(key)