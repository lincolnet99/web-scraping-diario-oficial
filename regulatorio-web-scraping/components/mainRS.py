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

    service = Service(chrome_driver_path)

    if not os.path.exists(chrome_driver_path):
        raise FileNotFoundError(f"ChromeDriver não encontrado em {chrome_driver_path}. Verifique o caminho.")

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)

    return driver

def buscar_links_no_diario(palavras_chave):
    driver = configurar_driver()
    url = "https://www.diariooficial.rs.gov.br/"
    driver.get(url)
    resultados=[]
    todos_os_links = []  

    for palavra_chave in palavras_chave:
        try:
            search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "palavra-chave"))
            )

            search_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".pesquisar-btn"))
            )

            search_input.clear()
            search_input.send_keys(palavra_chave)
            search_button.click()

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".item-titulo"))
                )
            except:
                logging.warning(f"Nenhum resultado encontrado para '{palavra_chave}'.")
                continue  

            while True:
                resultados = driver.find_elements(By.CSS_SELECTOR, ".itens")
                print(f"Encontrados {len(resultados)} itens na página.")

                if not resultados:  
                    logging.warning(f"Nenhum link encontrado na página para '{palavra_chave}'.")
                    break

                for resultado in resultados:
                    try:

                        item_titulo = resultado.find_element(By.CSS_SELECTOR, ".item-titulo a")
                        link = item_titulo.get_attribute("href")

                        
                        driver.execute_script("window.open(arguments[0], '_blank');", link)

                        
                        driver.switch_to.window(driver.window_handles[-1])

                        
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".conteudo"))
                        )

                        
                        url_atual = driver.current_url
                        if url_atual not in todos_os_links:
                            todos_os_links.append(url_atual)

                        driver.close()  
                        driver.switch_to.window(driver.window_handles[0])  

                        WebDriverWait(driver, 10).until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".itens"))
                        )

                        resultados = driver.find_elements(By.CSS_SELECTOR, ".itens")
                        print(f"Recarregados {len(resultados)} itens.")

                    except Exception as e:
                        logging.error(f"Erro ao processar um resultado: {e}")
                        continue

                
                try:
                    elementos_next = driver.find_elements(By.CSS_SELECTOR, "li.page-item a[aria-label='Next']")

                    elementos_next.click()
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".item-titulo"))
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
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".conteudo"))
                )
                texto = artigo.text
                logging.info("Obtendo titulo")
                
                titulo_element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".assunto"))
                )

                titulo = titulo_element.text.strip()  


                
                resultados.append({
                    "texto": texto,
                    "titulo": titulo,
                    "link":link,
                    "estado":'RS'
                })

            except Exception as e:
                logging.error(f"Erro ao acessar o link {link}: {e}")
                resultados.append({
                    "texto": "",
                    "titulo": "",
                    "link":link,
                    "estado":'RS'
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
        # Define o prompt para a IA
        prompt = (
            "analise o seguinte texto e forneça:\n"
            "1. Um resumo claro e objetivo. no qual você ira colocar escrito apenas 'Resumo: ' no inicio e mantenha esse padrão para fins de automação\n"
            "2. Uma avaliação se o texto é relevante para processos administrativos ou jurídicos e você coloca 'Relevante: ' no inicio e mantenha esse padrão para fins de automação"
            "Responda apenas 'Sim' ou 'Não' com base no conteúdo relevante."
            "Mantenha sempre esse padrão Resumo: e Relevante: para que não haja quebra de automação"
            f"\nTexto: {texto}"
        )

        # Envia a consulta para a IA
        logging.info("Enviando texto para a IA local para processamento...")
        resposta = query_data.query_rag(prompt)
        
        if not resposta or "Erro" in resposta:
            raise ValueError("A IA retornou uma resposta inválida ou erro.")

        resposta = resposta.strip()

        # Processa a resposta (esperando que tenha dois componentes: Resumo e Relevância)
        if "Resumo:" in resposta and "Relevante:" in resposta:
            # Encontrar as posições dos dois campos
            resumo_pos = resposta.find("Resumo:")
            relevante_pos = resposta.find("Relevante:")

            # Obter as partes corretas, baseadas nas posições encontradas
            resumo = resposta[resumo_pos + len("Resumo:"):relevante_pos].strip()
            relevancia = resposta[relevante_pos + len("Relevante:"):].strip().lower() == "sim"
        else:
            raise ValueError("Formato da resposta da IA incorreto.")

        return resumo, relevancia
    except Exception as e:
        logging.error(f"Erro ao obter dados da IA local: {e}")
        return "Erro ao gerar resumo", False
    
# Executando o script
if __name__ == "__main__":
    palavras_chave = buscar_palavras_chave_do_banco()

    if not palavras_chave:
        print("Nenhuma palavra-chave ativa encontrada.")
    else:
        for palavra_chave in palavras_chave:
            print(palavra_chave)
            # Buscar links relacionados à palavra-chave atual
            links = buscar_links_no_diario([palavra_chave])

            # Processar cada link encontrado para a palavra-chave
            for link in links:
                # Obter texto da página
                resultados = acessar_e_obter_texto_das_paginas([link])
                for resultado in resultados:
                    texto = resultado.get('texto')
                    titulo = resultado.get('titulo', "Título desconhecido")
                    link_atual = resultado.get('link')
                    link_download = resultado.get('linkDownload')

                    resumo, relevante = obter_dados_via_ollama_local(texto)
                                                                                 # Gerar resumo e relevância via IA local
                    # Gerar outros dados
                    nome_arquivo = f"{palavra_chave}_{link.split('/')[-1]}"
                    data_arquivo = datetime.datetime.now() 
                    estado = "SP"
                    link_download = None

                    # Dados a serem salvos
                    dados = (link, palavra_chave, nome_arquivo, resumo, data_arquivo, link_download, estado, relevante)

                    # Salvar no banco
                    salvar_dados_no_banco(dados)