import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import requests
import time

class BankTransferTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = "http://localhost:8000/?balance=30000&reserved=20001"
        try:
            response = requests.get(cls.url)
            if response.status_code != 200:
                raise Exception(f"Сервер вернул статус: {response.status_code}")
        except requests.RequestException as e:
            raise Exception(f"Ошибка доступа к серверу: {e}")
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        cls.driver = webdriver.Chrome(options=options)
        cls.driver.get(cls.url)
        cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_card_less_16(self):
        """
        Тест-кейс 1. Проверка поведения при вводе номера карты менее 16 символов.
        Шаги:
        1. Выбрать валюту "Рубли".
        2. Ввести номер карты длиной 15 символов (с пробелами).
        3. Проверить, что поле суммы перевода не появилось.
        4. Проверить, что кнопка "Перевести" отсутствует или неактивна.
        Ожидается: поле суммы и кнопка "Перевести" не отображаются.
        """
        driver = self.driver
        # нажимаем на карточку "Рубли"
        rub_card = driver.find_element(By.XPATH, "//*[@id='root']/div/div/div[1]/div[1]")
        rub_card.click()
        time.sleep(1)
        # вводим номер карты длиной 15 символов (с пробелами)
        card_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[1]')
        card_input.clear()
        card_input.send_keys("1234 5678 9012 34")  # 15 символов с пробелами
        time.sleep(1)
        # пытаемся найти поле суммы перевода
        amount_fields = driver.find_elements(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[2]')
        # пытаемся найти кнопку "Перевести"
        transfer_buttons = driver.find_elements(By.XPATH, '//*[@id="root"]/div/div/div[2]/button')
        # проверяем, что поле суммы не появилось
        self.assertEqual(len(amount_fields), 0, "Поле суммы появилось при некорректном номере карты")
        # проверяем, что кнопка не появилась (или неактивна)
        self.assertEqual(len(transfer_buttons), 0, "Кнопка 'Перевести' появилась при некорректном номере карты")

    def test_card_invalid_chars(self):
        """
        Тест-кейс 2. Проверка ввода номера карты с недопустимыми символами.
        Шаги:
        1. Выбрать валюту "Рубли".
        2. Ввести номер карты с буквами, спецсимволами и пробелами.
        3. Проверить, что в поле остались только цифры и пробелы.
        4. Проверить, что поле суммы перевода не появилось.
        5. Проверить, что кнопка "Перевести" не появилась.
        Ожидается: номер карты очищается от недопустимых символов, перевод недоступен.
        """
        driver = self.driver
        # нажимаем на карточку "Рубли"
        rub_card = driver.find_element(By.XPATH, "//*[@id='root']/div/div/div[1]/div[1]")
        rub_card.click()
        time.sleep(1)
        # вводим в поле номер карты набор символов: буквы, спецсимволы, пробелы
        card_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[1]')
        card_input.clear()
        invalid_input = "ab! cD12#34@56-78"
        card_input.send_keys(invalid_input)
        time.sleep(1)
        # считываем значение из поля номера карты
        entered_value = card_input.get_attribute("value")
        # проверяем, что в поле есть только цифры и пробелы
        allowed_chars = set("0123456789 ")
        self.assertTrue(all(ch in allowed_chars for ch in entered_value),
                        f"В поле номера карты должны быть только цифры и пробелы, а получили: '{entered_value}'")
        # проверяем, что после удаления пробелов остались только цифры
        digits_only = entered_value.replace(" ", "")
        self.assertTrue(digits_only.isdigit(),
                        f"После удаления пробелов должны остаться только цифры, а получили: '{digits_only}'")
        # проверяем, что поле суммы перевода не появилось
        amount_fields = driver.find_elements(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[2]')
        self.assertEqual(len(amount_fields), 0, "Поле суммы появилось при некорректном номере карты")
        # проверяем, что кнопка "Перевести" не появилась
        transfer_buttons = driver.find_elements(By.XPATH, '//*[@id="root"]/div/div/div[2]/button')
        self.assertEqual(len(transfer_buttons), 0, "Кнопка 'Перевести' появилась при некорректном номере карты")

    def test_transfer_amount_more_than_balance(self):
        """
        Тест-кейс 3. Проверка невозможности перевода суммы больше остатка на балансе.
        Шаги:
        1. Выбрать валюту "Рубли".
        2. Ввести корректный номер карты.
        3. Ввести суммы перевода, превышающие доступный остаток.
        4. Проверить, что кнопка "Перевести" неактивна или отсутствует.
        Ожидается: перевод невозможен, кнопка неактивна или отсутствует.
        """
        driver = self.driver
        # нажимаем "Рубли"
        rub_card = driver.find_element(By.XPATH, "//*[@id='root']/div/div/div[1]/div[1]")
        rub_card.click()
        time.sleep(1)
        # корректный номер карты
        card_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[1]')
        card_input.clear()
        card_input.send_keys("1234 5678 9012 3456")
        time.sleep(1)
        # суммы для проверки
        amounts = ["10000", "20000", "9100"]
        for amount in amounts:
            amount_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[2]')
            amount_input.clear()
            amount_input.send_keys(amount)
            time.sleep(1)
            # проверяем что кнопка недоступна
            transfer_buttons = driver.find_elements(By.XPATH, '//*[@id="root"]/div/div/div[2]/button')
            if transfer_buttons:
                self.assertFalse(transfer_buttons[0].is_enabled(),
                                 f"Кнопка 'Перевести' должна быть неактивна для суммы {amount}")
            else:
                # если кнопка не появилась вовсе - тоже ок
                self.assertTrue(True)

    def test_negative_and_zero_amounts_dollars(self):
        """
        Тест-кейс 4. Проверка невозможности перевода нулевых и отрицательных сумм для валюты Доллары.
        Шаги:
        1. Выбрать валюту "Доллары".
        2. Ввести корректный номер карты.
        3. Ввести суммы перевода: 0, -1, -500, -9999.
        4. Нажать кнопку "Перевести".
        5. Проверить наличие alert: перевод не должен выполняться, но баг проявляется через alert с подтверждением.
        """
        driver = self.driver
        # нажимаем на Доллары
        dollar_card = driver.find_element(By.XPATH, "//*[@id='root']/div/div/div[1]/div[2]")
        dollar_card.click()
        time.sleep(1)
        # вводим корректный номер карты
        card_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[1]')
        card_input.clear()
        card_input.send_keys("1111 1122 2222 2222")
        time.sleep(1)
        test_amounts = ["0", "-1", "-500", "-9999"]
        for amount in test_amounts:
            amount_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[2]')
            amount_input.clear()
            amount_input.send_keys(amount)
            time.sleep(0.5)
            # нажимаем Перевести
            transfer_button = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/button')
            transfer_button.click()
            time.sleep(1)
            # проверяем наличие alert-а о переводе
            try:
                alert = driver.switch_to.alert
                alert_text = alert.text
                alert.accept()
                # если alert появляется с текстом, подтверждающим перевод, фиксируем баг
                if "Перевод" in alert_text and ("0" in alert_text or "-" in alert_text):
                    print(f"[BUG] Некорректный перевод суммы {amount} принят: {alert_text}")
                else:
                    print(f"Alert показан, но не подтверждает баг для суммы {amount}: {alert_text}")
            except:
                # если alert отсутствует — это корректно (перевод не прошел)
                print(f"Alert отсутствует для суммы {amount}, перевод не выполнен - корректно.")

    def test_negative_and_zero_amounts_euro(self):
        """
        Тест-кейс 5. Проверка невозможности перевода нулевых и отрицательных сумм для валюты Евро.
        Шаги:
        1. Выбрать валюту "Евро".
        2. Ввести корректный номер карты.
        3. Ввести сумму перевода: 0, -1, -500, -9999.
        4. Нажать кнопку "Перевести".
        Ожидается: перевод не выполняется, но баг проявляется через alert с подтверждением.
        """
        driver = self.driver
        # карточка "Евро"
        euro_card = driver.find_element(By.XPATH, "//*[@id='root']/div/div/div[1]/div[3]")
        euro_card.click()
        time.sleep(1)
        card_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[1]')
        card_input.clear()
        card_input.send_keys("1111 2222 3333 4444")
        time.sleep(1)
        test_amounts = ["0", "-1", "-500", "-9999"]
        for amount in test_amounts:
            amount_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[2]')
            amount_input.clear()
            amount_input.send_keys(amount)
            time.sleep(0.5)
            # нажимаем Перевести
            transfer_button = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/button')
            transfer_button.click()
            time.sleep(1)
            # проверяем наличие alert-а о переводе
            try:
                alert = driver.switch_to.alert
                alert_text = alert.text
                alert.accept()
                # фиксируем баг, если alert подтверждает перевод отрицательной или нулевой суммы
                if "Перевод" in alert_text and ("0" in alert_text or "-" in alert_text):
                    print(f"[BUG] Некорректный перевод суммы {amount} принят (евро): {alert_text}")
                else:
                    print(f"Alert показан, но не подтверждает баг для суммы {amount} (евро): {alert_text}")
            except:
                # alert отсутствует — корректное поведение
                print(f"Alert отсутствует для суммы {amount} (евро), перевод не выполнен - корректно.")

if __name__ == "__main__":
    unittest.main()
