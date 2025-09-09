-- Таблица пользователей бота ВКонтакте
CREATE TABLE IF NOT EXISTS vk_bot_users (   -- создаём таблицу для хранения пользователей бота
    vk_user_id INTEGER PRIMARY KEY,         -- ID пользователя ВК (основной ключ)
    first_name VARCHAR(100) NOT NULL,       -- имя, обязательное поле
    last_name VARCHAR(100) NOT NULL,        -- фамилия, обязательное поле
    age INTEGER,                            -- возраст (опционально)
    city VARCHAR(100),                      -- город (опционально)
    sex INTEGER,                            -- пол (1 = женский, 2 = мужской)
    preferred_sex INTEGER,                  -- предпочтения для поиска (1-ж, 2-м, 0-любой)
    profile_link TEXT,                      -- ссылка на профиль ВК
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- время последней активности
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- дата создания записи
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   -- дата последнего обновления
);

-- Таблица найденных пользователей
CREATE TABLE IF NOT EXISTS vk_found_users ( -- пользователи, найденные через поиск ВК
    vk_id INTEGER PRIMARY KEY,              -- ID найденного пользователя
    first_name VARCHAR(100) NOT NULL,       -- имя
    last_name VARCHAR(100) NOT NULL,        -- фамилия
    age INTEGER,                            -- возраст
    city VARCHAR(100),                      -- город
    sex INTEGER,                            -- пол
    profile_link TEXT,                      -- ссылка на профиль
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- время последнего обновления записи
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP    -- дата добавления
);

-- Таблица фотографий пользователей
CREATE TABLE IF NOT EXISTS vk_user_photos ( -- фотографии найденных пользователей
    photo_id SERIAL PRIMARY KEY,            -- ID фото (автоинкремент)
    vk_id INTEGER REFERENCES vk_found_users(vk_id) ON DELETE CASCADE, -- ссылка на найденного пользователя
    photo_url TEXT NOT NULL,                -- URL фотографии
    likes_count INTEGER DEFAULT 0,          -- количество лайков
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- дата добавления фото
);

-- Таблица избранных
CREATE TABLE IF NOT EXISTS favorites (      -- список избранных профилей
    favorite_id SERIAL PRIMARY KEY,         -- ID записи (автоинкремент)
    vk_user_id INTEGER REFERENCES vk_bot_users(vk_user_id) ON DELETE CASCADE, -- кто добавил
    favorite_vk_id INTEGER REFERENCES vk_found_users(vk_id) ON DELETE CASCADE, -- кого добавили
    notes TEXT,                             -- заметки к профилю
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- дата добавления
    UNIQUE(vk_user_id, favorite_vk_id)      -- уникальность (один и тот же профиль нельзя добавить дважды)
);

-- Таблица просмотренных профилей
CREATE TABLE IF NOT EXISTS viewed_profiles ( -- просмотренные пользователем профили
    view_id SERIAL PRIMARY KEY,             -- ID записи
    vk_user_id INTEGER REFERENCES vk_bot_users(vk_user_id) ON DELETE CASCADE, -- кто смотрел
    viewed_vk_id INTEGER REFERENCES vk_found_users(vk_id) ON DELETE CASCADE,  -- кого смотрел
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- дата просмотра
    UNIQUE(vk_user_id, viewed_vk_id)        -- нельзя просмотреть одного и того же дважды
);

-- Таблица оценок пользователей (лайки, дизлайки, черный список)
CREATE TABLE IF NOT EXISTS user_ratings (   -- хранение оценок
    rating_id SERIAL PRIMARY KEY,           -- ID записи
    vk_user_id INTEGER REFERENCES vk_bot_users(vk_user_id) ON DELETE CASCADE, -- кто оценил
    rated_vk_id INTEGER REFERENCES vk_found_users(vk_id) ON DELETE CASCADE,   -- кого оценили
    rating_type VARCHAR(20) NOT NULL CHECK (rating_type IN ('like', 'dislike', 'blacklist')), -- тип оценки
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- дата оценки
    UNIQUE(vk_user_id, rated_vk_id)         -- уникальная оценка для каждой пары
);

-- Таблица состояний пользователей
CREATE TABLE IF NOT EXISTS user_states (    -- хранение состояния пользователя (FSM)
    state_id SERIAL PRIMARY KEY,            -- ID записи
    vk_user_id INTEGER UNIQUE REFERENCES vk_bot_users(vk_user_id) ON DELETE CASCADE, -- пользователь
    current_state VARCHAR(50) DEFAULT 'main_menu', -- текущее состояние (по умолчанию главное меню)
    state_data JSONB,                        -- дополнительные данные состояния
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- дата создания
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- дата обновления
);

-- Таблица настроек поиска пользователей
CREATE TABLE IF NOT EXISTS user_preferences ( -- настройки поиска
    user_id INTEGER PRIMARY KEY REFERENCES vk_bot_users(vk_user_id) ON DELETE CASCADE, -- пользователь
    preferences JSONB NOT NULL DEFAULT '{}'::jsonb, -- параметры поиска в формате JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- дата создания
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- дата обновления
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_vk_bot_users_city ON vk_bot_users(city);       -- индекс по городу
CREATE INDEX IF NOT EXISTS idx_vk_bot_users_age ON vk_bot_users(age);         -- индекс по возрасту
CREATE INDEX IF NOT EXISTS idx_vk_found_users_city ON vk_found_users(city);   -- индекс по городу найденных
CREATE INDEX IF NOT EXISTS idx_vk_found_users_age ON vk_found_users(age);     -- индекс по возрасту найденных
CREATE INDEX IF NOT EXISTS idx_vk_user_photos_vk_id ON vk_user_photos(vk_id); -- индекс по пользователю фото
CREATE INDEX IF NOT EXISTS idx_vk_user_photos_likes ON vk_user_photos(likes_count); -- индекс по лайкам
CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(vk_user_id);       -- индекс по избранному
CREATE INDEX IF NOT EXISTS idx_viewed_profiles_user ON viewed_profiles(vk_user_id); -- индекс по просмотрам
CREATE INDEX IF NOT EXISTS idx_user_ratings_user ON user_ratings(vk_user_id); -- индекс по оценкам
CREATE INDEX IF NOT EXISTS idx_user_ratings_type ON user_ratings(rating_type);-- индекс по типу оценки
CREATE INDEX IF NOT EXISTS idx_user_preferences_user ON user_preferences(user_id); -- индекс по настройкам

-- Функция для обновления временных меток
CREATE OR REPLACE FUNCTION update_updated_at_column() -- функция для автообновления поля updated_at
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;     -- при апдейте обновляем timestamp
    RETURN NEW;                             -- возвращаем новую запись
END;
$$ LANGUAGE plpgsql;

-- Триггер для обновления времени в vk_bot_users
CREATE OR REPLACE TRIGGER update_vk_bot_users_updated_at
    BEFORE UPDATE ON vk_bot_users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Триггер для обновления времени в user_states
CREATE OR REPLACE TRIGGER update_user_states_updated_at
    BEFORE UPDATE ON user_states
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Триггер для обновления времени в user_preferences
CREATE OR REPLACE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
