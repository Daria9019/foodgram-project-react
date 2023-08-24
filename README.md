
# Foodgram
**Продуктовый помощник, в котором пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.**
- клонируйте репозиторий: git clone
- создайте виртуальное окружение: py -3.9 -m venv venv
- активируйте виртуальное окружение: source env/bin/activate
- установите зависимости: pip install -r requirements.txt
- примените миграции: python manage.py makemigrations
                      python manage.py migrate
- запустите контейнеры: docker-compose up
- в новом окне терминала выполните команды:
   - docker compose exec backend python manage.py migrate
   - docker compose exec backend python manage.py migrate

