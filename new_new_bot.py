import asyncio
import re
import xml.etree.ElementTree as ET
from typing import Dict

import nltk
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from nltk.corpus import wordnet
from transformers import pipeline

# Загрузка необходимых ресурсов NLTK
nltk.download("wordnet")
nltk.download("omw-1.4")
nltk.download("punkt")

# Токен бота 
BOT_TOKEN = "7679561637:AAG7dtHbfTbyhlaU9ZlqHBtIB_m1vvaJAJE"

# Путь к файлу с параллельным корпусом в формате TMX
TMX_FILE = "C:\\Users\\infinix\\Desktop\\it-ru (3).tmx"

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Модель перевода для перевода определений с английского на русский
translator = pipeline("translation", model="Helsinki-NLP/opus-mt-en-ru")

# Словарь для хранения последней команды каждого пользователя
# Формат: {user_id: last_command}
user_commands: Dict[int, str] = {}


@dp.message(Command("start"))
async def start(message: types.Message) -> None:
    """Обработчик команды /start.
    
    Отправляет приветственное сообщение с описанием доступных команд.
    
    Args:
        message: Входящее сообщение от пользователя.
    """
    await message.answer(
        "Привет! Я бот-помощник в изучении итальянского языка.\n"
        "Используй команды:\n"
        "/meanings - поиск значений и синонимов слова\n"
        "/examples - примеры употребления слова в контексте"
    )


def find_meanings(word: str) -> str:
    """Находит значения итальянского слова и его синонимы (если есть).

    Использует WordNet для поиска значений слова и переводит определения
    с английского на русский.

    Args:
        word: Итальянское слово, введенное пользователем.

    Returns:
        Строка с дефинициями и синонимами или сообщение
        об ошибке, если слово не найдено.
    """
    synsets = wordnet.synsets(word, lang="ita")
    if not synsets:
        return f"❌ Слово '{word}' не найдено в словаре."

    result = f"Значения слова {word}:\n"
    for i, synset in enumerate(synsets, 1):
        # создаем список синонимов без самого слова, введенного пользователем
        synonyms = [lemma for lemma in synset.lemma_names("ita") if lemma != word] 
        definition = synset.definition()
        translated_def = translator(definition)[0]["translation_text"]
        
        result += f"\n💡 {i}. {translated_def}\n"
        if synonyms:
            result += f"📝 Синонимы: {', '.join(synonyms)}\n"
    
    return result


def find_examples(file_path: str, word: str) -> str:
    """Ищет примеры употребления слова в итало-русском параллельном корпусе.

    Args:
        file_path: Путь к TMX-файлу параллельного корпуса.
        word: Итальянское слово, введенное прльзователем.

    Returns:
        5 примеров употребления введенного слова в контексте или сообщение
        об отсутствии результатов.
    """
    tree = ET.parse(file_path)
    root = tree.getroot()
    examples = []
    word_pattern = re.compile(rf"\b{re.escape(word)}\b", flags=re.IGNORECASE)

    for tu in root.findall(".//tu"):
        segments = []
        for seg in tu.findall("tuv/seg"):
            if seg.text is not None:
                segments.append(seg.text.strip())

        if len(segments) >= 2 and word_pattern.search(segments[0]):
            examples.append(f"🇮🇹 {segments[0]}\n🇷🇺 {segments[1]}")
            if len(examples) >= 5:
                break

    return (
        "Примеры употребления:\n\n" + "\n\n".join(examples)
        if examples
        else f"❌ Слово '{word}' не найдено в корпусе."
    )


@dp.message(F.text & ~F.text.startswith("/"))
async def handle_word(message: types.Message) -> None:
    """Обрабатывает ввод слова пользователем после выбора команды.
    Проверяет, чтобы слово не являлось командой и состояло только из букв.
    Args:
        message: Входящее сообщение с итальянским словом.
    """
    user_id = message.from_user.id
    word = message.text.strip()

    if not word.isalpha():
        await message.answer("Пожалуйста, введите одно слово на итальянском.")
        return

    if user_id not in user_commands:
        await message.answer("Сначала выберите команду /meanings или /examples")
        return

    response = (
        find_meanings(word)
        if user_commands[user_id] == "/meanings"
        else find_examples(TMX_FILE, word)
    )
    
    await message.answer(response)
    user_commands.pop(user_id, None)  # Удаляем команду после использования


@dp.message(Command("meanings"))
async def meanings_cmd(message: types.Message) -> None:
    """Обработчик команды /meanings.
    
    Сохраняет команду и запрашивает слово у пользователя.
    
    Args:
        message: Входящее сообщение от пользователя.
    """
    user_commands[message.from_user.id] = "/meanings"
    await message.answer("Введите итальянское слово для поиска значений:")


@dp.message(Command("examples"))
async def examples_cmd(message: types.Message) -> None:
    """Обработчик команды /examples.
    
    Сохраняет команду и запрашивает слово у пользователя.
    
    Args:
        message: Входящее сообщение от пользователя.
    """
    user_commands[message.from_user.id] = "/examples"
    await message.answer("Введите итальянское слово для поиска примеров:")


async def main() -> None:
    """Основная функция для запуска бота."""
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())