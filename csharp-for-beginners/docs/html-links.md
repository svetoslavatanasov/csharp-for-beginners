# HTML навигация и важни връзки

Всеки HTML урок трябва да има навигация към важните страници на курса.

## Задължителна навигация

За HTML урок в `html/lessons/lesson-XX.html` използвай:

```html
<nav class="top-nav" aria-label="Основна навигация">
  <div class="top-nav-title">C# за начинаещи</div>
  <div class="top-nav-links">
    <a href="../index.html">Начало</a>
    <a href="../docs/curriculum.html">Програма</a>
    <a href="../docs/glossary.html">Речник</a>
  </div>
</nav>
```

За HTML страница в `html/docs/` използвай:

```html
<nav class="top-nav" aria-label="Основна навигация">
  <div class="top-nav-title">C# за начинаещи</div>
  <div class="top-nav-links">
    <a href="../index.html">Начало</a>
    <a href="curriculum.html">Програма</a>
    <a href="glossary.html">Речник</a>
  </div>
</nav>
```

## Важни страници

- `html/index.html` - начална страница на HTML курса.
- `html/docs/curriculum.html` - учебна програма.
- `html/docs/glossary.html` - речник.
- `html/lessons/lesson-XX.html` - HTML версия на конкретен урок.

Когато добавяш нов урок, добави линк към него в `html/index.html` и `html/docs/curriculum.html`.
