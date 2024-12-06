import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import os
import time
import pyodbc
import requests
import logging
import query_data

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def configurar_driver():
    chrome_driver_path = os.path.join(os.getcwd(), 'chrome_driver', 'chromedriver.exe')

    chrome_options = Options()
    chrome_options.add_argument("--headless")  
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")  

    service = Service(chrome_driver_path)

    if not os.path.exists(chrome_driver_path):
        raise FileNotFoundError(f"ChromeDriver não encontrado em {chrome_driver_path}. Verifique o caminho.")

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)

    return driver
def buscar_links_no_diario(palavras_chave):
    driver = configurar_driver()
    url = "https://doe.sp.gov.br/busca-avancada"
    driver.get(url)

    todos_os_links = []

    for palavra_chave in palavras_chave:
        try:
            search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".css-1g557a2"))
            )
            add_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".css-10m9zcj"))
            )
            search_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".css-1oy4u67"))
            )

            try:
                delete_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".css-1ga7ilp"))
                )
                delete_button.click()
            except:
                pass  

            search_input.clear()
            search_input.send_keys(palavra_chave)
            add_input.click()
            search_button.click()

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".css-yzftv1"))
                )
            except:
                logging.warning(f"Nenhum resultado encontrado para '{palavra_chave}'.")
                continue  

            while True:
                resultados = driver.find_elements(By.CSS_SELECTOR, ".css-yzftv1")
                
                if not resultados:  
                    logging.warning(f"Nenhum link encontrado na página para '{palavra_chave}'.")
                    break

                for resultado in resultados:
                    try:
                        resultado.click()
                        time.sleep(1)  
                        driver.switch_to.window(driver.window_handles[-1])

                        url_atual = driver.current_url
                        if url_atual not in todos_os_links:
                            todos_os_links.append(url_atual)

                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    except Exception as e:
                        logging.error(f"Erro ao processar um resultado: {e}")
                        continue

                try:
                    next_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".css-6rdzsm"))
                    )
                    next_button.click()
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".css-yzftv1"))
                    )
                except:
                    logging.info(f"Fim dos resultados para '{palavra_chave}'.")
                    break

        except Exception as e:
            logging.error(f"Erro ao buscar links para '{palavra_chave}': {e}")
            continue

    driver.quit()
    return todos_os_links
def acessar_e_obter_texto_das_paginas(links):
    driver = configurar_driver() 
    resultados = []
    try:
        for link in links:
            try:
                logging.info(f"Acessando o link: {link}")
                driver.get(link)

                logging.info("Obtendo artigo")
                artigo = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".css-1e09a5c"))
                )
                texto = artigo.text
                logging.info("Obtendo titulo")
                titulo_element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".css-1wniyr8"))
                )

                logging.info(f"valor to titulo:{titulo_element.text}")

                titulo = titulo_element.text.strip()  

                logging.info(f"valor to titulo:{titulo}")

                resultados.append({
                    "texto": texto,
                    "titulo": titulo,
                    "link":link,
                    "estado":'SP'
                })

            except Exception as e:
                logging.error(f"Erro ao acessar o link {link}: {e}")
                resultados.append({
                    "texto": "",
                    "titulo": "",
                    "link":link,
                    "estado":'SP'
                })
    finally:
        driver.quit()

    return resultados


def buscar_palavras_chave_do_banco():
    server = '10.101.50.101,50000'
    database = 'Regulatorio2'
    username = 'usrOwnRegulario2'
    password = 's&0tp0s8WTmz4ST3xZG'
    
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
    )

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        query = "SELECT Palavra FROM PalavraChave WHERE Ativa = 1"
        cursor.execute(query)

        palavras_chave = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return palavras_chave

    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return []


def salvar_dados_no_banco(dados):
    server = '10.101.50.101,50000'
    database = 'Regulatorio2'
    username = 'usrOwnRegulario2'
    password = 's&0tp0s8WTmz4ST3xZG'
    
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
    )

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        query = """
        INSERT INTO ArquivosObtidos (
            LinkPagina, PalavraChave, NomeArquivo, 
            ResumoArquivo, DataArquivo, LinkDownload, 
            Estado, Relevante
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(query, dados)
        conn.commit()
        
        cursor.close()
        conn.close()
        print("Dados salvos com sucesso!")
    except Exception as e:
        print(f"Erro ao salvar dados no banco de dados: {e}")

def obter_dados_via_ollama_local(texto):
    try:
        prompt = (
            "analise o seguinte texto e forneça:\n"
            "1. Um resumo claro e objetivo. no qual você ira colocar escrito apenas 'Resumo: ' no inicio e mantenha esse padrão para fins de automação\n"
            "2. Uma avaliação se o texto é relevante para processos administrativos ou jurídicos e você coloca 'Relevante: ' no inicio e mantenha esse padrão para fins de automação"
            "Responda apenas 'Sim' ou 'Não' com base no conteúdo relevante."
            "Mantenha sempre esse padrão Resumo: e Relevante: para que não haja quebra de automação"
            f"\nTexto: {texto}"
        )

        logging.info("Enviando texto para a IA local para processamento...")
        resposta = query_data.query_rag(prompt)
        
        if not resposta or "Erro" in resposta:
            raise ValueError("A IA retornou uma resposta inválida ou erro.")

        resposta = resposta.strip()

        if "Resumo:" in resposta and "Relevante:" in resposta:
            resumo_pos = resposta.find("Resumo:")
            relevante_pos = resposta.find("Relevante:")

            resumo = resposta[resumo_pos + len("Resumo:"):relevante_pos].strip()
            relevancia = resposta[relevante_pos + len("Relevante:"):].strip().lower() == "sim"
        else:
            raise ValueError("Formato da resposta da IA incorreto.")

        return resumo, relevancia
    except Exception as e:
        logging.error(f"Erro ao obter dados da IA local: {e}")
        return "Erro ao gerar resumo", False
    
if __name__ == "__main__":
    palavras_chave = buscar_palavras_chave_do_banco()

    if not palavras_chave:
        print("Nenhuma palavra-chave ativa encontrada.")
    else:
        for palavra_chave in palavras_chave:
            print(palavra_chave)
            links = buscar_links_no_diario([palavra_chave])

            for link in links:
                print(resultados["texto"])
                resultados = acessar_e_obter_texto_das_paginas([link])
                resumo, relevante = obter_dados_via_ollama_local(resultados["texto"])

                nome_arquivo = f"{palavra_chave}_{link.split('/')[-1]}"
                data_arquivo = datetime.datetime.now() 
                estado = "SP"
                link_download = None

                dados = (link, palavra_chave, nome_arquivo, resumo, data_arquivo, link_download, estado, relevante)

                salvar_dados_no_banco(dados)