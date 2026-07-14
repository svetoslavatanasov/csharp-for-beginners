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
└── README.md
```

## Работен процес

1. Всеки урок се пише първо като Markdown файл в `lessons/lesson-XX.md`.
2. След това се създава HTML версия в `html/lessons/lesson-XX.html`.
3. HTML версията трябва да съдържа същото учебно съдържание като Markdown урока.
4. Всички HTML уроци използват общия стил `html/assets/course.css`.
5. Уроците следват правилата в `docs/author-bible.md` и шаблона в `docs/lesson-template.md`.

## Цел

До края на курса ученикът трябва да може да пише малки конзолни C# програми самостоятелно
и да има стабилна основа за по-сериозно програмиране по-късно.
