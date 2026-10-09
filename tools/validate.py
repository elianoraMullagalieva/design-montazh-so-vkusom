#!/usr/bin/env python3
"""Проверка репозитория скиллов перед публикацией.

Запуск из корня репозитория:
    python3 tools/validate.py            # проверить skills/ и весь репозиторий
    python3 tools/validate.py --skills-dir ~/.claude/skills --no-repo-checks

Что проверяется:
  * каждая папка skills/<имя>/ содержит SKILL.md (Claude Code ищет скиллы ровно на один уровень вглубь);
  * у SKILL.md есть YAML-frontmatter с name и description;
  * name — [a-z0-9-]{1,64}, без дефиса в начале/конце и двойных дефисов, совпадает с именем папки;
  * description не пустой и не длиннее 1024 символов;
  * нет двух скиллов с одинаковым name;
  * в текстовых файлах скиллов нет абсолютных путей вида /Users/..., /home/..., C:\\Users\\...;
  * нигде нет указателей Git LFS и LFS-правил в .gitattributes;
  * ссылки на файлы внутри скилла (markdown-ссылки и `пути/в/обратных/кавычках`) существуют;
  * в репозитории нет файлов больше 50 МБ (GitHub их не любит).

Код выхода: 0 — ошибок нет (предупреждения допустимы), 1 — есть ошибки.
Зависимостей нет: работает на чистом python3 (PyYAML используется, если установлен).
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
TEXT_EXT = {".md", ".py", ".js", ".mjs", ".cjs", ".ts", ".html", ".htm", ".css", ".json",
            ".yaml", ".yml", ".txt", ".sh", ".ps1", ".svg", ".toml", ".xml", ".csv"}
LFS_MAGIC = b"version https://git-lfs.github.com/spec/v1"
ABS_PATH_RE = re.compile(r"(/Users/[A-Za-z0-9._-]+/|/home/[a-z][a-z0-9._-]*/|[A-Za-z]:\\\\?Users\\\\?)")
AUTHOR_HOME_RE = re.compile(r"~/(Desktop|Documents|Downloads|Library)/")
MD_LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
MD_IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
CODE_RE = re.compile(r"`([^`\n]+)`")
PATHLIKE_RE = re.compile(r"^[\w.\-/ *А-Яа-яЁё+@]+$")
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv"}
MAX_FILE_MB_ERROR = 50
MAX_FILE_MB_WARN = 20


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, where: str, msg: str) -> None:
        self.errors.append(f"ОШИБКА  {where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"ВНИМАНИЕ {where}: {msg}")


# ---------------------------------------------------------------- frontmatter
def split_frontmatter(text: str):
    text = text.lstrip("\ufeff")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return None


def _unquote(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        inner = v[1:-1]
        if v[0] == '"':
            inner = inner.replace('\\"', '"').replace("\\\\", "\\")
        else:
            inner = inner.replace("''", "'")
        return inner
    return v


def parse_yaml_simple(src: str) -> dict:
    """Мини-парсер для плоского frontmatter (если нет PyYAML)."""
    data: dict = {}
    lines = src.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2)
        if val in (">", "|", ">-", "|-", ">+", "|+"):
            block = []
            i += 1
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                block.append(lines[i].strip())
                i += 1
            data[key] = (" " if val.startswith(">") else "\n").join(b for b in block if b).strip()
            continue
        if val == "":
            # список или вложенная структура
            items = []
            i += 1
            while i < len(lines) and lines[i].startswith((" ", "\t", "-")):
                s = lines[i].strip()
                if s.startswith("- "):
                    items.append(_unquote(s[2:]))
                i += 1
            data[key] = items
            continue
        data[key] = _unquote(val)
        i += 1
    return data


def parse_frontmatter(src: str):
    try:
        import yaml  # type: ignore

        try:
            d = yaml.safe_load(src)
        except Exception as e:  # noqa: BLE001
            return None, f"frontmatter не парсится как YAML: {e}".replace("\n", " ")
        if not isinstance(d, dict):
            return None, "frontmatter не является словарём ключ: значение"
        return d, None
    except ImportError:
        for line in src.splitlines():
            m = re.match(r"^[A-Za-z0-9_-]+:\s+(.*)$", line)
            if m:
                v = m.group(1).strip()
                if v and v[0] not in "\"'>|[{" and (": " in v or " #" in v):
                    return None, ("в значении есть ': ' или ' #' без кавычек — это невалидный YAML, "
                                  "оберни значение в двойные кавычки: " + line[:80])
        return parse_yaml_simple(src), None


# ---------------------------------------------------------------- helpers
def is_text(p: Path) -> bool:
    return p.suffix.lower() in TEXT_EXT or p.name in {"LICENSE", "NOTICE", ".gitignore"}


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            yield Path(dirpath) / f


def rel(p: Path, base: Path) -> str:
    try:
        return str(p.relative_to(base))
    except ValueError:
        return str(p)


def check_ref(skill_dir: Path, base_dir: Path, target: str) -> bool:
    """True если путь существует (поддерживаются * и ?)."""
    target = target.split("#", 1)[0].split("?", 1)[0]
    if not target:
        return True
    cand = (base_dir / target)
    if any(ch in target for ch in "*?"):
        return bool(glob.glob(str(cand)))
    return cand.exists() or (skill_dir / target).exists()


# ---------------------------------------------------------------- checks
def check_skill(skill_dir: Path, rep: Report, names: dict, base: Path) -> None:
    where = rel(skill_dir, base)
    skill_md = skill_dir / "SKILL.md"
    if len(skill_dir.name) > 64 or not NAME_RE.match(skill_dir.name):
        rep.err(where, "имя папки должно быть латиницей [a-z0-9-] (как name в SKILL.md)")
    if not skill_md.is_file():
        nested = [p for p in skill_dir.rglob("SKILL.md")]
        hint = f" (найдено глубже: {', '.join(rel(n, base) for n in nested[:3])})" if nested else ""
        rep.err(where, "нет SKILL.md — Claude Code не увидит скилл" + hint)
        return

    text = skill_md.read_text(encoding="utf-8", errors="replace")
    fm_src = split_frontmatter(text)
    if fm_src is None:
        rep.err(rel(skill_md, base), "нет YAML-frontmatter (файл должен начинаться с '---', затем name/description, затем '---')")
        return
    fm, perr = parse_frontmatter(fm_src)
    if perr:
        rep.err(rel(skill_md, base), perr)
        return

    name = fm.get("name")
    desc = fm.get("description")
    if not isinstance(name, str) or not name.strip():
        rep.err(rel(skill_md, base), "нет поля name")
    else:
        name = name.strip()
        if len(name) > 64 or not NAME_RE.match(name):
            rep.err(rel(skill_md, base), f"name '{name}' не соответствует [a-z0-9-]{{1,64}} (латиница в нижнем регистре, цифры, дефисы)")
        if name != skill_dir.name:
            rep.err(rel(skill_md, base), f"name '{name}' не совпадает с именем папки '{skill_dir.name}'")
        if name in names:
            rep.err(rel(skill_md, base), f"дубль имени '{name}' (уже есть в {names[name]})")
        else:
            names[name] = where
    if not isinstance(desc, str) or not desc.strip():
        rep.err(rel(skill_md, base), "нет поля description (или оно пустое)")
    else:
        if len(desc) > 1024:
            rep.err(rel(skill_md, base), f"description длиннее 1024 символов ({len(desc)})")
        if re.search(r"<[A-Za-z/][^>]*>", desc):
            rep.warn(rel(skill_md, base), "в description есть XML/HTML-теги — лучше убрать")

    for extra in skill_dir.rglob("SKILL.md"):
        if extra != skill_md:
            rep.warn(rel(extra, base), "вложенный SKILL.md — Claude Code его не подхватит как отдельный скилл")

    # содержимое файлов скилла
    top_entries = {p.name for p in skill_dir.iterdir()}
    for f in iter_files(skill_dir):
        try:
            head = f.open("rb").read(200)
        except OSError:
            continue
        if head.startswith(LFS_MAGIC):
            rep.err(rel(f, base), "это указатель Git LFS, а не настоящий файл")
            continue
        if not is_text(f):
            continue
        try:
            body = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for ln, line in enumerate(body.splitlines(), 1):
            if ABS_PATH_RE.search(line):
                rep.err(f"{rel(f, base)}:{ln}", "абсолютный путь к чужому компьютеру: " + line.strip()[:120])
            if f.suffix == ".md" and AUTHOR_HOME_RE.search(line):
                rep.warn(f"{rel(f, base)}:{ln}", "путь к личной папке автора (~/Desktop, ~/Documents…): " + line.strip()[:120])
        if f.suffix.lower() == ".md":
            md_dir = f.parent
            for m in list(MD_LINK_RE.finditer(body)) + list(MD_IMG_RE.finditer(body)):
                t = m.group(1).strip("<>")
                if re.match(r"^[a-z][a-z0-9+.-]*:", t, re.I) or t.startswith(("#", "/", "~", "{")):
                    continue
                if not check_ref(skill_dir, md_dir, t):
                    rep.err(rel(f, base), f"ссылка на несуществующий файл: {t}")
        if f == skill_md:
            for m in CODE_RE.finditer(body):
                t = m.group(1).strip()
                if ("/" not in t or "://" in t or t.startswith(("/", "~", "$", "..", ".")) or
                        "…" in t or "<" in t or not PATHLIKE_RE.match(t)):
                    continue
                first = t.split("/", 1)[0]
                if first not in top_entries:
                    continue  # путь не про эту папку (например, в проекте пользователя)
                if not check_ref(skill_dir, skill_dir, t.rstrip("/")):
                    rep.err(rel(f, base), f"упомянут несуществующий файл скилла: `{t}`")


def check_repo(repo: Path, rep: Report) -> None:
    ga = repo / ".gitattributes"
    if ga.is_file() and "filter=lfs" in ga.read_text(encoding="utf-8", errors="replace"):
        rep.err(".gitattributes", "есть правила Git LFS (filter=lfs) — у людей без LFS скачаются заглушки")
    for f in iter_files(repo):
        if "tools" in f.relative_to(repo).parts[:1] and f.name == "validate.py":
            continue
        try:
            size = f.stat().st_size
            head = f.open("rb").read(200)
        except OSError:
            continue
        if head.startswith(LFS_MAGIC):
            rep.err(rel(f, repo), "указатель Git LFS вместо файла")
        mb = size / 1024 / 1024
        if mb > MAX_FILE_MB_ERROR:
            rep.err(rel(f, repo), f"файл {mb:.0f} МБ — больше {MAX_FILE_MB_ERROR} МБ, пережми или убери")
        elif mb > MAX_FILE_MB_WARN:
            rep.warn(rel(f, repo), f"файл {mb:.0f} МБ — тяжеловато для репозитория")


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(description="Проверка скиллов")
    ap.add_argument("--skills-dir", type=Path, default=repo / "skills")
    ap.add_argument("--no-repo-checks", action="store_true", help="не проверять .gitattributes и размеры файлов")
    args = ap.parse_args()

    skills_dir = args.skills_dir.expanduser().resolve()
    rep = Report()
    if not skills_dir.is_dir():
        print(f"Нет папки со скиллами: {skills_dir}")
        return 1

    base = skills_dir.parent
    names: dict = {}
    dirs = sorted(p for p in skills_dir.iterdir()
                  if p.is_dir() and not p.name.startswith((".", "_")))
    for f in skills_dir.iterdir():
        if f.is_file() and f.name not in {".DS_Store", "README.md"}:
            rep.warn(rel(f, base), "файл прямо в skills/ — сюда кладут только папки скиллов")
    for d in dirs:
        check_skill(d, rep, names, base)
    if not args.no_repo_checks:
        check_repo(repo, rep)

    for w in rep.warnings:
        print(w)
    for e in rep.errors:
        print(e)
    print()
    print(f"Скиллов проверено: {len(dirs)} | ошибок: {len(rep.errors)} | предупреждений: {len(rep.warnings)}")
    if names:
        print("Скиллы: " + ", ".join(sorted(names)))
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
