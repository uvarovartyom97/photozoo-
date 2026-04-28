# Деплой PhotoZoom Analytics на VPS

Эта инструкция описывает самый простой production-вариант: российский VPS + Ubuntu + cron. Проект не является веб-приложением, ему не нужен домен, nginx или открытый порт. Сервер регулярно запускает Python-скрипт, а скрипт сам проверяет расписание торговых точек, читает Google Sheets и отправляет нужные отчеты в Telegram.

## Выбор VPS

Рекомендую **Timeweb Cloud**, тариф **Cloud MSK 30**:

- локация: Москва;
- ОС: Ubuntu 24.04 LTS;
- ресурсы: 1 CPU, 2 GB RAM, 30 GB NVMe;
- цена на момент проверки: 657 руб./мес.;
- публичный IP включен в тариф;
- есть почасовая оплата и простая панель управления.

Почему не минимальный 1 GB RAM: проект использует `pandas`, а для спокойного запуска отчетов лучше иметь 2 GB памяти. Если отчет станет тяжелее, тариф можно увеличить.

Альтернативы:

- **Beget VPS**: можно взять 1 CPU / 2 GB / 15 GB, примерно 17 руб./день плюс публичный IPv4 около 5 руб./день. Хороший вариант, если удобнее Beget.
- **REG.RU VPS**: есть дешевые тарифы, но для этого проекта Timeweb проще по соотношению цена/удобство.
- **Yandex Cloud**: надежно, но для маленького cron-скрипта обычно сложнее и дороже по настройке, потому что тарифицируются VM, диск, IP и трафик отдельно.

Официальные страницы для проверки актуальных цен:

- https://timeweb.cloud/services/vds-vps
- https://beget.com/ru/vps
- https://www.reg.ru/company/prices/vps
- https://yandex.cloud/ru/docs/compute/pricing

## 1. Создать сервер

1. Зарегистрируйтесь в Timeweb Cloud.
2. Откройте раздел создания VPS/VDS.
3. Выберите:
   - регион: Москва;
   - образ: Ubuntu 24.04 LTS;
   - тариф: Cloud MSK 30;
   - авторизация: SSH-ключ, если умеете пользоваться SSH-ключами, иначе пароль.
4. Создайте сервер.
5. Скопируйте публичный IP-адрес сервера.

Дальше в примерах:

```bash
SERVER_IP=your_server_ip
```

## 2. Подключиться к серверу

С локального компьютера:

```bash
ssh root@SERVER_IP
```

Если используется SSH-ключ:

```bash
ssh -i ~/.ssh/your_key root@SERVER_IP
```

## 3. Подготовить Ubuntu

На сервере:

```bash
apt update
apt upgrade -y
apt install -y python3 python3-venv python3-pip git nano cron
timedatectl set-timezone Asia/Yekaterinburg
systemctl enable cron
systemctl start cron
```

Проверить время:

```bash
date
```

## 4. Создать отдельного пользователя

Не обязательно, но лучше не запускать проект от `root`.

```bash
adduser photozoom
usermod -aG sudo photozoom
su - photozoom
```

Дальше команды выполняются от пользователя `photozoom`.

## 5. Загрузить проект на сервер

Вариант A: если проект лежит в Git-репозитории:

```bash
mkdir -p ~/apps
cd ~/apps
git clone <repo-url> photozoom-analytics
cd photozoom-analytics
```

Вариант B: если Git-репозитория пока нет, загрузите папку с локального компьютера через `scp`:

```bash
scp -r "/Users/aduvarov/Documents/PhotoZoom Analytics" photozoom@SERVER_IP:~/apps/photozoom-analytics
```

После загрузки на сервере:

```bash
cd ~/apps/photozoom-analytics
```

## 6. Установить зависимости Python

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

Проверить, что пакет запускается:

```bash
PYTHONPATH=src .venv/bin/python -m photozoom_analytics
```

На этом шаге запуск может упасть из-за отсутствия `.env` или `service-account.json`. Это нормально, они настраиваются дальше.

## 7. Создать `.env` на сервере

```bash
cp .env.example .env
nano .env
```

Заполните значения:

```bash
GOOGLE_SHEET_ID=your_google_sheet_id
GOOGLE_WORKSHEET_NAME=*
GOOGLE_SERVICE_ACCOUNT_FILE=/home/photozoom/apps/photozoom-analytics/service-account.json
TRADING_POINTS_FILE=

TELEGRAM_BOT_TOKEN=123456789:replace_me
TELEGRAM_CHAT_ID=-1001234567890

REPORT_TITLE=Ракета Челябинск
REPORT_TIMEZONE=Asia/Yekaterinburg
REPORT_SEND_TIME=22:00
REPORT_STATE_FILE=.photozoom-report-state.json
DATE_COLUMN=date
REVENUE_COLUMN=revenue
COST_COLUMN=cost
ORDERS_COLUMN=orders
CONVERSIONS_COLUMN=conversions
VISITS_COLUMN=visits
REPORT_DATE=
FORCE_SEND=false
DRY_RUN=false
```

Защитить файл:

```bash
chmod 600 .env
```

## 8. Загрузить Google service account key

Файл должен называться:

```bash
/home/photozoom/apps/photozoom-analytics/service-account.json
```

С локального компьютера:

```bash
scp "/Users/aduvarov/Documents/PhotoZoom Analytics/service-account.json" photozoom@SERVER_IP:/home/photozoom/apps/photozoom-analytics/service-account.json
```

На сервере:

```bash
cd /home/photozoom/apps/photozoom-analytics
chmod 600 service-account.json
```

Важно: Google Sheet должен быть расшарен на email сервисного аккаунта из `service-account.json`.

## 9. Проверить запуск без отправки в Telegram

На сервере:

```bash
cd /home/photozoom/apps/photozoom-analytics
DRY_RUN=true PYTHONPATH=src .venv/bin/python -m photozoom_analytics
```

Если отчет построился и текст вывелся в консоль, доступ к Google Sheets работает.

## 10. Проверить настоящую отправку в Telegram

```bash
cd /home/photozoom/apps/photozoom-analytics
PYTHONPATH=src .venv/bin/python -m photozoom_analytics
```

Если сообщение пришло в Telegram-канал, ручной запуск готов.

Если не пришло:

- проверьте `TELEGRAM_BOT_TOKEN`;
- проверьте `TELEGRAM_CHAT_ID`;
- убедитесь, что бот добавлен в приватный канал администратором;
- убедитесь, что `DRY_RUN=false` в `.env`.

## 11. Настроить торговые точки и расписание

Если торговая точка одна, можно оставить `GOOGLE_SHEET_ID`, `GOOGLE_WORKSHEET_NAME`, `REPORT_TIMEZONE` и `REPORT_SEND_TIME` прямо в `.env`.

Если точек несколько, создайте отдельный файл:

```bash
cp trading-points.example.json trading-points.json
nano trading-points.json
```

Пример одной точки:

```json
{
  "name": "PhotoZoom Москва",
  "google_sheet_id": "google_sheet_id_for_moscow",
  "google_worksheet_name": "*",
  "report_title": "PhotoZoom Москва",
  "timezone": "Europe/Moscow",
  "send_time": "22:00"
}
```

В `.env` укажите:

```bash
TRADING_POINTS_FILE=./trading-points.json
```

Для каждой точки можно задать свой `timezone` и `send_time`. Если `telegram_chat_id` не указан внутри точки, используется общий `TELEGRAM_CHAT_ID`.

## 12. Настроить запуск через cron

Открыть crontab:

```bash
crontab -e
```

Добавить строку для запуска каждые 2 часа. Скрипт сам проверит локальное время каждой торговой точки и не отправит дубль за одну локальную дату:

```cron
0 */2 * * * cd /home/photozoom/apps/photozoom-analytics && PYTHONPATH=src .venv/bin/python -m photozoom_analytics >> /home/photozoom/apps/photozoom-analytics/report.log 2>&1
```

Проверить список задач:

```bash
crontab -l
```

Состояние отправок хранится в `.photozoom-report-state.json`. Для ручной проверки без учета расписания можно использовать:

```bash
FORCE_SEND=true PYTHONPATH=src .venv/bin/python -m photozoom_analytics
```

## 13. Проверить логи

После первого запуска:

```bash
cd /home/photozoom/apps/photozoom-analytics
tail -100 report.log
```

Смотреть лог в реальном времени:

```bash
tail -f report.log
```

## 14. Как обновлять проект на сервере

Если проект загружен через Git:

```bash
cd /home/photozoom/apps/photozoom-analytics
git pull
.venv/bin/pip install -r requirements.txt
```

Потом проверить ручной запуск:

```bash
PYTHONPATH=src .venv/bin/python -m photozoom_analytics
```

## 15. Минимальная безопасность

Сделайте хотя бы это:

```bash
sudo apt install -y ufw
sudo ufw allow OpenSSH
sudo ufw enable
```

Для этого проекта не нужно открывать HTTP/HTTPS-порты, потому что он ничего не принимает из интернета.

Периодически обновляйте сервер:

```bash
sudo apt update
sudo apt upgrade -y
```

## 16. Финальный чек-лист

- VPS создан.
- Ubuntu 24.04 установлена.
- Timezone выставлен на `Asia/Yekaterinburg`.
- Проект лежит в `/home/photozoom/apps/photozoom-analytics`.
- `.venv` создан.
- Зависимости установлены.
- `.env` заполнен.
- `trading-points.json` создан, если торговых точек несколько.
- `service-account.json` загружен.
- Google Sheet расшарен на сервисный аккаунт.
- Бот добавлен администратором в Telegram-канал.
- Ручной запуск работает.
- Cron-задача добавлена.
- `report.log` создается и обновляется.
