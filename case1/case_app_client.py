import tkinter as tk
from tkinter import filedialog, messagebox
import boto3
import os
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# Настройки для подключения к VK Cloud
S3_BUCKET = "ggwphttpd"  # Укажите имя вашего бакета
AWS_ACCESS_KEY = "2KuTeTZej47Aj52fgBmXT4"
AWS_SECRET_KEY = "hdsjhVN5tZTxxfeLyBByMZ7aL5s8drEsAZTHCSpoc4cY"
REGION = "kz-ast"  # Регион (можно использовать "ru-msk" для Москвы)
ENDPOINT_URL = "https://hb.kz-ast.bizmrg.com"  # Для региона Казахстан

# Инициализация клиента для работы с S3
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION,
    endpoint_url=ENDPOINT_URL,
)

# Глобальная переменная для отслеживания текущей папки
current_folder = ""


# Функция для скачивания файла из S3
def download_file(file_name):
    try:
        file_path = filedialog.asksaveasfilename(defaultextension=".bin", initialfile=file_name)  # Диалог для сохранения
        if file_path:
            s3.download_file(S3_BUCKET, file_name, file_path)
            messagebox.showinfo("Успех", f"Файл '{file_name}' успешно загружен на компьютер!")
    except NoCredentialsError:
        messagebox.showerror("Ошибка", "Ошибка в учетных данных.")
    except PartialCredentialsError:
        messagebox.showerror("Ошибка", "Некорректные учетные данные.")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")


# Функция для скачивания папки
def download_folder(folder_name):
    try:
        folder_path = filedialog.askdirectory()  # Диалог выбора папки для сохранения
        if not folder_path:
            return

        # Получаем список всех объектов внутри папки
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=folder_name + "/")
        objects = response.get("Contents", [])
        if not objects:
            messagebox.showinfo("Информация", "Папка пуста или не найдена.")
            return

        for obj in objects:
            key = obj["Key"]
            local_file_path = f"{folder_path}/{key[len(folder_name)+1:]}"  # Убираем префикс папки из пути
            local_dir = "/".join(local_file_path.split("/")[:-1])

            # Создаём локальную структуру папок
            os.makedirs(local_dir, exist_ok=True)

            # Скачиваем файл
            s3.download_file(S3_BUCKET, key, local_file_path)

        messagebox.showinfo("Успех", f"Папка '{folder_name}' успешно загружена!")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка при скачивании папки: {e}")


# Функция для отображения списка файлов и папок
def load_file_list(folder=""):
    global current_folder
    current_folder = folder  # Обновляем текущую папку

    try:
        prefix = f"{folder}/" if folder else ""
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix, Delimiter="/")
        files = response.get("Contents", [])

        for widget in file_list_frame.winfo_children():
            widget.destroy()  # Удаляем все элементы перед обновлением

        if not files and not response.get("CommonPrefixes", []):
            messagebox.showinfo("Информация", "В бакете нет файлов или папок.")
            return

        # Кнопка для возврата в родительскую папку
        if folder:
            parent_folder = '/'.join(folder.split('/')[:-1])
            back_button = tk.Button(file_list_frame, text="Назад", command=lambda: load_file_list(parent_folder), 
                                    bg="#FF5733", fg="white", font=("Arial", 14))
            back_button.pack(fill="x", pady=5)

        # Папки
        for prefix in response.get("CommonPrefixes", []):
            folder_name = prefix["Prefix"].rstrip("/")
            folder_frame = tk.Frame(file_list_frame)
            folder_frame.pack(fill="x", pady=2)

            folder_button = tk.Button(
                folder_frame,
                text=f"[Папка] {folder_name}",
                command=lambda folder_name=folder_name: load_file_list(folder_name),
                bg="#4CAF50",
                fg="white",
                font=("Arial", 14),
            )
            folder_button.pack(side="left", padx=5)

            download_folder_button = tk.Button(
                folder_frame,
                text="Скачать",
                command=lambda folder_name=folder_name: download_folder(folder_name),
                bg="#2196F3",
                fg="white",
                font=("Arial", 12),
            )
            download_folder_button.pack(side="right", padx=5)

        # Файлы
        for file in files:
            file_name = file["Key"]

            # Исключаем "файл", создаваемый при создании папки
            if file_name == f"{folder}/":
                continue

            file_frame = tk.Frame(file_list_frame)
            file_frame.pack(fill="x", pady=2)

            file_label = tk.Label(file_frame, text=file_name, width=50, font=("Arial", 12), anchor="w")
            file_label.pack(side="left")

            # Кнопка для скачивания файла
            download_button = tk.Button(file_frame, text="Скачать", 
                                        command=lambda file_name=file_name: download_file(file_name), 
                                        bg="#2196F3", fg="white", font=("Arial", 12))
            download_button.pack(side="right", padx=5)

    except NoCredentialsError:
        messagebox.showerror("Ошибка", "Ошибка в учетных данных.")
    except PartialCredentialsError:
        messagebox.showerror("Ошибка", "Некорректные учетные данные.")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")


# Основное окно приложения
root = tk.Tk()
root.title("Просмотр и скачивание файлов")
root.geometry("600x500")  # Размер окна

# Фрейм для кнопок
button_frame = tk.Frame(root, bg="#f0f0f0")
button_frame.pack(pady=10, padx=10, fill="x")

# Кнопка для получения списка файлов
get_file_list_button = tk.Button(button_frame, text="Получить список файлов", command=lambda: load_file_list(""), 
                                 font=("Arial", 14), bg="#2196F3", fg="white", width=20)
get_file_list_button.pack(side="left", padx=5)

# Фрейм для отображения списка файлов
file_list_frame = tk.Frame(root)
file_list_frame.pack(pady=10, fill="both", expand=True, padx=10)

# Запуск интерфейса
root.mainloop()
