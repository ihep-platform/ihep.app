"""
Ollama LLM Client for IHEP Agent Swarm

Provides local LLM integration using Ollama for privacy-first operation.
No PHI leaves the system.

Author: Jason M Jarmacz | jason@ihep.app
Co-Author: Claude by Anthropic
"""

import os
from typing import Optional, Dict, Any, Generator
from dataclasses import dataclass
from loguru import logger

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("Ollama package not installed. LLM features will be limited.")


@dataclass
class LLMConfig:
    """Configuration for LLM models"""
    model: str = "llama3"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9
    stream: bool = False


# Model configurations by purpose
MODEL_CONFIGS: Dict[str, LLMConfig] = {
    "general": LLMConfig(model="llama3", temperature=0.7),
    "code": LLMConfig(model="codellama", temperature=0.3, max_tokens=8192),
    "reasoning": LLMConfig(model="llama3:70b", temperature=0.5),
    "clinical": LLMConfig(model="llama3", temperature=0.4),  # medllama2 if available
}


class OllamaClient:
    """
    Local Ollama LLM client for IHEP Agent Swarm.

    Provides privacy-first LLM access with no data leaving the local system.
    Supports multiple models for different use cases.
    """

    def __init__(self, host: Optional[str] = None):
        """
        Initialize Ollama client.

        Args:
            host: Ollama server host (default: http://localhost:11434)
        """
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.available_models: list = []
        self._check_connection()

    def _check_connection(self) -> bool:
        """Check if Ollama server is available"""
        if not OLLAMA_AVAILABLE:
            logger.error("Ollama package not installed")
            return False

        try:
            # List available models to verify connection
            response = ollama.list()
            self.available_models = [m["name"] for m in response.get("models", [])]
            logger.info(f"Connected to Ollama. Available models: {self.available_models}")
            return True
        except Exception as e:
            logger.warning(f"Could not connect to Ollama: {e}")
            return False

    def query(
        self,
        prompt: str,
        model: str = "llama3",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """
        Query the LLM with a prompt.

        Args:
            prompt: The user prompt to send
            model: Model to use (llama3, codellama, etc.)
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        if not OLLAMA_AVAILABLE:
            return self._fallback_response(prompt)

        try:
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            response = ollama.chat(
                model=model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            )

            return response["message"]["content"]

        except Exception as e:
            logger.error(f"Ollama query failed: {e}")
            return self._fallback_response(prompt)

    def query_stream(
        self,
        prompt: str,
        model: str = "llama3",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """
        Stream query response from LLM.

        Yields chunks of generated text as they become available.
        """
        if not OLLAMA_AVAILABLE:
            yield self._fallback_response(prompt)
            return

        try:
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            stream = ollama.chat(
                model=model,
                messages=messages,
                stream=True,
                options={"temperature": temperature}
            )

            for chunk in stream:
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]

        except Exception as e:
            logger.error(f"Ollama stream failed: {e}")
            yield self._fallback_response(prompt)

    def query_for_code(self, prompt: str, language: str = "python") -> str:
        """
        Query optimized for code generation.

        Uses codellama model with lower temperature for more deterministic output.
        """
        system_prompt = f"""You are an expert {language} developer.
Generate clean, well-documented, production-ready code.
Follow best practices and include error handling.
Do not include explanations unless specifically asked - just output the code."""

        return self.query(
            prompt=prompt,
            model="codellama",
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=8192,
        )

    def query_for_analysis(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """
        Query optimized for analysis and reasoning.

        Uses larger model with moderate temperature for thoughtful analysis.
        """
        system_prompt = """You are a senior software architect and analyst.
Provide thorough, well-reasoned analysis with clear recommendations.
Consider security, performance, and maintainability in your analysis.
Structure your response with clear headings and actionable items."""

        if context:
            prompt = f"Context:\n{context}\n\nAnalysis Request:\n{prompt}"

        model = "llama3:70b" if "llama3:70b" in self.available_models else "llama3"

        return self.query(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=0.5,
            max_tokens=4096,
        )

    def query_for_task_decomposition(self, objective: str, constraints: Dict[str, Any] = None) -> str:
        """
        Query optimized for task decomposition.

        Breaks down complex objectives into actionable tasks with dependencies.
        """
        system_prompt = """You are a project manager and systems analyst.
Decompose the given objective into specific, actionable tasks.
For each task, specify:
1. Task description
2. Estimated complexity (low/medium/high)
3. Dependencies (task IDs)
4. Required skills/MOS
5. Expected output

Format as JSON array of task objects."""

        prompt = f"Objective: {objective}"
        if constraints:
            prompt += f"\n\nConstraints: {constraints}"

        return self.query(
            prompt=prompt,
            model="llama3",
            system_prompt=system_prompt,
            temperature=0.4,
            max_tokens=4096,
        )

    def _fallback_response(self, prompt: str) -> str:
        """
        Fallback response when Ollama is unavailable.

        Returns a structured placeholder that can be processed by the agent.
        """
        return f"""[OLLAMA_UNAVAILABLE]
Unable to process request. Ollama server not available.

Original prompt: {prompt[:200]}...

Recommended actions:
1. Ensure Ollama is installed: curl -fsSL https://ollama.com/install.sh | sh
2. Start Ollama: ollama serve
3. Pull required models: ollama pull llama3 && ollama pull codellama
"""

    def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model"""
        if not OLLAMA_AVAILABLE:
            return None

        try:
            return ollama.show(model)
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return None

    def pull_model(self, model: str) -> bool:
        """Pull a model from Ollama library"""
        if not OLLAMA_AVAILABLE:
            return False

        try:
            logger.info(f"Pulling model: {model}")
            ollama.pull(model)
            self._check_connection()  # Refresh available models
            return True
        except Exception as e:
            logger.error(f"Failed to pull model: {e}")
            return False

    def is_model_available(self, model: str) -> bool:
        """Check if a model is available locally"""
        return model in self.available_models or any(
            model in m for m in self.available_models
        )
