import tkinter as tk
import os
from tkinter import simpledialog
from tkinter import filedialog, messagebox
import boto3
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


# Функция для загрузки файла в S3
def upload_file(path=""):
    if not path:
        file_path = filedialog.askopenfilename()  # Открыть диалог выбора файла
    else:
        file_path = path
    if file_path:
        try:
            file_name = file_path.split("/")[-1]  # Имя файла
            file_name = f"{current_folder}/{file_name}" if current_folder else file_name  # Префикс папки в имени файла

            s3.upload_file(file_path, S3_BUCKET, file_name)
            messagebox.showinfo("Успех", f"Файл '{file_name}' успешно загружен в бакет!")
            load_file_list(current_folder)  # Обновляем список файлов
        except FileNotFoundError:
            messagebox.showerror("Ошибка", "Файл не найден.")
        except NoCredentialsError:
            messagebox.showerror("Ошибка", "Ошибка в учетных данных.")
        except PartialCredentialsError:
            messagebox.showerror("Ошибка", "Некорректные учетные данные.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")


# Функция для создания папки
def create_folder():
    folder_name = simpledialog.askstring("Создать папку", "Введите имя новой папки:")
    if folder_name:
        folder_path = f"{current_folder}/{folder_name}/" if current_folder else f"{folder_name}/"
        try:
            # Создаем "пустую папку" (создаём объект с ключом, оканчивающимся на "/")
            s3.put_object(Bucket=S3_BUCKET, Key=folder_path)
            messagebox.showinfo("Успех", f"Папка '{folder_name}' успешно создана!")
            load_file_list(current_folder)  # Обновляем список файлов и папок
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать папку: {e}")


# Функция для удаления папки
def delete_folder(folder_name):
    confirm = messagebox.askyesno(
        "Подтверждение", f"Вы уверены, что хотите удалить папку '{folder_name}' и все её содержимое?"
    )
    if confirm:
        try:
            response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=folder_name + "/")
            objects_to_delete = response.get("Contents", [])

            if not objects_to_delete:
                messagebox.showinfo("Информация", "Папка пуста или не найдена.")
                return

            delete_objects = {"Objects": [{"Key": obj["Key"]} for obj in objects_to_delete]}
            s3.delete_objects(Bucket=S3_BUCKET, Delete=delete_objects)

            messagebox.showinfo("Успех", f"Папка '{folder_name}' и все её содержимое успешно удалены!")
            load_file_list(current_folder)  # Обновляем список файлов
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка при удалении папки: {e}")


# Функция для удаления файла из S3
def delete_file(file_name):
    try:
        s3.delete_object(Bucket=S3_BUCKET, Key=file_name)  # Удалить файл
        messagebox.showinfo("Успех", f"Файл '{file_name}' успешно удален из бакета!")
        load_file_list(current_folder)  # Обновляем список файлов
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")


# Функция для скачивания файла из S3
def download_file(file_name):
    try:
        file_path = filedialog.asksaveasfilename(defaultextension=".bin", initialfile=file_name)  # Диалог для сохранения
        if file_path:
            s3.download_file(S3_BUCKET, file_name, file_path)
            messagebox.showinfo("Успех", f"Файл '{file_name}' успешно загружен на компьютер!")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")

# Функция для скачивания всей папки
def download_folder(folder_name):
    try:
        # Выбор локальной директории для сохранения
        local_dir = filedialog.askdirectory(title="Выберите папку для сохранения")
        if not local_dir:
            return  # Пользователь отменил выбор

        # Создание локальной папки для содержимого
        local_folder_path = os.path.join(local_dir, os.path.basename(folder_name))
        os.makedirs(local_folder_path, exist_ok=True)

        # Получение всех объектов в папке из S3
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=f"{folder_name}/")
        files = response.get("Contents", [])

        if not files:
            messagebox.showinfo("Информация", "Папка пуста или не найдена.")
            return

        # Скачивание каждого файла
        for file in files:
            file_key = file["Key"]
            local_file_path = os.path.join(local_folder_path, os.path.relpath(file_key, folder_name))
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)  # Создаём подкаталоги при необходимости

            s3.download_file(S3_BUCKET, file_key, local_file_path)

        messagebox.showinfo("Успех", f"Папка '{folder_name}' успешно скачана в '{local_folder_path}'!")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка при скачивании папки: {e}")

# Функция для отображения списка файлов и папок
def load_file_list(folder=""):
    global current_folder
    current_folder = folder

    try:
        prefix = f"{folder}/" if folder else ""
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix, Delimiter="/")
        files = response.get("Contents", [])

        for widget in file_list_frame.winfo_children():
            widget.destroy()

        if folder:
            parent_folder = "/".join(folder.split("/")[:-1])
            back_button = tk.Button(
                file_list_frame, text="Назад", command=lambda: load_file_list(parent_folder), bg="#FF5733", fg="white", font=("Arial", 14)
            )
            back_button.pack(fill="x", pady=5)

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

             delete_folder_button = tk.Button(
                 folder_frame,
                 text="Удалить",
                 command=lambda folder_name=folder_name: delete_folder(folder_name),
                 bg="#F44336",
                 fg="white",
                 font=("Arial", 12),
             )
             delete_folder_button.pack(side="right", padx=5)


        for file in files:
            file_name = file["Key"]
            if file_name == f"{folder}/":
                continue

            file_frame = tk.Frame(file_list_frame)
            file_frame.pack(fill="x", pady=2)

            file_label = tk.Label(file_frame, text=file_name, width=50, font=("Arial", 12), anchor="w")
            file_label.pack(side="left")

            download_button = tk.Button(
                file_frame, text="Скачать", command=lambda file_name=file_name: download_file(file_name), bg="#2196F3", fg="white", font=("Arial", 12)
            )
            download_button.pack(side="right", padx=5)

            delete_button = tk.Button(
                file_frame, text="Удалить", command=lambda file_name=file_name: delete_file(file_name), bg="#F44336", fg="white", font=("Arial", 12)
            )
            delete_button.pack(side="right")

    except Exception as e:
        messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")


# Основное окно приложения
root = tk.Tk()
root.title("Управление файлами и папками в VK Cloud")
root.geometry("650x600")

# Фрейм для кнопок
button_frame = tk.Frame(root, bg="#f0f0f0")
button_frame.pack(pady=10, padx=10, fill="x")

# Кнопка для создания папки
create_folder_button = tk.Button(
    button_frame, text="Создать папку", command=create_folder, font=("Arial", 14), bg="#4CAF50", fg="white", width=15
)
create_folder_button.pack(side="left", padx=5)

# Кнопка для получения списка файлов
get_file_list_button = tk.Button(
    button_frame, text="Получить список файлов", command=lambda: load_file_list(""), font=("Arial", 14), bg="#2196F3", fg="white", width=20
)
get_file_list_button.pack(side="left", padx=5)

# Фрейм для отображения списка файлов
file_list_frame = tk.Frame(root)
file_list_frame.pack(pady=10, fill="both", expand=True, padx=10)

# Кнопка для загрузки файла
upload_button = tk.Button(
    root, text="Загрузить файл", command=upload_file, font=("Arial", 14), bg="#FF5733", fg="white", width=15
)
upload_button.pack(pady=10)

root.mainloop()
