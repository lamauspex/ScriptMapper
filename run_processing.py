
"""
Запуск обработки сценария
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from script_loader import ScriptLoader

load_dotenv(dotenv_path='.env')


def main():
    # Путь к тестовому файлу
    script_file = os.getenv('SCRIPT_FILE')
    output_format = os.getenv('OUTPUT_FORMAT')
    output_dir = os.getenv('OUTPUT_DIR')
    enable_logging = os.getenv('ENABLE_LOGGING')
    verbose_output = os.getenv('VERBOSE_OUTPUT')

    print("ЗАПУСК ОБРАБОТКИ СЦЕНАРИЯ")
    print("=" * 50)
    print(f" Файл: {script_file}")
    print(f"Выходная папка: {output_dir}")
    print(f"Формат вывода: {output_format}")

    # Проверяем существование файла
    if not os.path.exists(script_file):
        print(f" Файл {script_file} не найден!")
        print("Проверьте путь в .env файле или текущую директорию")
        return False

    try:
        # Создаем выходную директорию
        if output_dir != '.':
            os.makedirs(output_dir, exist_ok=True)

        # Создаем загрузчик сценариев
        loader = ScriptLoader()

        print("Начинаем обработку...")

        # Обрабатываем файл
        result = loader.load_script(script_file)

        # Показываем основную информацию
        print("\n ОБРАБОТКА ЗАВЕРШЕНА УСПЕШНО!")
        print("\n ОСНОВНАЯ СТАТИСТИКА:")
        print(f"Формат файла: {result['file_info']['extension']}")
        print(f"Размер файла: {result['file_info']['size']:,} байт")
        print(
            f"Символов в сыром тексте: {result['text_info']['raw_length']:,}")
        print(
            f"Символов в очищенном тексте:"
            f"{result['text_info']['cleaned_length']:,}"
        )
        print(f"Сцен найдено: {result['text_info']['scene_count']}")

        # Создаем имена выходных файлов
        base_name = Path(script_file).stem
        if output_dir != '.':
            base_path = Path(output_dir) / base_name
        else:
            base_path = base_name

        # Сохраняем результаты в зависимости от формата
        if output_format in ['json', 'both']:
            json_file = f"{base_path}.json"
            loader.save_to_json(result, json_file)
            print(f"JSON сохранен: {json_file}")

        if output_format in ['text', 'both']:
            text_file = f"{base_path}_analysis.txt"
            loader.save_to_text(result, text_file)
            print(f"Текстовый анализ сохранен: {text_file}")

        if verbose_output:
            # Показываем информацию о первых сценах
            print("\nПЕРВЫЕ 3 СЦЕНЫ:")
            print("-" * 40)

        for i, scene in enumerate(result['scenes'][:3]):
            print(f"\nСцена {scene['number']}: {scene['title']}")
            print(f"Локация: {scene['location']}")
            print(f"Тип: {scene['metadata']['scene_type']}")
            print(f"Строк в сцене: {scene['metadata']['line_count']}")
            print(f"Слов в сцене: {scene['metadata']['word_count']}")
            print(
                f"Есть диалоги: {'Да' if scene['metadata']['has_dialogue'] else 'Нет'}")

        if len(result['scenes']) > 3:
            print(f"\n... и еще {len(result['scenes']) - 3} сцен")

        # Показываем распределение по типам сцен
        scene_types = {}
        for scene in result['scenes']:
            scene_type = scene['metadata']['scene_type']
            scene_types[scene_type] = scene_types.get(scene_type, 0) + 1

        print("\nРАСПРЕДЕЛЕНИЕ ПО ТИПАМ СЦЕН:")
        for scene_type, count in scene_types.items():
            print(f"   {scene_type}: {count} сцен")

        print(f"\nГОТОВО! Результаты сохранены в папку: {output_dir}")

        return True

    except Exception as e:
        print(f"ОШИБКА при обработке: {e}")
        if enable_logging:
            import traceback
            traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
