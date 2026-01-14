from constants.constants import AI_MODEL, AI_TEMPERATURE, AI_TOP_P, AI_CONTEXT_SIZE
import ollama
import json

from models.logger import Logger

class AIManager:
    initiated = False

    @staticmethod
    def init() -> bool:
        Logger.info("Initializing AI Manager...")
        try:
            ollama.pull(AI_MODEL)
            AIManager.initiated = True
        except Exception as e:
            Logger.error(f"[AIManager] Failed to initialize AI model: {e}")
            return False
    
    @staticmethod
    def get_json_response(system_prompt: str, user_prompt: str) -> dict[str, str] | None:
        if not AIManager.initiated:
            succ = AIManager.init()
            if not succ:
                return None

        Logger.debug("[AIManager] Sending request to AI model...")
        response = ollama.chat( # type: ignore
            model=AI_MODEL,
            format='json',
            options={
                'temperature': AI_TEMPERATURE,
                'top_p': AI_TOP_P,
                'num_ctx': AI_CONTEXT_SIZE,
                'stream': False
            },
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
        )

        raw_res = response['message']['content']
        try:
            return json.loads(raw_res)
        except json.JSONDecodeError:
            Logger.error("[AIManager] Failed to decode AI response as JSON.")
            return None
