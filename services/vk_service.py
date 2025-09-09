import logging
import vk_api
from vk_api.exceptions import VkApiError
from typing import List, Tuple, Optional, Dict, Any

from config.settings import config
from database.models import VKUser

from utils import VKAPIError

logger = logging.getLogger(__name__)


class VKService:
    def __init__(self):
        self.user_session = vk_api.VkApi(token=config.VK.USER_TOKEN)
        self.user_vk = self.user_session.get_api()

        self.group_session = vk_api.VkApi(token=config.VK.GROUP_TOKEN)
        self.group_vk = self.group_session.get_api()

        # Проверяем токены
        self._validate_tokens()
        
    def get_user_info(self, user_id: int) -> Optional[VKUser]:
        """Получает информацию о пользователе ВКонтакте"""
        try:
            response = self.group_vk.users.get(
                user_ids=user_id,
                fields='city,sex,bdate,domain',
                lang='ru'
            )

            if not response:
                return None

            user_data = response[0]

            # Извлекаем возраст из даты рождения
            age = self._calculate_age(user_data.get('bdate'))

            # Извлекаем город
            city = user_data.get('city', {}).get('title') if isinstance(user_data.get('city'), dict) else user_data.get('city')

            # Формируем ссылку на профиль
            domain = user_data.get('domain', f'id{user_id}')
            profile_link = f'https://vk.com/{domain}'
            
            return VKUser(
                vk_id=user_id,
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                age=age,
                city=city,
                sex=user_data.get('sex', 0),
                profile_link=profile_link
            )

        except VkApiError as e:
            logger.error(f"VK API Error getting user info: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting user info: {e}")
            return None

    def get_city_id(self, city_name: str) -> Optional[int]:
        """Получает ID города по названию"""
        try:
            # Используем пользовательский токен для получения ID города
            response = self.user_vk.database.getCities(
                country_id=1,  # Россия
                q=city_name,
                count=1
            )
            
            cities = response.get('items', [])
            if cities:
                return cities[0]['id']
            return None
            
        except VkApiError as e:
            logger.error(f"VK API Error getting city ID: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting city ID: {e}")
            return None

    def search_users(self, age: int, sex: int, city: str, offset: int = 0) -> List[Dict[str, Any]]:
        """Ищет пользователей по критериям"""
        try:
            # Определяем пол для поиска (инвертируем)
            search_sex = 1 if sex == 2 else 2 if sex == 1 else 0
            
            # Вычисляем возрастные границы
            age_from = max(18, age - config.VK.MAX_AGE_DIFFERENCE)
            age_to = min(100, age + config.VK.MAX_AGE_DIFFERENCE)
            
            # Получаем ID города
            city_id = self.get_city_id(city)
            if not city_id:
                logger.warning(f"Could not find city ID for: {city}")
                return []
            
            response = self.user_vk.users.search(
                count=config.VK.SEARCH_LIMIT,
                offset=offset,
                age_from=age_from,
                age_to=age_to,
                sex=search_sex,
                city=city_id,
                has_photo=1,
                fields='is_closed,can_access_closed,domain',
                v=config.VK.API_VERSION
            )

            # Фильтруем только открытые профили
            open_profiles = [
                user for user in response.get('items', [])
                if not user.get('is_closed', True) and user.get('can_access_closed', False)
            ]

            return open_profiles

        except VkApiError as e:
            logger.error(f"VK API Error searching users: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching users: {e}")
            return []
    # Добавим метод создания ссылки на профиль
    
    def create_profile_link(self, vk_id: int, domain: Optional[str] = None) -> str:
        """
        Создает ссылку на профиль ВКонтакте
    
        Args:
            vk_id: ID пользователя
            domain: Имя пользователя (если есть)
        
        Returns:
            str: Ссылка на профиль
        """
        if domain and domain != f"id{vk_id}":
            return f"https://vk.com/{domain}"
        else:
            return f"https://vk.com/{domain}"


    def get_top_photos(self, user_id: int) -> List[Tuple[str, int]]:
        """Получает топ-3 фотографии пользователя по лайкам"""
        try:
            response = self.user_vk.photos.get(
                owner_id=user_id,
                album_id='profile',
                extended=1,
                count=100,
                v=config.VK.API_VERSION
            )

            if not response or 'items' not in response:
                return []

            # Сортируем фотографии по количеству лайков
            sorted_photos = sorted(
                response['items'],
                key=lambda x: x.get('likes', {}).get('count', 0),
                reverse=True
            )

            # Берем топ-3 фотографии
            top_photos = sorted_photos[:config.VK.PHOTOS_LIMIT]

            # Формируем список в формате (attachment_string, likes_count)
            result = []
            for photo in top_photos:
                attachment_str = f"photo{photo['owner_id']}_{photo['id']}"
                likes_count = photo.get('likes', {}).get('count', 0)
                result.append((attachment_str, likes_count))

            return result
            
        except VkApiError as e:
            logger.error(f"VK API Error getting photos: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting photos: {e}")
            return []

    async def send_message(self, user_id: int, message: str,
                     keyboard: Optional[str] = None,
                     attachment: Optional[str] = None) -> bool:
        """Отправляет сообщение пользователю"""
        try:
            params = {
                'user_id': user_id,
                'message': message,
                'random_id': 0,
                'v': config.VK.API_VERSION
            }

            if keyboard:
                params['keyboard'] = keyboard

            if attachment:
                params['attachment'] = attachment

            self.group_vk.messages.send(**params)
            return True

        except VkApiError as e:
            logger.error(f"VK API Error sending message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return False

    def _calculate_age(self, bdate: Optional[str]) -> Optional[int]:
        """Вычисляет возраст из даты рождения"""
        if not bdate:
            return None

        try:
            parts = bdate.split('.')
            if len(parts) == 3:
                from datetime import datetime
                birth_date = datetime.strptime(bdate, "%d.%m.%Y")
                today = datetime.today()

                age = today.year - birth_date.year
                # Проверяем, был ли уже день рождения в этом году
                if (today.month, today.day) < (birth_date.month, birth_date.day):
                    age -= 1

                return age
        except (ValueError, AttributeError):
            pass
        return None

    def _validate_tokens(self):
        """Проверяет валидность VK токенов"""
        try:
            # Проверяем user token
            self.user_vk.users.get(user_ids=1)
            logger.info("✅ User token valid")
        except Exception as e:
            logger.error(f"❌ Invalid user token: {e}")
            raise VKAPIError(f"Invalid user token: {e}") from e

        try:
            # Проверяем group token
            self.group_vk.groups.getById()
            logger.info("✅ Group token valid")
        except Exception as e:
            logger.error(f"❌ Invalid group token: {e}")
            raise VKAPIError(f"Invalid group token: {e}") from e