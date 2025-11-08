"""
Модуль загрузки и обработки сценариев
Поддерживает форматы PDF и DOCX с сегментацией на сцены
"""

import os
import re
import json
from turtle import pd
import PyPDF2
import pdfplumber
from docx import Document
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Scene:
    """Структура данных для сцены"""
    number: int
    title: str
    location: str
    content: str
    raw_text: str
    metadata: Dict[str, Any]


class ScriptLoader:
    """Основной класс для загрузки и обработки сценариев"""

    def __init__(self, scene_patterns: Optional[List[str]] = None):
        """
        Инициализация загрузчика сценариев

        Args:
            scene_patterns: Список паттернов для определения начала сцен
        """
        self.scene_patterns = scene_patterns or [
            r'^\s*(?:INT\.|EXT\.|INT\/EXT\.|FADE IN:|FADE OUT:)',
            r'^\s*\d+\.\s*',
            r'^\s*(?:SCENE\s+\d+|CUT TO:)',
            r'^\s*(?:EST\.|MEDIUM|CLOSE|ANGLE)',
        ]
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for pattern in self.scene_patterns
        ]

    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Извлечение текста из PDF файла

        Args:
            file_path: Путь к PDF файлу

        Returns:
            Извлеченный текст
        """
        try:
            # Попробуем сначала pdfplumber для лучшего качества
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            logger.warning(f"pdfplumber не удался: {e}, пробуем PyPDF2")

            # Fallback на PyPDF2
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    return text
            except Exception as e2:
                logger.error(f"Ошибка извлечения текста из PDF: {e2}")
                raise

    def extract_text_from_docx(self, file_path: str) -> str:
        """
        Извлечение текста из DOCX файла

        Args:
            file_path: Путь к DOCX файлу

        Returns:
            Извлеченный текст
        """
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Ошибка извлечения текста из DOCX: {e}")
            raise

    def clean_text(self, text: str) -> str:
        """
        Очистка и структурирование текста

        Args:
            text: Исходный текст

        Returns:
            Очищенный текст
        """
        # Удаление лишних пробелов и переносов строк
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Максимум 2 переноса строки
        text = re.sub(r' +', ' ', text)  # Удаление лишних пробелов
        text = text.strip()

        # Удаление служебной информации (номера страниц, колонтитулы)
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            # Пропускаем строки, которые выглядят как номера страниц
            if re.match(r'^\d+$', line) and len(line) < 5:
                continue
            # Пропускаем очень короткие строки без букв
            if len(line) < 3 and not re.search(
                r'[а-яёa-z]', line, re.IGNORECASE
            ):
                continue
            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def segment_into_scenes(self, text: str) -> List[Scene]:
        """
        Сегментация текста на сцены

        Args:
            text: Очищенный текст

        Returns:
            Список сцен
        """
        lines = text.split('\n')
        scenes = []
        current_scene = []
        scene_number = 1

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Проверяем, является ли строка началом новой сцены
            is_new_scene = False
            for pattern in self.compiled_patterns:
                if pattern.match(line):
                    is_new_scene = True
                    break

            # Если это новая сцена и у нас есть содержимое предыдущей
            if is_new_scene and current_scene:
                scene = self._create_scene(current_scene, scene_number)
                scenes.append(scene)
                scene_number += 1
                current_scene = [line]
            else:
                current_scene.append(line)

        # Добавляем последнюю сцену
        if current_scene:
            scene = self._create_scene(current_scene, scene_number)
            scenes.append(scene)

        return scenes

    def _create_scene(self, lines: List[str], number: int) -> Scene:
        """
        Создание объекта сцены из списка строк

        Args:
            lines: Строки сцены
            number: Номер сцены

        Returns:
            Объект Scene
        """
        raw_text = '\n'.join(lines)

        # Извлекаем заголовок (обычно первая строка)
        title = lines[0] if lines else ""

        # Определяем локацию из заголовка
        location = self._extract_location(title)

        # Извлекаем метаданные
        metadata = self._extract_metadata(lines)

        return Scene(
            number=number,
            title=title,
            location=location,
            content='\n'.join(lines[1:]) if len(lines) > 1 else "",
            raw_text=raw_text,
            metadata=metadata
        )

    def _extract_location(self, title: str) -> str:
        """
        Извлечение локации из заголовка сцены

        Args:
            title: Заголовок сцены

        Returns:
            Название локации
        """
        # Ищем паттерны INT./EXT.
        location_match = re.search(
            r'(INT\.|EXT\.|INT\/EXT\.)\s*([^-]+)', title, re.IGNORECASE)
        if location_match:
            return location_match.group(2).strip()

        # Если не найдено, возвращаем часть заголовка
        return title[:50] + "..." if len(title) > 50 else title

    def _extract_metadata(self, lines: List[str]) -> Dict[str, Any]:
        """
        Извлечение метаданных из сцены

        Args:
            lines: Строки сцены

        Returns:
            Словарь с метаданными
        """
        metadata = {
            'line_count': len(lines),
            'word_count': sum(len(line.split()) for line in lines),
            'has_dialogue': any(
                line.isupper() and len(line) < 50 for line in lines
            ),
            'scene_type': self._determine_scene_type(lines)
        }

        return metadata

    def _determine_scene_type(self, lines: List[str]) -> str:
        """
        Определение типа сцены

        Args:
            lines: Строки сцены

        Returns:
            Тип сцены
        """
        title = lines[0].upper() if lines else ""

        if 'INT.' in title:
            return 'интерьер'
        elif 'EXT.' in title:
            return 'экстерьер'
        elif 'INT/EXT.' in title:
            return 'интерьер/экстерьер'
        else:
            return 'неопределен'

    def load_script(self, file_path: str) -> Dict[str, Any]:
        """
        Основной метод загрузки и обработки сценария

        Args:
            file_path: Путь к файлу сценария

        Returns:
            Словарь с результатами обработки
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        file_ext = os.path.splitext(file_path)[1].lower()

        # Извлекаем текст в зависимости от формата
        if file_ext == '.pdf':
            raw_text = self.extract_text_from_pdf(file_path)
        elif file_ext == '.docx':
            raw_text = self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {file_ext}")

        # Очищаем и структурируем текст
        cleaned_text = self.clean_text(raw_text)

        # Сегментируем на сцены
        scenes = self.segment_into_scenes(cleaned_text)

        # Формируем результат
        result = {
            'file_info': {
                'path': file_path,
                'extension': file_ext,
                'size': os.path.getsize(file_path)
            },
            'text_info': {
                'raw_length': len(raw_text),
                'cleaned_length': len(cleaned_text),
                'scene_count': len(scenes)
            },
            'scenes': [asdict(scene) for scene in scenes],
            'processed_at': str(pd.Timestamp.now()) if 'pd' in globals() else None
        }

        logger.info(
            f"Обработан файл: {file_path}, найдено сцен: {len(scenes)}")
        return result

    def save_to_json(self, data: Dict[str, Any], output_path: str) -> None:
        """
        Сохранение результатов в JSON файл

        Args:
            data: Данные для сохранения
            output_path: Путь к выходному файлу
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_to_text(self, data: Dict[str, Any], output_path: str) -> None:
        """
        Сохранение результатов в структурированный текст

        Args:
            data: Данные для сохранения
            output_path: Путь к выходному файлу
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("АНАЛИЗ СЦЕНАРИЯ\n")
            f.write("=" * 50 + "\n\n")

            # Информация о файле
            file_info = data.get('file_info', {})
            f.write(f"Файл: {file_info.get('path', 'Неизвестен')}\n")
            f.write(f"Формат: {file_info.get('extension', 'Неизвестен')}\n")
            f.write(f"Размер: {file_info.get('size', 0)} байт\n\n")

            # Статистика
            text_info = data.get('text_info', {})
            f.write("СТАТИСТИКА\n")
            f.write("-" * 20 + "\n")
            f.write(f"Количество сцен: {text_info.get('scene_count', 0)}\n")
            f.write(
                f"Символов в сыром тексте: {text_info.get('raw_length', 0)}\n")
            f.write(
                f"Символов в очищенном тексте:"
                f"{text_info.get('cleaned_length', 0)}\n\n"
            )

            # Сцены
            f.write("СЦЕНЫ\n")
            f.write("=" * 20 + "\n\n")

            for scene_data in data.get('scenes', []):
                f.write(f"СЦЕНА {scene_data.get('number', 0)}\n")
                f.write("-" * 15 + "\n")
                f.write(f"Заголовок: {scene_data.get('title', '')}\n")
                f.write(f"Локация: {scene_data.get('location', '')}\n")
                f.write(
                    f"Тип: {scene_data.get('metadata', {}).get('scene_type', '')}\n")
                f.write(
                    f"Строк: {scene_data.get('metadata', {}).get('line_count', 0)}\n")
                f.write(
                    f"Слов: {scene_data.get('metadata', {}).get('word_count', 0)}\n")
                f.write(
                    f"Диалог: {'Да' if scene_data.get(
                        'metadata',
                        {}).get('has_dialogue') else 'Нет'}\n\n")

                # Содержимое сцены
                content = scene_data.get('content', '')
                if content:
                    f.write("СОДЕРЖИМОЕ:\n")
                    f.write(f"{content}\n\n")

                f.write(f"{'='*50}\n\n")


# Пример использования
if __name__ == "__main__":
    # Создаем загрузчик с настройками по умолчанию
    loader = ScriptLoader()

    # Пример обработки файла
    # result = loader.load_script("path/to/script.pdf")
    # loader.save_to_json(result, "output.json")
    # loader.save_to_text(result, "output.txt")
