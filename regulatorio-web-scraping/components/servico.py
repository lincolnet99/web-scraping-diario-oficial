import schedule
import time
import datetime
from threading import Thread
import logging
import main
import mainRS
import mainDF
import os
import requests



logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
MAX_ARQUIVOS = 5 
DIRETORIO_DOWNLOAD = "./data"

def executar_tarefa_diaria():
    executar_tarefa_SP()
    executar_tarefa_RS()
    executar_tarefa_DF()

def executar_tarefa_SP():
    if not os.path.exists(DIRETORIO_DOWNLOAD):
        os.makedirs(DIRETORIO_DOWNLOAD)

    try:
        logging.info("Iniciando tarefa diária.")
        palavras_chave = main.buscar_palavras_chave_do_banco()

        if not palavras_chave:
            logging.warning("Nenhuma palavra-chave ativa encontrada.")
            return

        for palavra_chave in palavras_chave:
            logging.info(f"Processando palavra-chave: {palavra_chave}")

            # Buscar links relacionados à palavra-chave atual
            links = main.buscar_links_no_diario([palavra_chave])
            if not links:
                logging.warning(f"Nenhum link encontrado para a palavra-chave: {palavra_chave}")
                continue

            # Obter texto e links de download das páginas
            resultados = main.acessar_e_obter_texto_das_paginas(links)
            for resultado in resultados:
                texto = resultado.get('texto')
                titulo = resultado.get('titulo', "Título desconhecido")
                link_atual = resultado.get('link')

                # Pular se não houver texto extraído
                if not texto:
                    logging.warning("Texto vazio. Pulando este resultado.")
                    continue

                # Gerar resumo e relevância via IA local
                resumo, relevante = main.obter_dados_via_ollama_local(texto)

                # Nome do arquivo baseado na palavra-chave e título
                data_arquivo = datetime.datetime.now()
                estado = resultado.get('estado')

                # Dados a serem salvos
                dados = (
                    link_atual,  # URL do link
                    palavra_chave,  # Palavra-chave processada
                    titulo,  # Título ou nome do arquivo
                    resumo,  # Resumo gerado
                    data_arquivo,  # Data e hora da extração
                    '',  # Link de download (se disponível)
                    estado,  # Estado associado
                    True if relevante else False  # Relevância avaliada pela IA
                )

                # Salvar no banco
                logging.info(f"Salvando dados no banco para {titulo}")
                main.salvar_dados_no_banco(dados)

        logging.info("Tarefa diária concluída com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao executar a tarefa diária: {e}")

def executar_tarefa_RS():
    if not os.path.exists(DIRETORIO_DOWNLOAD):
        os.makedirs(DIRETORIO_DOWNLOAD)

    try:
        logging.info("Iniciando tarefa diária.")
        palavras_chave = mainRS.buscar_palavras_chave_do_banco()

        if not palavras_chave:
            logging.warning("Nenhuma palavra-chave ativa encontrada.")
            return

        for palavra_chave in palavras_chave:
            logging.info(f"Processando palavra-chave: {palavra_chave}")

            # Buscar links relacionados à palavra-chave atual
            links = mainRS.buscar_links_no_diario([palavra_chave])
            if not links:
                logging.warning(f"Nenhum link encontrado para a palavra-chave: {palavra_chave}")
                continue

            # Obter texto e links de download das páginas
            resultados = mainRS.acessar_e_obter_texto_das_paginas(links)
            for resultado in resultados:
                texto = resultado.get('texto')
                titulo = resultado.get('titulo', "Título desconhecido")
                link_atual = resultado.get('link')
                link_download = resultado.get('linkDownload')

                # Pular se não houver texto extraído
                if not texto:
                    logging.warning("Texto vazio. Pulando este resultado.")
                    continue

                # Gerar resumo e relevância via IA local
                resumo, relevante = mainRS.obter_dados_via_ollama_local(texto)

                # Nome do arquivo baseado na palavra-chave e título
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

                # Salvar no banco
                logging.info(f"Salvando dados no banco para {titulo}")
                mainRS.salvar_dados_no_banco(dados)

        logging.info("Tarefa diária concluída com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao executar a tarefa diária: {e}")


def executar_tarefa_DF():

        if not os.path.exists(DIRETORIO_DOWNLOAD):
            os.makedirs(DIRETORIO_DOWNLOAD)

        try:
            logging.info("Iniciando tarefa diária.")
            palavras_chave = mainDF.buscar_palavras_chave_do_banco()

            if not palavras_chave:
                logging.warning("Nenhuma palavra-chave ativa encontrada.")
                return

        

            # Buscar links relacionados à palavra-chave atual
            links = mainDF.buscar_links_no_diario()
            if not links:
                logging.warning(f"Nenhum link encontrado")
                

            # Obter texto e links de download das páginas
                resultados = mainDF.acessar_e_obter_texto_das_paginas(links)
                for resultado in resultados:
                    texto = resultado.get('texto')
                    titulo = resultado.get('titulo', "Título desconhecido")
                    link_atual = resultado.get('link')
                    link_download = resultado.get('linkDownload')

                    # Pular se não houver texto extraído
                    if not texto:
                        logging.warning("Texto vazio. Pulando este resultado.")
                        continue

                    # Gerar resumo e relevância via IA local
                    resumo, relevante, palavra_chave = mainDF.obter_dados_via_ollama_local(texto, palavras_chave)

                    # Nome do arquivo baseado na palavra-chave e título
                    data_arquivo = datetime.datetime.now()
                    estado = resultado.get('estado')

                    # Dados a serem salvos
                    if(palavra_chave != "Nenhuma"):
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
                        mainDF.salvar_dados_no_banco(dados)
                        if(link_download != None):
                            mainDF.baixar_pdf(link_download, titulo + ".pdf")

            logging.info("Tarefa diária concluída com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao executar a tarefa diária: {e}")

def agendar_tarefa():
    # Agenda a tarefa para rodar de segunda a sexta às 10h
    schedule.every().monday.at("10:00").do(executar_tarefa_diaria)
    schedule.every().tuesday.at("10:00").do(executar_tarefa_diaria)
    schedule.every().wednesday.at("10:00").do(executar_tarefa_diaria)
    schedule.every().thursday.at("10:00").do(executar_tarefa_diaria)
    schedule.every().friday.at("10:00").do(executar_tarefa_diaria)

    # Mantém o agendador em execução contínua
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # Executar o agendador em uma thread separada
    logging.info("Iniciando o serviço...")
    thread = Thread(target=agendar_tarefa)
    thread.daemon = True  # Permite que o programa seja interrompido com Ctrl+C
    thread.start()

    # Mantém o script principal ativo
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Serviço encerrado pelo usuário.")
