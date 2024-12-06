import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

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

def preencher_data(driver, elemento, texto):
    for caractere in texto:
        driver.execute_script("""
            var input = arguments[0];
            var event = new KeyboardEvent('keydown', {key: arguments[1]});
            input.dispatchEvent(event);
            input.value += arguments[1];
            event = new Event('input', { bubbles: true });
            input.dispatchEvent(event);
        """, elemento, caractere)

def buscar_links_no_diario():
    driver = configurar_driver()
    url = "https://dodf.df.gov.br/dodf/jornal/diario"
    driver.get(url)

    todos_os_links = []

    try:
        # Esperar até o dropdown ser carregado
        select_element = Select(driver.find_element(By.ID, "tpDemandante"))
        select_element.select_by_visible_text("Poder Executivo")

        # Espera até que os resultados estejam disponíveis
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".box-materia"))
        )

        # Captura todos os links dentro das matérias
        resultados = driver.find_elements(By.CSS_SELECTOR, ".box-materia a")

        for resultado in resultados:
            link = resultado.get_attribute("href")
            if link:
                try:
                    # Clicar no link e mudar para a nova aba
                    driver.execute_script("arguments[0].click();", resultado)
                    driver.switch_to.window(driver.window_handles[-1])

                    # Espera a página carregar (tempo de espera ajustável)
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".conteudo-materia"))
                    )

                    # Captura o conteúdo da página da nova aba
                    url_da_nova_guia = driver.current_url
                    todos_os_links.append(url_da_nova_guia)

                    # Fecha a aba e volta para a aba principal
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

                except Exception as e:
                    logging.error(f"Erro ao acessar a matéria: {e}")
                    continue

        logging.info("Processamento concluído.")
        driver.quit()
        return todos_os_links

    except Exception as e:
        logging.error(f"Erro ao buscar links: {e}")
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
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".conteudo-materia"))
                )
                texto = artigo.text
                titulo_element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".materia"))
                )
                link_download_element = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".link-box-materia"))
                )

                titulo = titulo_element.text.strip()  
                link_download = link_download_element.get_attribute("href")

                resultados.append({
                    "texto": texto,
                    "titulo": titulo,
                    "link":link,
                    "linkDownload":link_download,
                    "estado":'DF'
                })

            except Exception as e:
                logging.error(f"Erro ao acessar o link {link}: {e}")
                resultados.append({
                    "texto": "",
                    "titulo": "",
                    "link":link,
                    "estado":'DF'
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



def baixar_pdf(url, nome_arquivo):
    caminho_pasta = os.path.join(os.path.dirname(__file__), "data")
    caminho_arquivo = os.path.join(caminho_pasta, nome_arquivo)

    # Certifique-se de que a pasta 'data' existe
    os.makedirs(caminho_pasta, exist_ok=True)

    # Fazendo o download do arquivo
    try:
        print("Baixando o arquivo...")
        resposta = requests.get(url, stream=True)
        resposta.raise_for_status()  # Lança uma exceção para erros HTTP

        # Salvando o arquivo
        with open(caminho_arquivo, "wb") as arquivo_pdf:
            for chunk in resposta.iter_content(chunk_size=8192):  # Baixa em pedaços
                arquivo_pdf.write(chunk)
        print(f"Arquivo salvo em: {caminho_arquivo}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar o arquivo: {e}")

def obter_dados_via_ollama_local(texto, palavras_chave):
    try:
        palavras_chave_str = ", ".join(palavras_chave)
        logging.info(palavras_chave_str)

        prompt = (
            "analise o seguinte texto e forneça:\n"
            "1. Um resumo claro e objetivo. no qual você ira colocar escrito apenas 'Resumo: ' no inicio e mantenha esse padrão para fins de automação\n"
            "2. Qual das palavras-chave da lista mais exemplifica o resumo feito, caso nenhuma seja correlata, retorne: palavra_chave: 'Nenhuma', do contrario retorne palavra_chave: '' com o valor que voce achar correlato no inicio e mantenha esse padrão para fins de automação"
            "3. Uma avaliação se o texto é relevante para processos administrativos ou jurídicos e você coloca 'Relevante: ' no inicio e mantenha esse padrão para fins de automação"
            "Responda apenas 'Sim' ou 'Não' com base no conteúdo relevante."
            "Mantenha sempre esse padrão Resumo:, Relevante:, palavra_chave: para que não haja quebra de automação"
            f"\nTexto: {texto}, Palavras Chave a serem comparadas: {palavras_chave_str}"
        )

        logging.info("Enviando texto para a IA local para processamento...")
        resposta = query_data.query_rag(prompt)

        if not resposta or "Erro" in resposta:
            raise ValueError("A IA retornou uma resposta inválida ou erro.")

        resposta = resposta.strip()
        logging.info(f"Resposta da IA: {resposta}")

        # Garantir que todas as partes existem
        resumo = None
        relevancia = None
        palavra_chave = None

        if "Resumo:" in resposta:
            resumo_pos = resposta.find("Resumo:") + len("Resumo:")
            relevante_pos = resposta.find("Relevante:")
            resumo = resposta[resumo_pos:relevante_pos].strip() if relevante_pos != -1 else resposta[resumo_pos:].strip()

        if "Relevante:" in resposta:
            relevante_pos = resposta.find("Relevante:") + len("Relevante:")
            palavra_chave_pos = resposta.find("palavra_chave:")
            relevancia = resposta[relevante_pos:palavra_chave_pos].strip().lower() == "sim" if palavra_chave_pos != -1 else resposta[relevante_pos:].strip().lower() == "sim"

        if "palavra_chave:" in resposta:
            palavra_chave_pos = resposta.find("palavra_chave:") + len("palavra_chave:")
            palavra_chave = resposta[palavra_chave_pos:].strip()

        # Garantir que nenhum valor seja retornado como None
        resumo = resumo or "Erro ao gerar resumo"
        relevancia = relevancia or False
        palavra_chave = palavra_chave or "Nenhuma"

        return resumo, relevancia, palavra_chave

    except Exception as e:
        logging.error(f"Erro ao obter dados da IA local: {e}")
        return "Erro ao gerar resumo", False, "Nenhuma"

if __name__ == "__main__":
    palavras_chave = buscar_palavras_chave_do_banco()

    if not palavras_chave:
        print("Nenhuma palavra-chave ativa encontrada.")
    else:
            links = buscar_links_no_diario()

            for link in links:
                resultados = acessar_e_obter_texto_das_paginas([link])
                for resultado in resultados:
                    texto = resultado.get('texto')
                    titulo = resultado.get('titulo', "Título desconhecido")
                    link_atual = resultado.get('link')
                    link_download = resultado.get('linkDownload')

                    resumo, relevante, palavra_chave= obter_dados_via_ollama_local(texto, palavras_chave)

                    if(palavra_chave != "Nenhuma" and palavra_chave != ""):
                        data_arquivo = datetime.datetime.now()
                        estado = resultado.get('estado')                                       
                        # Dados a serem salvos
                        dados = (
                            link_atual,  # URL do link
                            palavra_chave,  # Palavra-chave processada
                            titulo,  # Título ou nome do arquivo
                            resumo,  # Resumo gerado
                            data_arquivo,  # Data e hora da extração
                            link_download,  # Link de download (se disponível)
                            estado,  # Estado associado
                            True if relevante else False  # Relevância avaliada pela IA
                        )
                        salvar_dados_no_banco(dados)
                        if(link_download != None):
                            baixar_pdf(link_download, titulo + ".pdf")