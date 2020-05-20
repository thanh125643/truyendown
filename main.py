from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import threading
import time
import os

# chạy conda env create -f environment.yml đẻt tạo môi trường chạy
# update thì chạy conda env update -f environment.yml


def updatedatabase(url):
    database = loadatabase()
    if url not in database:
        with open("databasebook.txt", "w+", encoding="utf-8") as file:
            file.write(url)


def loadatabase():
    database = []
    with open("databasebook.txt", "w+", encoding="utf-8") as file:
        database = file.readlines()
    return database


def updatemethod(url):
    database = loadatabase()
    for i in database:
        if url != i:
            khoitao(i, 1)


def khoitao(url, timedelay):
    try:
        print("Khoi tao trang web de lay link truyen")
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(executable_path="geckodriver.exe", options=options)
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        windownload = min(32, os.cpu_count() * 2 + 4)
        print("Dang lay danh sach link truyen xin cho")
        name = driver.title

        listtruyen = driver.find_element_by_xpath(
            "/html/body/div[1]/main/div/div/section[2]/div/ul/li[2]/a"
        )
        listtruyen.click()

        listtruyen = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "/html/body/div[1]/main/div/div/section[2]/div/div/div[2]/div/div/div/div/div[1]/div[1]/div/a",
                )
            )
        )

        link = listtruyen.get_attribute("href")
        maxnumber = list(filter(lambda x: x != "", link.split("/")))
        maxnumber = int(maxnumber[-1].split("-")[-1])
        truyens = []
        for i in range(maxnumber, 0, -1):
            truyens.append(url + "chuong-" + str(i) + "/")
    except Exception:
        driver.quit()
    else:
        driver.quit()
        updatedatabase(url)
        setupdownload(name, truyens, maxnumber, windownload, timedelay)


def has_live_threads(threads):
    return True in [t.is_alive() for t in threads]


def setupdownload(name, truyens, maxnumber, windownload, timedelay):
    print("Khoi tao qua trinh download truyen: " + name)
    if not os.path.exists(name):
        os.mkdir(name)
    else:
        t = os.listdir(name)
        truyens = truyens[: -len(t)]

    if maxnumber > len(truyens):
        maxnumber = len(truyens)
        print("Update truyen:" + name)

    if maxnumber == 0:
        print("Truyện chưa ra chương mới")
        return 0

    qbar = tqdm(total=maxnumber)
    thread = []
    lock = threading.Lock()

    for i in range(windownload + 1):
        p = download(name, truyens, timedelay, lock, qbar)
        p.daemon = True
        p.start()
        thread.append(p)

    while has_live_threads(thread):
        try:
            for i in thread:
                i.join(1)
        except KeyboardInterrupt:
            print("\nThoat chuong trinh do nguoi dung")
            for i in thread:
                i.kill_received = True
            qbar.close()
            return 0
    qbar.close()
    print("Tai ve " + name + " thanh cong")
    print("Tong so chuong da tai la : " + str(maxnumber) + " chuong")


class download(threading.Thread):
    def __init__(self, named, truyens, timedelay, lock, qbar):
        threading.Thread.__init__(self)
        self.named = named
        self.truyens = truyens
        self.timedelay = timedelay
        self.lock = lock
        self.qbar = qbar
        self.kill_received = False

    def run(self):
        header = {
            "user-agent": "Mozilla/5.0 (Windows NT x.y; Win64; x64; rv:10.0) Gecko/20100101 Firefox/10.0"
        }
        path = os.path.join(self.named)
        while not self.kill_received and self.truyens:
            self.lock.acquire()
            i = self.truyens.pop()
            self.lock.release()
            req = requests.get(i, headers=header)
            soup = BeautifulSoup(req.text, "lxml")
            title = soup.select("div.header:nth-child(3) > h2:nth-child(1)")
            noidung = soup.find(id="js-truyencv-content").get_text(separator="\n\n")
            chuong = list(filter(lambda x: x != "", i.split("/")))[-1]
            pathchuong = os.path.join(path, chuong + ".txt")
            with open(pathchuong, "w", encoding="utf-8") as file:
                file.write(title[0].get_text() + "\n\n")
                file.write(noidung)
            self.lock.acquire()
            self.qbar.update(1)
            self.lock.release()
            time.sleep(self.timedelay)


if __name__ == "__main__":
    url = "https://truyencv.com/thai-co-long-tuong-quyet/"
    timedelay = 1
    khoitao(url, timedelay)
    update = input("Bạn có muốn update tất cả các truyện bạn đã tải không ?Y/N")
    if update == "Y" or update == "Yes" or update == "yes":
        updatemethod(url)
    else:
        print("You won't get mecry")
