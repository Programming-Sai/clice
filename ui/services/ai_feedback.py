# ui/services/ai_feedback.py
import json
import requests
from ui.services.config import Config

class AIFeedbackService:
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.api_key = self.config.openrouter_api_key
        self.model = self.config.openrouter_model
    
    def generate_feedback(self, challenge: dict, session_log: dict, metrics: dict) -> str:
        """Generate AI feedback from challenge, session log, and metrics."""
        if not self.api_key:
            return "_AI feedback not available. Set OPENROUTER_API_KEY in .env_"
        
        prompt = self._build_prompt(challenge, session_log, metrics)
        
        try:
            response = self._call_api(prompt)
            if response is None:
                return "_AI feedback returned empty response_"
            return response
        except Exception as e:
            return f"_AI feedback error: {e}_"
    
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