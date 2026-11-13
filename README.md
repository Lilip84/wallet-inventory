# wallet-inventory

Локальный инвентаризатор крипто-кошельков, установленных на компьютере.

Сканирует профили браузеров семейства Chrome (Chrome, Chromium, Edge, Brave,
Vivaldi, Opera) и каталоги десктопных кошельков. Показывает только безопасные
метаданные: название, версию, браузер, профиль, дату установки.

**Что он НЕ делает:** не читает ключи, seed-фразы, cookies, историю, не
обращается к сети, ничего не отправляет наружу и не изменяет файлы.

## Зачем

Понять, какие кошельки стоят на машине — при инвентаризации парка, перед
аудитом безопасности, при подготовке рабочего места. Только чтение метаданных.

## Установка

```bash
git clone https://github.com/Lilip84/wallet-inventory.git
cd wallet-inventory
python3 wallet_inventory.py
```

Зависимостей нет, нужен Python 3.10+.

## Использование

```bash
python3 wallet_inventory.py             # таблица
python3 wallet_inventory.py --json      # машинный формат
python3 wallet_inventory.py --home /path # другой домашний каталог
```

Пример вывода:

```
WALLET    VERSION  BROWSER  PROFILE  INSTALLED
--------  -------  -------  -------  ---------
MetaMask  11.2.0   Chrome   Default  2026-03-14
Phantom   24.1.0   Brave    Profile 1 2026-05-02
```

## Как определяются кошельки

Два независимых признака:

1. Известные идентификаторы расширений (`nkbihfbeogaeaoehlefnkodbefgpgknn` —
   MetaMask, `bfnaelmomeimhlpmgjnjophhpkkoljpa` — Phantom и другие).
2. Ключевые слова в поле `name` файла `manifest.json` — так ловятся кошельки,
   которых нет в списке.

Неизвестные расширения без ключевых слов в названии в отчёт не попадают.

## Платформы

Linux проверен. Пути для macOS и Windows заданы, но на них инструмент
пока не тестировался — это честно указано, а не заявлено как поддержка.

## Тесты

```bash
python3 -m unittest discover -s tests -v
```

## Лицензия

MIT.
