import discord
from telethon import TelegramClient
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.users import GetFullUserRequest
import asyncio

# --- ТВОИ НАСТРОЙКИ ---
TG_API_ID = 00000000  # Твой ID из конфига
TG_API_HASH = '' # Твой Hash из конфига

DISCORD_BOT_TOKEN = ''
TARGET_USER_ID = 000000000000000000 # Твой ID в Discord (цифры)

# --- КОД ---

tg_client = TelegramClient('discord_session', TG_API_ID, TG_API_HASH)

intents = discord.Intents.default()
intents.presences = True
intents.members = True

class MusicSpyBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_first_name = None 
        self.original_about = None
        self.last_processed_track = None # Тут бот будет помнить, что играет

    async def on_ready(self):
        print(f'🕵️  Бот запущен. Слежу за ID: {TARGET_USER_ID}')
        await tg_client.start()
        
        # Запоминаем исходные данные при запуске
        me = await tg_client.get_me()
        full_me = await tg_client(GetFullUserRequest(me))
        
        self.original_first_name = me.first_name
        self.original_about = full_me.full_user.about
        
        print(f"✅ Данные сохранены.\nИмя: {self.original_first_name}\nБио: {self.original_about}")

    async def on_presence_update(self, before, after):
        # Реагируем только на ТВОИ изменения
        if after.id != TARGET_USER_ID:
            return

        # Ищем Spotify активность
        spotify_activity = None
        for activity in after.activities:
            if isinstance(activity, discord.Spotify):
                spotify_activity = activity
                break
        
        if spotify_activity:
            # === МУЗЫКА ИГРАЕТ ===
            track = spotify_activity.title
            artist = spotify_activity.artist
            
            # Уникальный ID текущего состояния (чтобы сравнивать)
            current_track_id = f"{track} - {artist}"
            
            # Если трек ТОТ ЖЕ САМЫЙ, что мы уже поставили -> ничего не делаем
            # Это фильтрует лишние события (например, изменение времени 01:23 -> 01:24)
            if self.last_processed_track == current_track_id:
                return 

            # Если трек новый -> Обновляем
            print(f"🎵 Новый трек: {track}")
            self.last_processed_track = current_track_id # Запоминаем новый трек
            
            new_name = f"{self.original_first_name} | 🎵 Слушает музыку"[:64]
            new_bio = f"🎵 Прямо сейчас слушает «{track}» от {artist} в Spotify!"[:70]
            
            try:
                await tg_client(UpdateProfileRequest(
                    first_name=new_name,
                    about=new_bio
                ))
            except Exception as e:
                print(f"❌ Ошибка обновления: {e}")

        else:
            # === МУЗЫКА НЕ ИГРАЕТ ===
            # Если мы думаем, что музыка играет (last_processed_track не пустой) -> Сбрасываем
            if self.last_processed_track is not None:
                print(f"⏹ Музыка закончилась. Возвращаю профиль.")
                self.last_processed_track = None # Очищаем память
                
                try:
                    await tg_client(UpdateProfileRequest(
                        first_name=self.original_first_name,
                        about=self.original_about if self.original_about else ""
                    ))
                except Exception as e:
                    print(f"❌ Ошибка возврата: {e}")

client = MusicSpyBot(intents=intents)
client.run(DISCORD_BOT_TOKEN)
