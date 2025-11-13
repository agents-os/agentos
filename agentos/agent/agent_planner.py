"""Agent Planning and LLM Interaction Module"""

import logging
import os
import re
import time
from typing import List, Tuple

from agentos.core import utils
from agentos.core.utils import SYSTEM_PROMPT
from agentos.llm import answerer

logger = logging.getLogger(__name__)


def ask_llm(system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
    """Ask LLM with retry logic and error handling"""
    provider = utils.PROVIDER.lower()
    model = utils.MODEL

    for attempt in range(max_retries):
        try:
            logger.debug(f"LLM request (attempt {attempt + 1}): {provider}/{model}")

            if provider == "ollama":
                return answerer.get_ollama_response(
                    query=user_prompt,
                    system_prompt=system_prompt,
                    model=model,
                    temperature=0.1,
                )
            elif provider == "openai":
                return answerer.get_openai_response(
                    query=user_prompt,
                    system_prompt=system_prompt,
                    model=model,
                    temperature=0.1,
                )
            elif provider == "claude":
                return answerer.get_claude_response(
                    query=user_prompt,
                    system_prompt=system_prompt,
                    model=model,
                    temperature=0.1,
                )
            elif provider == "cohere":
                return answerer.get_cohere_response(
                    query=user_prompt,
                    system_prompt=system_prompt,
                    model=model,
                    temperature=0.1,
                )
            elif provider == "gemini":
                return answerer.get_gemini_response(
                    query=user_prompt,
                    system_prompt=system_prompt,
                    model=model,
                    temperature=0.1,
                )
            elif provider == "github":
                return answerer.get_github_response(
                    query=user_prompt,
                    system_prompt=system_prompt,
                    model=model,
                    temperature=0.1,
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")

        except Exception as e:
            logger.warning(f"LLM request failed (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                logger.error(f"All LLM attempts failed for provider {provider}")
                raise
            time.sleep(2**attempt)

    raise RuntimeError("LLM request failed after all retries")


def generate_plan(goal: str) -> List[str]:
    """Generate a simple plan to achieve the goal"""
    plan_prompt = f"""
    Current working directory: {os.getcwd()}
    Create a step-by-step plan to achieve this goal using CLI commands: {goal}
    Consider choosing how this goal should be achieved - either by writing a code to do it, or strictly using CLI commands.
    If you write code, pay attention for it to have print() statements so that you could test it in the next steps.
    If you write code, make sure you have steps to execute it.
    Enclose each step in <step></step> tags.
    Example:
    <step>First action to take</step>
    <step>Second action to take</step>
    The plan must have the smallest amount of steps as possible to achieve the goal.
    """
    plan_response = ask_llm(SYSTEM_PROMPT, plan_prompt)
    return parse_steps(plan_response)


def parse_steps(plan_response: str) -> List[str]:
    """Parse steps from the response"""
    step_pattern = r"<step>(.*?)</step>"
    steps = re.findall(step_pattern, plan_response, re.DOTALL)
    return [step.strip() for step in steps]


def execute_step(goal: str, plan: str, step: str, history: str) -> Tuple[str, str]:
    """Execute a single step of the plan"""
    step_prompt = f"""
    Task Goal: {goal}
    Plan: {plan}
    {history}
    Current Step: {step}
    Current working directory: {os.getcwd()}

    Based on the above information, determine the next CLI command to execute for this step. Follow these guidelines:

    1. Analyze the current step in the context of the overall goal and previous actions.
    2. Choose the most appropriate CLI command to accomplish this step.
    3. Ensure the command is safe and non-destructive.
    4. If the step requires multiple commands, choose only the next logical command.
    5. If the step is unclear, interpret it in the most reasonable way to progress towards the goal.

    Provide your response in this exact format:
    EXPLANATION: A brief, clear explanation of what this command will do and why it's necessary.
    COMMAND: The exact CLI command to be executed, with no additional text or formatting.

    Remember:
    - Use only standard Unix/Linux CLI commands.
    - Avoid any potentially destructive commands.
    - Consider the current working directory and the results of previous commands.
    - NEVER use text editors like nano, vim, emacs in commands.
    - Use `"` Around paths with spaces.
    """
    response = ask_llm(SYSTEM_PROMPT, step_prompt)
    explanation, command = response.split("COMMAND:", 1)
    explanation = explanation.replace("EXPLANATION:", "").strip()
    command = command.strip()
    return explanation, command
