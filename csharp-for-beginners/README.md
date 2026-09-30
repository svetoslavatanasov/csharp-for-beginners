# C# за начинаещи

Markdown-базиран курс по C# за напълно начинаещ ученик на около 15 години.
Курсът учи не само синтаксис, а и универсални програмни принципи: алгоритми,
стъпково мислене, дебъгване, четене на код и разбиване на проблеми.

## Структура

```text
csharp-for-beginners/
├── docs/
│   ├── author-bible.md
│   ├── curriculum.md
│   ├── lesson-template.md
│   ├── exercise-rules.md
│   ├── glossary.md
│   └── visual-style.md
├── html/
│   ├── assets/
│   │   └── course.css
│   └── lessons/
├── lessons/
├── exercises/
├── solutions/
├── examples/
├── tools/
│   ├── build_html.py
│   ├── test_build_html.py
│   └── test_site.py
└── README.md
```

## Работен процес

1. Всеки урок се пише първо като Markdown файл в `lessons/lesson-XX.md`.
2. HTML версията `html/lessons/lesson-XX.html` се генерира от Markdown с командата
   `python tools/build_html.py` (пуска се от папка `csharp-for-beginners`). HTML уроците не се
   редактират на ръка.
3. След това `python -m unittest discover -s tools` проверява, че HTML е актуален, съдържа
   целия текст на урока и че линковете работят.
4. Всички HTML уроци използват общия стил `html/assets/course.css`.
5. Уроците следват правилата в `docs/author-bible.md` и шаблона в `docs/lesson-template.md`.

## Цел

До края на курса ученикът трябва да може да пише малки конзолни C# програми самостоятелно
и да има стабилна основа за по-сериозно програмиране по-късно.
