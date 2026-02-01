# app/services/llm.py
import ollama
import asyncio

class LLMService:
    async def generate_stream(self, prompt):
        """Yields text chunks."""
        resp = ollama.chat(
            model='llama3.2:1b', 
            messages=[{'role':'user','content':prompt}],
            stream=True
        )
        for chunk in resp:
            content = chunk['message']['content']
            yield content
            await asyncio.sleep(0) 

llm_service = LLMService()