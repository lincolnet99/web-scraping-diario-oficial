from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


def configurar_driver():

    # Caminho correto para o ChromeDriver (substitua pelo caminho correto)
    chrome_driver_path = r"C:\Users\linco\Desktop\chromedriver-win64\chromedriver.exe"  # Exemplo: C:\chromedriver\chromedriver.exe

    # Configuração das opções do Chrome
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Inicializando o driver com o caminho do ChromeDriver e opções configuradas
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver

def buscar_links_no_diario(palavra_chave):
    driver = configurar_driver()
    url = "https://www.in.gov.br/leiturajornal?data=22-11-2024#daypicker"
    driver.get(url)


    try:


        for palavra_chave in palavras_chave:
            while True:
                # Esperar pelo campo de busca e interagir com ele
                search_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "search-bar"))
                )
                search_input.clear()
                search_input.send_keys(palavra_chave)
                search_input.send_keys(Keys.RETURN)  # Pressionar Enter

                # Esperar que os resultados sejam carregados
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".resultados-wrapper"))
                )

                # Capturar os links dos resultados
                resultados = driver.find_elements(By.CSS_SELECTOR, ".resultados-wrapper a")
                links = [resultado.get_attribute("href") for resultado in resultados if resultado.get_attribute("href")]

                print(f"Encontrados {len(links)} links para '{palavra_chave}' na página atual.")

                # Verificar se existe o botão "Próximo"
                try:
                    proximo_button = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "li.page-item button#rightArrow"))
                    )
                    if proximo_button.is_enabled():
                        proximo_button.click()  # Clica para ir para a próxima página
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".resultados-wrapper"))
                        )  # Aguarda o carregamento da nova página
                    else:
                        break  # Não há mais páginas, sai do loop
                except:
                    break  # Não encontrou o botão "Próximo", sai do loop

    except Exception as e:
        print(f"Erro ao buscar os links: {e}")
    finally:
        driver.quit()

        return links

# Testando o script
if __name__ == "__main__":
    palavras_chave = ["licitação", "contrato", "registro"]
    links = buscar_links_no_diario(palavras_chave)
    print(f"Encontrados {len(links)} links para '{palavras_chave}'.")
    for link in links: 
        print(link)