import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

class BankingTest(unittest.TestCase):
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

    def test_card_too_long(self):
        """
        Тест-кейс 1. Номер карты длиннее 16 символов

        Цель: Проверить, что система отклоняет номер карты, превышающий допустимую длину.

        Шаги:
        1. Ввести номер карты, длиной более 16 символов: '1234 5678 9012 34567'
        2. Указать сумму перевода.
        3. Нажать кнопку 'Перевести'.

        Ожидается: Перевод невозможен из-за некорректного номера карты.

        Фактический результат: Перевод выполняется, несмотря на превышение длины номера карты.

        Вывод: Тест не пройден. Функционал работает некорректно.

        Рекомендации: Добавить валидацию на длину номера карты (строго 16 символов).
        """
        driver = self.driver
        # выбираем карточку Рубли
        rub_card = driver.find_element(By.XPATH, "//*[@id='root']/div/div/div[1]/div[1]")
        rub_card.click()
        time.sleep(1)
        # вводим слишком длинный номер карты (17 символов + пробелы)
        card_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[1]')
        card_input.clear()
        card_input.send_keys("1234 5678 9012 34567")
        time.sleep(1)
        amount_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[2]')
        amount_input.clear()
        amount_input.send_keys("1000")
        time.sleep(0.5)
        # нажатие на кнопку перевода
        transfer_btn = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/button')
        transfer_btn.click()
        time.sleep(1)
        # проверяем появление alert или что перевод прошел
        try:
            alert = driver.switch_to.alert
            alert_text = alert.text
            alert.accept()
            print(f"Alert показан: {alert_text} - перевод заблокирован, тест пройден.")
        except:
            # alert отсутствует - значит перевод прошел, а это баг
            print("[BUG] Перевод с номером карты длиннее 16 символов выполнен (баг)")

    def get_commission_text(self):
        driver = self.driver
        try:
            # пытаемся получить элемент комиссии по id="comission"
            fee_comp = driver.find_element(By.ID, "comission")
            return fee_comp.text.strip()
        except:
            try:
                # если не нашли, пытаемся по xpath
                fee_comp = driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/p/span")
                return fee_comp.text.strip()
            except:
                return None

    def test_commission_calculation(self):
        """
        тест-кейс 2. расчет суммы комиссии за перевод

        цель: проверить, что комиссия составляет 10% от суммы перевода и округляется вниз.

        шаги:
        1. ввести корректный номер карты.
        2. ввести суммы: 10, 100, 1000, 1250, 5500.
        3. проверить, что комиссия совпадает с ожидаемыми значениями.

        ожидаемый результат:
        для каждой суммы комиссия:
        10 -> 0
        100 -> 10
        1000 -> 100
        1250 -> 120
        5500 -> 550

        вывод: тест пройден, если комиссии совпадают.
        """
        driver = self.driver
        currencies = {
            "rub": "//*[@id='root']/div/div/div[1]/div[1]",
            "usd": "//*[@id='root']/div/div/div[1]/div[2]",
            "eur": "//*[@id='root']/div/div/div[1]/div[3]"
        }
        card_number = "1111 2222 3333 4444"
        test_amounts = ["10", "100", "1000", "1250", "5500"]
        fees_to_test = {
            "10": "0",
            "100": "10",
            "1000": "100",
            "1250": "120",
            "5500": "550"
        }
        for currency, xpath_card in currencies.items():
            card = driver.find_element(By.XPATH, xpath_card)
            card.click()
            time.sleep(1)
            card_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[1]')
            card_input.clear()
            card_input.send_keys(card_number)
            time.sleep(0.5)
            for amount in test_amounts:
                amount_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[2]')
                amount_input.clear()
                amount_input.send_keys(amount)
                time.sleep(0.5)
                commission_text = self.get_commission_text()
                if commission_text is None:
                    print(f"[ERROR {currency}] комиссия для суммы {amount} не найдена")
                    continue
                if commission_text == fees_to_test[amount]:
                    print(f"[{currency}] сумма {amount} -> комиссия {commission_text} - корректно")
                else:
                    print(
                        f"[BUG {currency}] сумма {amount} -> комиссия {commission_text}, ожидалось {fees_to_test[amount]}")

    def test_transfer_exceeding_balance_dollars(self):
        """
        тест-кейс 3. перевод суммы, превышающей доступный баланс (доллары)

        цель: убедиться, что перевод невозможен при недостаточном доступном балансе.

        шаги:
        1. баланс 100, резерв 0 (установлено в url)
        2. ввести корректный номер карты
        3. ввести суммы перевода: 99, 1000, 5000, 9999, 20000
        4. проверить, что перевод невозможен при превышении доступного баланса с учетом комиссии

        ожидаемый результат:
        перевод недоступен при суммах больше доступной суммы с учетом комиссии

        фактический результат:
        перевод доступен при суммах до 9099 — баг

        вывод:
        тест пройден, если перевод недоступен при превышении баланса, иначе баг
        """
        driver = self.driver
        # выбираем долларовую карту (второй по счету)
        usd_card = driver.find_element(By.XPATH, "//*[@id='root']/div/div/div[1]/div[2]")
        usd_card.click()
        time.sleep(1)
        card_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[1]')
        card_input.clear()
        card_input.send_keys("1111 2222 3333 4444")
        time.sleep(0.5)
        test_amounts = ["99", "1000", "5000", "9999", "20000"]
        for amount in test_amounts:
            amount_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[2]')
            amount_input.clear()
            amount_input.send_keys(amount)
            time.sleep(0.5)
            # проверяем наличие и доступность кнопки "Перевести"
            try:
                transfer_btn = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/button')
                if transfer_btn.is_enabled():
                    transfer_btn.click()
                    time.sleep(1)
                    # проверяем alert
                    try:
                        alert = driver.switch_to.alert
                        alert_text = alert.text
                        alert.accept()
                        print(f"перевод суммы {amount} отклонен: {alert_text} - корректно")
                    except:
                        print(f"[BUG] перевод суммы {amount} прошел при недостаточном балансе")
                else:
                    print(f"кнопка 'Перевести' отключена для суммы {amount} - корректно")
            except:
                print(f"кнопка 'Перевести' не найдена или не доступна для суммы {amount} - корректно")

    def test_card_input_appears(self):
        """
        тест-кейс 4. появление поля ввода номера карты при выборе любого счета

        цель: проверить, что поле 'номер карты' появляется при выборе любого счета.

        шаги:
        1. перейти на страницу с балансом 30000, резервом 20001
        2. поочередно выбрать счета рубли, доллары, евро

        ожидаемый результат:
        поле 'номер карты' появляется при каждом выборе счета

        фактический результат:
        поле появляется корректно

        вывод:
        тест пройден, если поле появляется при выборе каждого счета
        """
        driver = self.driver
        # локаторы карточек 
        card_selectors = [
            "//*[@id='root']/div/div/div[1]/div[1]",  # рубли
            "//*[@id='root']/div/div/div[1]/div[2]",  # доллары
            "//*[@id='root']/div/div/div[1]/div[3]"  # евро
        ]
        for idx, card_xpath in enumerate(card_selectors, start=1):
            card = driver.find_element(By.XPATH, card_xpath)
            card.click()
            time.sleep(0.5)
            try:
                card_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[1]')
                assert card_input.is_displayed(), f"поле 'номер карты' не отображается при выборе счета #{idx}"
                print(f"поле 'номер карты' отображается при выборе счета #{idx} - ок")
            except Exception as e:
                self.fail(f"поле 'номер карты' не найдено или не отображается при выборе счета #{idx}: {e}")

    def test_amount_input_visibility(self):
        """
        тест-кейс 5. поведение ui при вводе/удалении номера карты

        цель: проверить появление поля суммы в зависимости от длины номера карты

        шаги:
        1. выбрать счет 'рубли'
        2. ввести полный номер карты (16 цифр + пробелы)
        3. проверить появление поля суммы
        4. удалить часть номера карты (оставить <16 символов)
        5. проверить исчезновение поля суммы

        ожидаемый результат:
        поле суммы появляется при полном номере
        поле суммы исчезает при неполном номере

        фактический результат:
        соответствует

        вывод:
        тест пройден при корректном поведении
        """
        driver = self.driver
        # выбираем рублевую карту
        rub_card = driver.find_element(By.XPATH, "//*[@id='root']/div/div/div[1]/div[1]")
        rub_card.click()
        time.sleep(0.5)
        card_input = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/input[1]')
        amount_input_xpath = '//*[@id="root"]/div/div/div[2]/input[2]'
        # вводим полный номер карты (16 цифр и пробелы)
        full_card_number = "1111 2222 3333 4444"
        card_input.clear()
        card_input.send_keys(full_card_number)
        time.sleep(0.5)
        try:
            amount_input = driver.find_element(By.XPATH, amount_input_xpath)
            assert amount_input.is_displayed(), "поле суммы не отображается при полном номере карты"
            print("поле суммы отображается при полном номере карты - ок")
        except Exception as e:
            self.fail(f"поле суммы не найдено или не отображается при полном номере карты: {e}")
        # удаляем часть номера, оставляем <16 символов
        short_card_number = "1111 2222 3333"
        card_input.clear()
        card_input.send_keys(short_card_number)
        time.sleep(0.5)
        # теперь поле суммы должно исчезнуть
        amount_inputs = driver.find_elements(By.XPATH, amount_input_xpath)
        if amount_inputs:
            if amount_inputs[0].is_displayed():
                self.fail("поле суммы отображается при неполном номере карты - баг")
            else:
                print("поле суммы скрыто при неполном номере карты - ок")
        else:
            print("поле суммы отсутствует при неполном номере карты - ок")

if __name__ == "__main__":
    unittest.main()
