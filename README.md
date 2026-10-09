# Дизайн и монтаж со вкусом — скиллы для Claude Code

Библиотека скиллов для [Claude Code](https://claude.com/claude-code): дизайн интерфейсов и лендингов, SVG и моушен, монтаж Reels с кинетической типографикой и инфографикой поверх говорящей головы.

Скилл — это папка с `SKILL.md` (инструкции) и файлами, которые ему нужны (шрифты, шаблоны, скрипты рендера). Claude Code ищет скиллы в `~/.claude/skills/<имя>/SKILL.md` и сам подключает нужный, когда задача подходит.

## Установка в одну команду

### macOS / Linux

```bash
git clone https://github.com/elianoraMullagalieva/design-montazh-so-vkusom.git
cd design-montazh-so-vkusom && ./install.sh
```

### Windows (PowerShell)

```powershell
git clone https://github.com/elianoraMullagalieva/design-montazh-so-vkusom.git
cd design-montazh-so-vkusom
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

### Без git — через ZIP

1. Нажми на GitHub **Code → Download ZIP** (или открой `https://github.com/elianoraMullagalieva/design-montazh-so-vkusom/archive/refs/heads/main.zip`).
2. Распакуй архив и открой терминал в папке `design-montazh-so-vkusom-main`.
3. macOS/Linux: `bash install.sh`  ·  Windows: `powershell -ExecutionPolicy Bypass -File .\install.ps1`

Git LFS больше не нужен: все файлы, включая видео-примеры, лежат в репозитории как обычные файлы, и ZIP скачивается целиком.

### Что делает установщик

1. Копирует каждую папку из `skills/` в `~/.claude/skills/` (Windows: `%USERPROFILE%\.claude\skills\`).
   Если там уже есть скилл с таким же именем и он отличается — старая версия переносится в `~/.claude/skills/_backup_<дата>/`, ничего не теряется. Одинаковые скиллы пропускаются, поэтому скрипт можно запускать повторно (например, после `git pull`).
2. Ставит зависимости для монтажа и рендера (если их ещё нет):
   - `ffmpeg` — через Homebrew (macOS), apt/dnf/pacman (Linux) или winget (Windows);
   - `playwright` + `pillow` и браузер Chromium для playwright — рендер HTML-анимаций в видео и снимки сцен;
   - `mlx-whisper` на Mac с Apple Silicon или `faster-whisper` на остальных — пословные таймкоды речи;
   - `cairosvg` — PNG-превью для `svg-creator` (необязательно).
   Если что-то не поставилось, скрипт пишет предупреждение и продолжает — скиллы всё равно установятся.
3. Печатает список установленных скиллов и проверяет, что у каждого на месте `SKILL.md`.

Параметры:

| macOS/Linux | Windows | Что делает |
|---|---|---|
| `./install.sh --no-deps` | `.\install.ps1 -NoDeps` | только скопировать скиллы, без зависимостей |
| `./install.sh --deps-only` | `.\install.ps1 -DepsOnly` | только зависимости |
| `./install.sh --dest ПАПКА` | `.\install.ps1 -Dest ПАПКА` | установить в другую папку (например, `.claude/skills` проекта) |

После установки **перезапусти Claude Code** (или открой новую сессию) и проверь: спроси «какие у тебя есть скиллы?» или набери `/skills`.

### Установить один скилл вручную

Скопируй нужную папку целиком (вместе с `fonts/`, скриптами и т. п.):

```bash
mkdir -p ~/.claude/skills
cp -R skills/montazh-prozrachnaya-tipografika ~/.claude/skills/
```

Важно: путь должен получиться ровно `~/.claude/skills/<имя>/SKILL.md` — без лишних вложенных папок.

## Скиллы

### Дизайн и UI

| Скилл | Для чего |
|---|---|
| `design-taste-frontend` | Senior UI/UX-инженер: метрические правила вёрстки, компонентная архитектура, производительный CSS (англ.) |
| `design-team-standards` | Стандарты студии для сайтов и лендингов: пропорции медиа, контраст, фоны, цвета из Figma, отступы, чек-лист |
| `dizayn-futuristik` | Футуристичные лендинги и hero-секции «как на Awwwards / Apple / Linear», чек-лист антипаттернов |
| `emil-design-eng` | Философия UI-полировки Эмиля Ковальски: детали, анимации, ощущение качества (англ.) |
| `gpt-taste` | Редакционная типографика, bento-сетки, GSAP ScrollTrigger, структура AIDA (англ.) |
| `high-end-visual-design` | Шрифты, отступы, тени и карточки «как у дорогого агентства», запрет дешёвых дефолтов (англ.) |
| `impeccable` | Дизайн, аудит, критика и полировка любого интерфейса: 20+ команд (craft, audit, polish, animate…) (англ.) |
| `industrial-brutalist-ui` | Брутализм: швейцарская типографика + эстетика военного терминала, жёсткие сетки (англ.) |
| `minimalist-ui` | Чистый редакционный минимализм: тёплый монохром, плоские bento-сетки, пастель (англ.) |
| `redesign-existing-projects` | Апгрейд существующего сайта до премиум-уровня без поломки функциональности (англ.) |
| `stitch-design-taste` | Генерация DESIGN.md для Google Stitch с анти-шаблонными правилами (англ.) |

### SVG, моушен и Reels

| Скилл | Для чего |
|---|---|
| `svg-animations` | SVG-анимации: SMIL, CSS, отрисовка контуров, морфинг, маски и фильтры (англ.) |
| `svg-creator` | Иконки, иллюстрации, логотипы, диаграммы в SVG с циклом «нарисовал → отрендерил → проверил» (англ.) |
| `premium-motion-infographics` | Дорогая смысловая SVG/HTML-инфографика для Reels и презентаций, с визуальным планом и QA |
| `eli-reels-graphics` | Графика-подложка для Reels 1080×1920 за говорящей головой: жёсткая типо-шкала, SVG-анимации, рендер `record.py` |
| `montazh-prozrachnaya-tipografika` | Прозрачный субтитр-монтаж с кинетической типографикой поверх видео (Bebas + Gogol), рендер в mp4 и ProRes с альфой |
| `montazh-zagolovok-rvanyi` | Монтаж «заголовок + рваный»: крупное вступление, затем мелкие пословные субтитры по краям |
| `reels-infografika` | SVG-инфографика 1080×1040 над говорящей головой в стиле бренда автора, синхрон по словам |

Если в `skills/` появились новые папки (например, `reels-montazh-pro`), установщик и проверка подхватят их автоматически.

## Что ещё в репозитории

```
skills/           ← скиллы: по одной папке на скилл, внутри SKILL.md и всё, что ему нужно
extras/
  etalony-html/        эталонные HTML-ролики и видео-примеры (открываются в браузере)
  fonts/
    commercial-safe/   Manrope и JetBrains Mono + лицензии OFL-1.1 (можно в коммерции)
    display/           Bebas Neue Cyrillic и Gogol (лицензии не подтверждены — см. README там)
  tipografika-v-tekstah/  личные правила типографики в текстах (не скилл, справочник)
  figma-instrukcii/    уроки по Figma
tools/validate.py ← проверка скиллов перед публикацией
install.sh / install.ps1
```

## Если что-то не работает

| Проблема | Решение |
|---|---|
| Claude Code не видит скиллы | Проверь, что файлы лежат ровно так: `~/.claude/skills/<имя>/SKILL.md` (не `~/.claude/skills/skills/<имя>` и не глубже). Перезапусти Claude Code. Проверка: `ls ~/.claude/skills/*/SKILL.md` |
| `./install.sh: Permission denied` | Запусти через bash: `bash install.sh` |
| Windows: «выполнение сценариев отключено» | Запускай так: `powershell -ExecutionPolicy Bypass -File .\install.ps1` |
| Windows: кракозябры вместо русского | Используй Windows Terminal или PowerShell 7; установщик от этого не ломается, страдает только вывод |
| Вместо видео/шрифтов маленькие текстовые файлы `version https://git-lfs…` | Это старая версия репозитория с Git LFS. Скачай заново (`git clone` или ZIP) — сейчас LFS не используется |
| `git clone` ругается на LFS / «This repository is over its data quota» | Скачай свежую версию — в ней LFS нет. Если ошибка осталась: `GIT_LFS_SKIP_SMUDGE=1 git clone …` |
| `ffmpeg: command not found` | macOS: `brew install ffmpeg` · Ubuntu: `sudo apt install ffmpeg` · Windows: `winget install Gyan.FFmpeg`, затем новое окно терминала |
| `error: externally-managed-environment` при pip | Установщик сам повторяет с `--break-system-packages` для `--user`. Вручную: `python3 -m pip install --user --break-system-packages playwright` или используй venv |
| `Executable doesn't exist … ms-playwright` | Не скачан браузер: `python3 -m playwright install chromium` |
| `mlx_whisper: command not found` | Пакет стоит в пользовательскую папку Python. Добавь её в PATH: `export PATH="$(python3 -m site --user-base)/bin:$PATH"` (в `~/.zshrc`) |
| mlx-whisper не ставится на Intel Mac / Windows / Linux | Это нормально: mlx работает только на Apple Silicon. Используй `faster-whisper` (установщик ставит его сам) |
| svg-creator: `no library called "cairo"` | macOS: `brew install cairo` · Ubuntu: `sudo apt install libcairo2` · Windows: нужен GTK3 runtime |
| Шрифты в HTML-шаблоне не подхватились | Шаблон ищет их в `fonts/` рядом с HTML. Копируя шаблон в свой проект, копируй и папку `fonts/` из скилла |
| После обновления скилл ведёт себя по-старому | Запусти установщик ещё раз — изменённые скиллы обновятся, старые версии будут в `~/.claude/skills/_backup_<дата>/` |

## Для авторов: проверка перед публикацией

```bash
python3 tools/validate.py
```

Проверяет каждый `skills/<имя>/SKILL.md`: frontmatter, `name` = имя папки и `[a-z0-9-]{1,64}`, `description` до 1024 символов, нет дублей имён, нет абсолютных путей `/Users/…`, нет заглушек Git LFS, все упомянутые файлы скилла существуют, нет файлов больше 50 МБ. Код выхода 0 — можно публиковать.

Тест установки «как у нового человека»:

```bash
HOME=$(mktemp -d) bash install.sh --no-deps
```

## Лицензии

Для коммерческого проекта перед использованием любого шрифта или ассета отдельно проверь лицензию. Manrope и JetBrains Mono распространяются по SIL Open Font License 1.1 (тексты лицензий лежат рядом со шрифтами). Права на Bebas Neue Cyrillic и Gogol не подтверждены. Сторонние скиллы (`svg-creator`, `impeccable` и др.) сохраняют свои лицензии внутри своих папок.
