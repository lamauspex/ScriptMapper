
"""
Запуск обработки сценария
"""

import os
import sys
from dotenv import load_dotenv

from script_loader import ScriptLoader

load_dotenv(dotenv_path='.env')


def main():
    # Путь к тестовому файлу
    script_file = SCRIPT_FILE

    print("ЗАПУСК ОБРАБОТКИ СЦЕНАРИЯ")
    print("=" * 50)
    print(f" Файл: {script_file}")

    # Проверяем существование файла
    if not os.path.exists(script_file):
        print(f" Файл {script_file} не найден!")
        print(
            "Убедитесь, что файл находится в той же директории, что и скрипт"
        )
        return False

    try:
        # Создаем загрузчик сценариев
        loader = ScriptLoader()

        print(" Начинаем обработку...")

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
        base_name = os.path.splitext(script_file)[0]
        json_output = f"{base_name}_processed.json"
        text_output = f"{base_name}_analysis.txt"

        # Сохраняем результаты
        print("\nСОХРАНЯЕМ РЕЗУЛЬТАТЫ...")
        loader.save_to_json(result, json_output)
        loader.save_to_text(result, text_output)

        print(f"JSON файл: {json_output}")
        print(f"Текстовый анализ: {text_output}")

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

            # Показываем первые 100 символов содержимого
            content_preview = scene['content'][:100].replace('\n', ' ')
            if len(scene['content']) > 100:
                content_preview += "..."
            print(f"Содержимое: {content_preview}")

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

        print("\nГОТОВО! Результаты сохранены в файлы:")
        print(" {json_output} - данные в JSON")
        print(" {text_output} - читаемый анализ")

        return True

    except Exception as e:
        print(f"ОШИБКА при обработке: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
