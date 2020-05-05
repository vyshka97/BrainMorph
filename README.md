# Brain Morph

Система для проведения морфометрического анализа гиппокампов головного мозга

### Структура проекта
- **app/** - модуль всего приложения
- **brain_morph.py** - верхнеуровневый сценарий, определяющий экземпляр приложения
- **.flaskenv** - конфигурационный файл с параметрами запуска Flask
- **.gitignore** - файл, указывающий git, какие файлы/папки нужно игнорировать
- **boot.sh** - входная точка при запуске Docker контейнера
- **config.py** - скрипт с параметрами конфигурации работы приложения
- **Dockerfile** - сценарий создания Docker образа
- **nipype.cfg** - конфигурационный файл для Nipype
- **requirements.txt** - зависимости для виртуального окружения под python3

#### Установка виртуального окружения и зависимостей
```bash
python3 -m venv ./venv
venv/bin/pip install wheel 
venv/bin/pip install -r requirements.txt
```

#### Собираем контейнер и закидываем в Docker Hub
```bash
docker build -t kronoker/brain-morph . && docker push kronoker/brain-morph
```

#### Запуск контейнера
```bash
docker run --name brain_morph -d -p 8000:8886 --rm -e PORT=8886 kronoker/brain-morph:latest
```

#### Остановка контейнера
```bash
docker stop brain_morph
```