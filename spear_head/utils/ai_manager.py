from constants.constants import AI_MODEL, AI_TEMPERATURE, AI_TOP_P, AI_CONTEXT_SIZE
import ollama
import json

class AIManager:
    initiated = False

    @staticmethod
    def init() -> None:
        ollama.pull(AI_MODEL)
        AIManager.initiated = True
    
    @staticmethod
    def get_json_response(system_prompt: str, user_prompt: str) -> dict[str, str] | None:
        if not AIManager.initiated:
            AIManager.init()

        print("AIManager: Sending request to AI model...")
        response = ollama.chat(
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
        print(response['message']['content'])
        raw_res = response['message']['content']
        try:
            return json.loads(raw_res)
        except json.JSONDecodeError:
            print("AIManager: Failed to decode JSON response from AI.")
            return None
