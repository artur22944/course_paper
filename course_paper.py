import requests
from datetime import datetime
import json
from private.API_TOKEN_ID import token_vk, user_id_vk, token_yandex

VK_VERSION = "5.131"
COUNT_PHOTO = int(input("Сколько фото загрузить? ").strip() or "5")
VK_ALBOMS = int(
    input("Выберети альбом для загрузки: 1. profile 2. wall 3. saved: ").strip() or "1"
)


# Преобразование времени
def time_conversion(vk_timestamp):
    vk_datetime = datetime.fromtimestamp(vk_timestamp)
    vk_date = vk_datetime.strftime("%d-%m-%Y")
    return vk_date


# Выбор альбома
def get_alboms(albom):
    if albom == 1:
        return "profile"
    elif albom == 2:
        return "wall"
    elif albom == 3:
        return "saved"
    else:
        return "profile"


# Получение списка фото c добавочной информацией
def get_photos(token, user_id, album, version, count):
    response = requests.get(
        url="https://api.vk.com/method/photos.get",
        params={
            "access_token": token,
            "owner_id": user_id,
            "album_id": album,
            "extended": 1,
            "photo_sizes": 1,
            "rev": 1,
            "v": version,
            "count": count,
        },
    ).json()["response"]

    return response


# Получение списка фото в максимального разрешения
def get_max_size(photo_list):
    max_url = []

    for photo in photo_list["items"]:
        likes_count = photo["likes"]["count"]
        date_load = time_conversion(photo["date"])
        photo_name = str(likes_count) + "_likes " + date_load

        max_rez = 0
        max_rez_url = None
        for size in photo["sizes"]:
            max_temp = size["width"] * size["height"]
            type_size = size["type"]
            if max_temp > max_rez:
                max_rez = max_temp
                max_rez_url = size["url"]

        max_url.append(
            {"Photo_name": photo_name, "URL": max_rez_url, "Size": type_size}
        )

    return max_url


# Вывод json - файла
def print_json(photo_list):
    json_list = []
    for photo in photo_list:
        json_list.append(
            {
                "file_name": photo["Photo_name"] + "+.jpg",
                "size": photo["Size"],
            }
        )

    with open(
        "C:/Users/artur/Desktop/ДЗ/Работа с внешним API/Курсовая/VK_photo.json",
        "w",
    ) as file:
        json.dump(json_list, file)


# Cоздание папки в яндекс диске
def create_folder_yandex(folder_name, token_yandex):

    print("Создание папки")

    response = requests.put(
        "https://cloud-api.yandex.net/v1/disk/resources",
        headers={"Authorization": f"OAuth {token_yandex}"},
        params={"path": {folder_name}},
    )

    if 400 <= response.status_code <= 409:
        print(f"Папка c названием {folder_name} уже существует")

    else:
        response.raise_for_status()
        print("Папка создана")


# Проверка существования файлов
def check_files_yandex(folder_name, token_yandex):

    name_in_list = []

    response = requests.get(
        "https://cloud-api.yandex.net/v1/disk/resources",
        headers={"Authorization": f"OAuth {token_yandex}"},
        params={"path": f"{folder_name}/"},
    )
    if 200 <= response.status_code < 300:
        date = response.json()["_embedded"]["items"]
        for file in date:
            name_in_list.append(file["name"])
    return name_in_list


# Загрузка фото в яндекс диск
def upload_yandex(photo_name, photo_url, folder_name, token_yandex):

    print(f"Загрузка фото - {photo_name}.jpg началась")

    response = requests.post(
        "https://cloud-api.yandex.net/v1/disk/resources/upload/",
        headers={"Authorization": f"OAuth {token_yandex}"},
        params={
            "url": photo_url,
            "path": f"{folder_name}/{photo_name}.jpg",
        },
    )
    if response.status_code == 202:
        print(f"Загрузка фото - {photo_name}.jpg завершена")
    else:
        response.raise_for_status()


if __name__ == "__main__":

    folder_name = "VK_photo"
    check_count = 0

    create_folder_yandex(folder_name, token_yandex)
    check_list = check_files_yandex(folder_name, token_yandex)
    alboms = get_alboms(VK_ALBOMS)

    photo_max_size = get_max_size(
        get_photos(token_vk, user_id_vk, alboms, VK_VERSION, COUNT_PHOTO)
    )

    for photo in photo_max_size:
        if photo["Photo_name"] + ".jpg" not in check_list:
            upload_yandex(photo["Photo_name"], photo["URL"], folder_name, token_yandex)
            check_count += 1
        else:
            print(f"Фото {photo['Photo_name']}.jpg уже существует")

    if len(photo_max_size) == check_count:
        print(
            f"Фотографии с альбома {alboms} в количестве {COUNT_PHOTO} шт. загружены в папку {folder_name} на яндекс диске."
        )
    else:
        print(
            f"Было загружено {check_count} фото из {len(photo_max_size)} альбома {alboms} в папку {folder_name} на яндекс диске."
        )

    print_json(photo_max_size)
