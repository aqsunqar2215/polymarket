from __future__ import annotations

import logging
import sys
from typing import Literal

import structlog


# ANSI цвета
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Основные цвета
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    
    # Фоны
    BG_RED = "\033[101m"
    BG_GREEN = "\033[102m"
    BG_YELLOW = "\033[103m"
    BG_BLUE = "\033[104m"


def colored_log_formatter(logger, method_name, event_dict):
    """Форматер логов с цветами"""
    
    timestamp = event_dict.pop("timestamp", "")
    level = event_dict.pop("level", "info").upper()
    message = event_dict.pop("message", "")
    logger_name = event_dict.pop("logger", "").split(".")[-1]
    
    # Выбор цвета по уровню
    if level == "ERROR":
        level_color = Colors.BG_RED + Colors.WHITE
    elif level == "WARNING":
        level_color = Colors.YELLOW
    elif level == "INFO":
        level_color = Colors.GREEN
    elif level == "DEBUG":
        level_color = Colors.CYAN
    else:
        level_color = Colors.WHITE
    
    # Форматирование основной части
    formatted = (
        f"{Colors.CYAN}{timestamp}{Colors.RESET} "
        f"{level_color}[{level}]{Colors.RESET} "
        f"{Colors.BLUE}{logger_name}{Colors.RESET} "
        f"{Colors.WHITE}{message}{Colors.RESET}"
    )
    
    # Добавляем остальные поля если есть
    if event_dict:
        formatted += "\n"
        for key, value in event_dict.items():
            formatted += f"  {Colors.MAGENTA}{key}{Colors.RESET}={Colors.YELLOW}{value}{Colors.RESET}\n"
    
    return formatted


def configure_logging(level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO") -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            colored_log_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )