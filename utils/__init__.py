"""
Utils package for VKinder Bot
"""

from .helpers import (
    VKinderError,
    VKAPIError,
    DatabaseError,
    ValidationError,
    async_retry,
    async_retry_method,
    validate_vk_user_id,
    validate_age,
    validate_city,
    validate_sex,
    parse_vk_date,
    calculate_age,
    format_user_profile,
    format_favorites_list,
    create_profile_link,
    chunk_list,
    safe_json_request,
    safe_close,
    dataclass_to_dict,
    format_timedelta,
    RateLimiter,
    DatabaseConnectionPool,
    setup_logging,
    with_error_handling,
    recover_user_state,
    # Синонимы
    validate_vk_id,
    format_profile,
    format_favorites,
)

from .data_models import UserState, StateData  # Добавляем импорт моделей

__all__ = [
    'VKinderError',
    'VKAPIError',
    'DatabaseError',
    'ValidationError',
    'async_retry',
    'async_retry_method',
    'validate_vk_user_id',
    'validate_age',
    'validate_city',
    'validate_sex',
    'parse_vk_date',
    'calculate_age',
    'format_user_profile',
    'format_favorites_list',
    'create_profile_link',
    'chunk_list',
    'safe_json_request',
    'safe_close',
    'dataclass_to_dict',
    'format_timedelta',
    'RateLimiter',
    'DatabaseConnectionPool',
    'setup_logging',
    'with_error_handling',
    'recover_user_state',
    'UserState',  # Добавляем
    'StateData',  # Добавляем
    'validate_vk_id',
    'format_profile',
    'format_favorites',
]
