# ui/services/ai_feedback.py
import json
import time
import requests
from ui.services.config import Config
from logger.debug import trace

class AIFeedbackService:
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.api_key = self.config.openrouter_api_key
        self.model = self.config.openrouter_model
    
    def generate_feedback(self, challenge: dict, session_log: dict, metrics: dict) -> str:
        """Generate AI feedback from challenge, session log, and metrics."""
        if not self.api_key:
            return "_AI feedback not available. Set OPENROUTER_API_KEY in .env or the settings screen_"
        
        prompt = self._build_prompt(challenge, session_log, metrics)

        max_attempts = 3
        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                response = self._call_api(prompt)
                if response is None:
                    return "_AI feedback returned an empty response_"
                return response
            except requests.exceptions.HTTPError as e:
                # 4xx means the request itself is bad (invalid API key, bad
                # model name, etc.) - retrying identical bad input won't
                # help, so fail fast with a clear, actionable message.
                status = e.response.status_code if e.response is not None else None
                if status and 400 <= status < 500:
                    trace("ai_feedback_client_error", status=status)
                    if status == 401:
                        return "_AI feedback unavailable: the configured OPENROUTER_API_KEY was rejected (check it in settings)_"
                    if status == 404:
                        return f"_AI feedback unavailable: model '{self.model}' not found on OpenRouter (check the model name in settings)_"
                    return f"_AI feedback unavailable: OpenRouter rejected the request (HTTP {status})_"
                last_error = e
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                # Transient/network-level - worth retrying.
                last_error = e
            except Exception as e:
                # Unexpected shape (bad JSON, etc.) - not worth retrying blindly.
                trace("ai_feedback_unexpected_error", error=str(e), error_type=type(e).__name__)
                return "_AI feedback failed unexpectedly - see logs for details_"

            trace("ai_feedback_retry", attempt=attempt, max_attempts=max_attempts, error=str(last_error))
            if attempt < max_attempts:
                time.sleep(attempt)  # 1s, then 2s before the next attempt

        trace("ai_feedback_exhausted", error=str(last_error))
        return "_AI feedback is temporarily unavailable (network issue reaching OpenRouter) - your PASS/FAIL result above is unaffected_"
    
    def _build_prompt(self, challenge: dict, session_log: dict, metrics: dict) -> str:
        """Build the prompt for the AI model."""
        # Challenge info
        challenge_title = challenge.get("title", "Unknown")
        challenge_description = challenge.get("description", "")
        challenge_objectives = challenge.get("objectives", [])
        challenge_difficulty = challenge.get("difficulty", "Unknown").split("[")[0]
        challenge_category = challenge.get("category", "Unknown")
        challenge_markdown = challenge.get("markdown", "")
        challenge_code = challenge.get("code", challenge.get("id", "Unknown"))
        
        # Session info
        goal_reached = session_log.get("goal_reached", False)
        commands = session_log.get("commands", [])
        checker_output = session_log.get("checker_output", "")
        checker_exit_code = session_log.get("checker_exit_code")
        checker_error = session_log.get("checker_error")
        
        # Metrics
        command_count = metrics.get("command_count", 0)
        time_seconds = metrics.get("time_seconds", 0)
        error_rate = metrics.get("error_rate", 0)
        correctness = metrics.get("correctness", 0) * 100
        
        # Format commands for display (limit to 20)
        cmd_list = []
        for i, cmd in enumerate(commands[:20], 1):
            cmd_text = cmd.get("command", "")
            output = cmd.get("output", "")
            exit_code = cmd.get("exit_code", 0)
            output_preview = output[:150] + "..." if output else "(no output)"
            cmd_list.append(f"  {i}. `{cmd_text}` (exit: {exit_code}) → {output_preview}")
        cmd_str = "\n".join(cmd_list) if cmd_list else "  (no commands)"
        
        # Objectives
        obj_str = "\n".join(f"  - {obj}" for obj in challenge_objectives[:5])

        # Checker output - the actual source of truth for pass/fail, not a
        # guess from command history. If checker_error is set, the checker
        # never produced a real verdict at all (missing interpreter, timeout,
        # couldn't stage the script) - that's a different situation from "the
        # checker ran and said no", and the model should say so plainly
        # rather than inventing a content-based explanation.
        if checker_error:
            checker_block = (
                f"The checker did NOT complete normally: {checker_error}\n"
                f"This means no real verdict on file content could be produced - "
                f"do not speculate about what might be wrong with the user's "
                f"submission itself; say the check could not run and why."
            )
        else:
            output_preview = checker_output[:500] if checker_output else "(no output)"
            checker_block = (
                f"Checker exit code: {checker_exit_code} (0 = pass, non-zero = fail)\n"
                f"Checker output:\n{output_preview}"
            )
        
        # Build the prompt
        prompt = f"""You are a strict, analytical CLI evaluator. Your job is to provide honest, critical feedback.

## Challenge Details
- **ID:** {challenge_code}
- **Title:** {challenge_title}
- **Difficulty:** {challenge_difficulty}
- **Category:** {challenge_category}
- **Description:** {challenge_description}
- **README:** {challenge_markdown}

### Challenge Objectives
{obj_str}

## User Performance
- **Goal reached:** {goal_reached}
- **Commands executed:** {command_count}
- **Time taken:** {time_seconds:.1f}s
- **Error rate:** {error_rate:.1f}%
- **Correctness:** {correctness:.1f}%

## Command History
{cmd_str}

## Checker Result (ground truth - base your explanation on this, not guesses)
{checker_block}

## Instructions
Provide a detailed performance analysis. Be honest and direct — no sugar-coating.

### If the user PASSED:
1. Acknowledge they met the goal
2. Analyze their approach: was it efficient? Did they use the right tools?
3. Identify what they did well, backed by specific commands
4. Point out what could have been better, even if they passed

### If the user FAILED:
1. State clearly that they failed
2. Explain why they failed — what went wrong?
3. Identify specific mistakes in their command sequence
4. Give a concrete plan for what to do next

### For ALL responses:
- Reference actual commands from their history
- Be specific, not generic
- Use markdown formatting: **bold** for emphasis, `code` for commands
- Use bullet points for clarity
- Keep it concise but comprehensive (4-6 bullet points)
- Speak directly to the user using "you" (second-person perspective)
- Never refer to "the user" or "they" — use "you" instead
- Example: "You used `echo` correctly" not "The user used `echo` correctly"

Return ONLY markdown-formatted text. No preamble, no explanations outside markdown.

Your feedback:"""
        
        return prompt
    
    def _call_api(self, prompt: str) -> str:
        """Call OpenRouter API."""
        import json
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/programming-sai/clice",
            "X-Title": "CLICE",
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 600,
            "temperature": 0.3,
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Debug: print the response structure
        print("🔍 API Response (first 500 chars):")
        print(json.dumps(data, indent=2)[:500])
        
        # Try different ways to extract content
        content = None
        
        # Method 1: OpenAI format
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                content = choice["message"]["content"]
            elif "text" in choice:
                content = choice["text"]
        
        # Method 2: OpenRouter specific
        if content is None and "data" in data:
            if "choices" in data["data"] and len(data["data"]["choices"]) > 0:
                content = data["data"]["choices"][0].get("text", "")
        
        # Method 3: Direct response field
        if content is None:
            content = data.get("response", None)
        
        if content is None:
            print("⚠️ Warning: Could not extract content from response")
            print(f"Full response: {json.dumps(data, indent=2)}")
            return ""
        
        return content.strip()