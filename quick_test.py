

"""
Быстрый тест обработки сценария
Проверяет работоспособность без полной обработки
"""

import os
from dotenv import load_dotenv

from script_loader import ScriptLoader

load_dotenv(dotenv_path='.env')


def quick_test():
    """Быстрый тест функциональности"""

    # Получаем настройки из переменных окружения
    script_file = os.getenv('SCRIPT_FILE')

    print("БЫСТРЫЙ ТЕСТ ОБРАБОТЧИКА СЦЕНАРИЕВ")
    print("=" * 45)

    # 1. Проверяем файл
    print(f"1. Проверка файла: {script_file}")
    if os.path.exists(script_file):
        print(
            f"Файл найден (размер: {os.path.getsize(script_file):,} байт)")
    else:
        print("Файл не найден!")
        return False

    # 2. Проверяем импорты
    print("\n2. Проверка зависимостей:")
    try:
        import PyPDF2
        print(f"PyPDF2: {PyPDF2.__version__}")
    except ImportError:
        print("PyPDF2 не установлен")
        return False

    try:
        import pdfplumber
        print(f"pdfplumber: {pdfplumber.__version__}")
    except ImportError:
        print("pdfplumber не установлен")
        return False

    try:
        from docx import Document
        print("python-docx установлен")
    except ImportError:
        print("python-docx не установлен")
        return False

    # 3. Создаем загрузчик
    print("\n3. Создание обработчика:")
    try:
        loader = ScriptLoader()
        print("ScriptLoader создан")
        print("Паттернов сцен: {len(loader.scene_patterns)}")
    except Exception as e:
        print(f"Ошибка создания: {e}")
        return False

    # 4. Быстрый тест извлечения текста
    print("\n4. Тест извлечения текста:")
    try:
        # Извлекаем только первые 1000 символов для теста
        with pdfplumber.open(script_file) as pdf:
            if pdf.pages:
                first_page = pdf.pages[0]
                test_text = first_page.extract_text() or ""
                print(
                    f"Текст извлечен (первая страница:"
                    f"{len(test_text)} символов)"
                )

                # Проверяем наличие паттернов сцен
                scene_indicators = ['INT.', 'EXT.', 'SCENE', 'FADE']
                found_indicators = [
                    ind for ind in scene_indicators if ind in test_text.upper()
                ]
                print(f"Найденные индикаторы сцен: {found_indicators}")
            else:
                print("PDF не содержит страниц")
    except Exception as e:
        print(f"Ошибка извлечения: {e}")
        return False

    print("\nТЕСТ ПРОЙДЕН УСПЕШНО!")
    print("Можно запускать полную обработку: python run_processing.py")

    return True


def show_file_info():
    """Показывает информацию о файле без обработки"""

    script_file = "_ 1 СЕРИЯ_.pdf"

    if not os.path.exists(script_file):
        print(f"Файл {script_file} не найден")
        return

    file_size = os.path.getsize(script_file)
    file_ext = os.path.splitext(script_file)[1].lower()

    print("ИНФОРМАЦИЯ О ФАЙЛЕ:")
    print(f"Название: {script_file}")
    print(f"Размер: {file_size:,} байт ({file_size/1024/1024:.2f} МБ)")
    print(f"Формат: {file_ext}")
    print(f"Тип: {'PDF документ' if file_ext == '.pdf' else 'DOCX документ' if file_ext == '.docx' else 'Неизвестный'}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "info":
        show_file_info()
    else:
        quick_test()
