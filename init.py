import urllib.request
import urllib.parse
import json
import ssl
import csv
from datetime import date
from datetime import time
from datetime import datetime

def convertJson(dados): 
  try:
    return json.loads(dados)
  except Exception as ex:
    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
    message = template.format(type(ex).__name__, ex.args)
    print(message)
    return False

def getCatalogoRecursos():
  try:
    urlFilter = "$filter=" + urllib.parse.quote("Api eq 'taxas_cartoes' and Recurso eq '/itens' and Situacao eq 'Produção'")
    query = "$top=10000&" + urlFilter + "&$format=json"
    url = "https://olinda.bcb.gov.br/olinda/servico/DASFN/versao/v1/odata/Recursos?"+query
    webUrl = urllib.request.urlopen(url)
    if webUrl.getcode() != 200:
      print("Received error, cannot parse results")
      return False
    data = webUrl.read()
    return json.loads(data)
  except Exception as ex:
    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
    message = template.format(type(ex).__name__, ex.args)
    print(message)
    return False

def getTaxasBanco(banco):
  urlDados = banco["URLDados"]
  nome = banco["NomeInstituicao"]
  print(". capturando " + nome)
  try:
    webUrl = urllib.request.urlopen(urlDados, context=ssl._create_unverified_context())
    if webUrl.getcode() != 200:
      print("Received error, cannot parse results")
      return False
    dados = webUrl.read()
    print(".. capturado com sucesso!")
    return convertJson(dados)
  except Exception as ex:
    print(ex)
    return False

def preparaDadosTaxasBanco(dados):
  taxasNormalizadas = []
  cnpj = dados["emissorCnpj"]
  nome = dados["emissorNome"]
  taxas = dados["historicoTaxas"]
  for taxa in taxas:
    try:
      taxasNormalizadas.append({
        "emissorCnpj": cnpj,
        "emissorNome": nome,
        "taxaTipoGasto": taxa["taxaTipoGasto"],
        "taxaData": taxa["taxaData"],
        "taxaConversao": taxa["taxaConversao"],
        "taxaDivulgacaoDataHora": taxa["taxaDivulgacaoDataHora"]
      })
    except Exception as ex:
      print("Emissor: " + nome)
      print(ex)
  return taxasNormalizadas

def getTaxasBancos(catalogo):
  taxas = []
  if "value" in catalogo:
    bancos = catalogo["value"]
    for banco in bancos:
      dadosBanco = getTaxasBanco(banco)
      if (dadosBanco):
        taxas.append(dadosBanco)
    return taxas

def createFileName(base_name = "taxas_cartoes", dir_name = "./files/"):
  now = datetime.now()
  nowFormated = now.strftime("%Y%m%d%H%M%S%f")
  return dir_name + base_name + "_" + nowFormated + ".csv"

def saveCsvFile(dados, base_name = "taxas_cartoes", dir_name = "./files/"):
  if len(dados) <= 0: return False
  with open(createFileName(base_name, dir_name), 'w+', newline='') as f:
    csv.register_dialect('customDialect', quoting=csv.QUOTE_NONNUMERIC, delimiter=";")
    csvWriter = csv.DictWriter(f, fieldnames=dados[0].keys(), dialect='customDialect')
    csvWriter.writeheader()
    for linha in dados:
      csvWriter.writerow(linha)

def main():
  taxaBancos = []
  catalogo = getCatalogoRecursos()
  saveCsvFile(catalogo["value"], base_name="catalogo_taxas")
  if catalogo == False:
    print(".! Houve um problema ao capturar catalogo dos bancos.")
    return
  print(". catalogo de bancos capturado com sucesso.")
  taxas = getTaxasBancos(catalogo)
  print(".. taxas capturadas")
  for taxa in taxas:
    taxaBancos = taxaBancos + preparaDadosTaxasBanco(taxa)
  # jsonTaxas = json.dumps(taxaBancos)
  saveCsvFile(taxaBancos)
  print(". captura concluida")
  
if __name__ == "__main__":
  main()
