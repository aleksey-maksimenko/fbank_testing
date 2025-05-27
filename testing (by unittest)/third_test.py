from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import unittest
import time

class FBankTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = "http://localhost:8000/?balance=30000&reserved=20001"
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

    def test_valid_card_number_length(self):
        """
        Тест-кейс 1. Номер карты равен 16 символам
        Цель: Проверить успешность перевода при корректной длине номера карты.
        Шаги:
        1. Ввести номер карты `1234 5678 9012 3456`.
        2. Указать допустимую сумму перевода.
        3. Нажать кнопку «Перевести».
        Ожидаемый результат: Перевод выполняется, номер карты считается корректным.
        """
        driver = self.driver
        # выбираем карту рубли
        rub_card = driver.find_element(By.XPATH, "//*[@id='root']/div/div/div[1]/div[1]")
        rub_card.click()
        time.sleep(1)
        # вводим корректный номер карты
        card_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[1]')
        card_input.clear()
        card_input.send_keys("1234 5678 9012 3456")
        time.sleep(1)
        # вводим допустимую сумму перевода
        amount_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[2]')
        amount_input.clear()
        amount_input.send_keys("100")
        time.sleep(1)
        # проверяем наличие кнопки и нажимаем, если она есть
        try:
            transfer_button = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/button')
            if transfer_button.is_displayed() and transfer_button.is_enabled():
                transfer_button.click()
                time.sleep(1)
                # проверяем alert
                alert = driver.switch_to.alert
                alert_text = alert.text
                alert.accept()
                if "Перевод" in alert_text:
                    print(f"Перевод успешно выполнен: {alert_text}")
                else:
                    print(f"[BUG] Alert показан, но текст не подтверждает успешный перевод: {alert_text}")
            else:
                print("[BUG] Кнопка перевода недоступна при корректном номере карты.")
        except Exception as e:
            print(f"[BUG] Кнопка перевода не найдена или alert не появился: {e}")

    def test_invalid_amounts(self):
        """
        Тест-кейс 2. Перевод суммы с недопустимыми значениями — валюта Рубли
        Цель: Проверить блокировку перевода при нулевой и отрицательной сумме.
        Шаги:
        1. Ввести корректный номер карты.
        2. Ввести суммы 0, -100, -1000 в поле «Сумма перевода».
        3. Нажать «Перевести».
        Ожидаемый результат: Перевод невозможен при недопустимом значении суммы.
        """
        driver = self.driver
        # выбираем рубли
        rub_card = driver.find_element(By.XPATH, "//*[@id='root']/div/div/div[1]/div[1]")
        rub_card.click()
        time.sleep(1)
        # вводим корректный номер карты
        card_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[1]')
        card_input.clear()
        card_input.send_keys("1234 5678 9012 3456")
        time.sleep(1)
        invalid_amounts = ["0", "-100", "-1000"]
        for amount in invalid_amounts:
            # вводим сумму
            amount_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[2]')
            amount_input.clear()
            amount_input.send_keys(amount)
            time.sleep(1)
            # пробуем нажать на кнопку, если доступна
            try:
                transfer_button = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/button')
                if transfer_button.is_displayed() and transfer_button.is_enabled():
                    transfer_button.click()
                    time.sleep(1)
                    # проверяем alert
                    alert = driver.switch_to.alert
                    alert_text = alert.text
                    alert.accept()
                    print(f"[BUG] Перевод выполнен с недопустимой суммой {amount}: {alert_text}")
                else:
                    print(f"[OK] Кнопка перевода недоступна для суммы {amount}")
            except Exception as e:
                print(f"[OK] Перевод не выполнен для суммы {amount}, исключение: {e}")

    def test_exceed_transfer_amount_euro(self):
        """
        Тест-кейс 3. Превышение допустимой суммы перевода — валюта Евро
        Цель: Убедиться, что перевод блокируется при превышении доступных средств с учётом комиссии.
        Доступно: 274 €
        Комиссия: 10% ⇒ максимум ≈ 249 €
        """
        driver = self.driver
        # выбираем евро
        euro_card = driver.find_element(By.XPATH, "//*[@id='root']/div/div/div[1]/div[3]")
        euro_card.click()
        time.sleep(1)
        # вводим корректный номер карты
        card_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[1]')
        card_input.clear()
        card_input.send_keys("1234 5678 9012 3456")
        time.sleep(1)
        test_amounts = ["270", "1000", "5000", "9999"]
        for amount in test_amounts:
            # ввод суммы
            amount_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[2]')
            amount_input.clear()
            amount_input.send_keys(amount)
            time.sleep(1)
            try:
                transfer_button = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/button')
                if transfer_button.is_displayed() and transfer_button.is_enabled():
                    transfer_button.click()
                    time.sleep(1)
                    alert = driver.switch_to.alert
                    alert_text = alert.text
                    alert.accept()
                    print(f"[BUG] Перевод прошел с суммой {amount} €, текст: {alert_text}")
                else:
                    print(f"[OK] Перевод недоступен для суммы {amount} € — кнопка отключена")
            except Exception as e:
                print(f"[OK] Перевод блокирован корректно для {amount} € — исключение: {e}")

    def test_valid_dollar_amounts(self):
        """
        Тест-кейс 4. Корректная сумма перевода — валюта Доллары
        Цель: Подтвердить успешный перевод при сумме ≤ доступному остатку (100 $)
        """
        driver = self.driver
        # выбираем доллары
        dollar_card = driver.find_element(By.XPATH, "//*[@id='root']/div/div/div[1]/div[2]")
        dollar_card.click()
        time.sleep(1)
        # вводим корректный номер карты
        card_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[1]')
        card_input.clear()
        card_input.send_keys("1234 5678 9012 3456")
        time.sleep(1)
        test_amounts = ["10", "30", "90"]
        for amount in test_amounts:
            # ввод суммы
            amount_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[2]')
            amount_input.clear()
            amount_input.send_keys(amount)
            time.sleep(1)
            try:
                transfer_button = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/button')
                if transfer_button.is_displayed() and transfer_button.is_enabled():
                    transfer_button.click()
                    time.sleep(1)
                    alert = driver.switch_to.alert
                    alert_text = alert.text
                    alert.accept()
                    print(f"[OK] Перевод {amount} $ выполнен успешно — текст: {alert_text}")
                else:
                    print(f"[BUG] Кнопка недоступна при сумме {amount} $ — ожидался успешный перевод")
            except Exception as e:
                print(f"[BUG] Ошибка при попытке перевода {amount} $ — {e}")

    def test_valid_euro_amounts(self):
        """
        тест-кейс 5. корректная сумма перевода — валюта евро

        цель: подтвердить успешный перевод при сумме ≤ доступному остатку (274 €).

        шаги:
        1. выбрать счёт «евро».
        2. ввести корректный номер карты.
        3. ввести суммы 50, 10, 200.
        4. нажать «перевести».

        ожидаемый результат: перевод выполняется, появляется alert-подтверждение.
        """
        driver = self.driver
        # выбираем карту «евро»
        euro_card = driver.find_element(By.XPATH, "//*[@id='root']/div/div/div[1]/div[3]")
        euro_card.click()
        time.sleep(1)
        # вводим корректный номер карты
        card_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[1]')
        card_input.clear()
        card_input.send_keys("1234 5678 9012 3456")
        time.sleep(0.5)
        valid_amounts = ["50", "10", "200"]
        for amount in valid_amounts:
            with self.subTest(amount=amount):
                # ввод суммы
                amount_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[2]')
                amount_input.clear()
                amount_input.send_keys(amount)
                time.sleep(0.5)
                # ищем и нажимаем кнопку перевода
                transfer_btn = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/button')
                self.assertTrue(transfer_btn.is_enabled(),
                                f"кнопка недоступна при сумме {amount} € — ожидался успешный перевод")
                transfer_btn.click()
                time.sleep(1)
                # проверяем alert с подтверждением
                try:
                    alert = driver.switch_to.alert
                    alert_text = alert.text
                    alert.accept()
                    self.assertIn("Перевод", alert_text,
                                  f"alert не содержит подтверждения для суммы {amount} €: {alert_text}")
                    print(f"[OK] перевод {amount} € выполнен — {alert_text}")
                except Exception as e:
                    self.fail(f"[BUG] alert не появился для суммы {amount} € — {e}")

if __name__ == "__main__":
    unittest.main()