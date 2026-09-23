"""
Apresentar ao professor essa parte


os dados vêm do github publico, porém a tradução do que está escrito
Inglês para Português, foi feito por IA, isso é, o Script a seguir foi gerado por IA, porém, os dados que ela
utiliza não são. os dados são públicos do OpenPlantDB, que é um banco de dados de plantas de jardim em domínio público (CC0).
por ora, optamos por esse caminho pois o objeto de avaliação é o site que será desenvolvido.


===============================================================================
COMO USAR
===============================================================================

1. Rode o script:

       python gerar_plantas_json.py

2. Pronto. O arquivo Data/Plantas.json é criado ou atualizado.

Na primeira vez o script baixa sozinho o banco de dados (48 MB) e guarda em
_openplantdb.json, ao lado do script. Nas próximas vezes ele reaproveita o
arquivo baixado e roda em segundos.

IMPORTANTE: coloque _openplantdb.json no .gitignore. São 48 MB que não
precisam ir para o repositório do trabalho.


===============================================================================
O QUE O SCRIPT FAZ
===============================================================================

O OpenPlantDB tem 21.926 registros, contando todas as variedades de cada
planta (só de manjericão são 64). O script faz três coisas:

  1. ESCOLHE  - só entram as plantas da lista NOMES abaixo, que é a nossa
                curadoria. Cada linha tem o nome científico e o nome em
                português.

  2. RESUME   - junta todas as variedades de uma mesma espécie e tira o valor
                mais comum de luz e de água, e a mediana dos números. Assim
                uma variedade fora da curva não distorce a ficha.

  3. CALCULA  - dificuldade e ambiente não existem no banco. São calculados
                por regras simples, escritas nas funções lá embaixo.

O script NUNCA APAGA NADA. Se o Plantas.json já existe, ele é lido antes e
tudo que estiver escrito lá é preservado. Dá para editar o JSON na mão e
rodar o script de novo sem perder o texto.
"""

import json
import re
import statistics
import urllib.request
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


# =============================================================================
# 1. ONDE SALVAR
# =============================================================================
# O script acha a pasta Data sozinho, esteja ele na raiz do projeto ou dentro
# de Scripts/. Assim ninguém precisa ajustar caminho na mão.

PASTA_DO_SCRIPT = Path(__file__).resolve().parent

def achar_raiz_do_projeto():
    for pasta in (PASTA_DO_SCRIPT, PASTA_DO_SCRIPT.parent):
        if (pasta / "Data").is_dir():
            return pasta
    return PASTA_DO_SCRIPT            # sem pasta Data: cria do lado do script

RAIZ = achar_raiz_do_projeto()
ARQUIVO_SAIDA = RAIZ / "Data" / "Plantas.json"

ARQUIVO_BANCO = PASTA_DO_SCRIPT / "_openplantdb.json"

URL_BANCO = ("https://raw.githubusercontent.com/cwfrazier1/openplantdb"
             "/main/data/plants.json")


def achar_ou_baixar_banco():
    """Devolve o caminho do banco de dados, baixando na primeira vez.

    Se alguém já tiver clonado o repositório inteiro, aproveita o arquivo
    de lá em vez de baixar de novo.
    """
    if ARQUIVO_BANCO.exists():
        return ARQUIVO_BANCO

    for pasta in (PASTA_DO_SCRIPT, RAIZ, RAIZ / "Scripts", RAIZ / "Data"):
        clonado = pasta / "openplantdb" / "data" / "plants.json"
        if clonado.exists():
            return clonado

    print("Primeira execução: baixando o banco de dados (48 MB)...")
    print(f"  de  {URL_BANCO}")
    print(f"  para {ARQUIVO_BANCO.name}  (adicione ao .gitignore)")
    try:
        urllib.request.urlretrieve(URL_BANCO, ARQUIVO_BANCO)
    except Exception as erro:
        print(f"\nNão consegui baixar: {erro}")
        print("Baixe manualmente e salve como _openplantdb.json ao lado do script:")
        print(f"    {URL_BANCO}")
        return None
    print("  pronto.\n")
    return ARQUIVO_BANCO


# =============================================================================
# 2. TRADUÇÃO DOS VALORES
# =============================================================================
# O banco é em inglês e usa palavras fixas. Aqui viram os valores em português
# que o site usa nos filtros.

LUZ = {"full": "sol-pleno", "partial": "meia-sombra", "shade": "sombra"}
AGUA = {"low": "baixa", "moderate": "media", "high": "alta"}


# =============================================================================
# 3. A CURADORIA: QUAIS PLANTAS ENTRAM NO SITE
# =============================================================================
# Uma linha por planta:  "nome científico": ("Nome em português", "categoria")
#
# PARA ADICIONAR UMA PLANTA: escreva uma linha nova e rode o script.
# PARA TIRAR UMA PLANTA:     apague a linha e rode o script.
#
# Categorias possíveis: erva, hortalica, medicinal, ornamental, fruta

NOMES = {
# --- ervas e temperos ---
"ocimum basilicum": ("Manjericão", "erva"),
"ocimum gratissimum": ("Alfavaca", "erva"),
"salvia rosmarinus": ("Alecrim", "erva"),
"salvia officinalis": ("Sálvia", "erva"),
"salvia elegans": ("Sálvia-abacaxi", "erva"),
"mentha spicata": ("Hortelã", "erva"),
"mentha piperita": ("Hortelã-pimenta", "erva"),
"mentha pulegium": ("Poejo", "erva"),
"melissa officinalis": ("Erva-cidreira", "erva"),
"origanum vulgare": ("Orégano", "erva"),
"origanum majorana": ("Manjerona", "erva"),
"thymus vulgaris": ("Tomilho", "erva"),
"thymus serpyllum": ("Tomilho-rasteiro", "erva"),
"petroselinum crispum": ("Salsinha", "erva"),
"coriandrum sativum": ("Coentro", "erva"),
"anethum graveolens": ("Endro", "erva"),
"artemisia dracunculus": ("Estragão", "erva"),
"laurus nobilis": ("Louro", "erva"),
"foeniculum vulgare": ("Funcho", "erva"),
"pimpinella anisum": ("Erva-doce", "erva"),
"cuminum cyminum": ("Cominho", "erva"),
"carum carvi": ("Alcaravia", "erva"),
"nigella sativa": ("Nigela", "erva"),
"trigonella foenum-graecum": ("Feno-grego", "erva"),
"satureja hortensis": ("Segurelha", "erva"),
"hyssopus officinalis": ("Hissopo", "erva"),
"levisticum officinale": ("Levístico", "erva"),
"anthriscus cerefolium": ("Cerefólio", "erva"),
"borago officinalis": ("Borragem", "erva"),
"perilla frutescens": ("Perila", "erva"),
"nepeta cataria": ("Erva-dos-gatos", "erva"),
"monarda didyma": ("Monarda", "erva"),
"stevia rebaudiana": ("Estévia", "erva"),
"zingiber officinale": ("Gengibre", "erva"),
"curcuma longa": ("Açafrão-da-terra", "erva"),
"armoracia rusticana": ("Raiz-forte", "erva"),
"allium schoenoprasum": ("Cebolinha-francesa", "erva"),
"tropaeolum majus": ("Capuchinha", "erva"),

# --- medicinais ---
"matricaria chamomilla": ("Camomila", "medicinal"),
"chamaemelum nobile": ("Camomila-romana", "medicinal"),
"calendula officinalis": ("Calêndula", "medicinal"),
"lavandula angustifolia": ("Lavanda", "medicinal"),
"echinacea purpurea": ("Equinácea", "medicinal"),
"valeriana officinalis": ("Valeriana", "medicinal"),
"hypericum perforatum": ("Erva-de-são-joão", "medicinal"),
"urtica dioica": ("Urtiga", "medicinal"),
"plantago major": ("Tanchagem", "medicinal"),
"taraxacum officinale": ("Dente-de-leão", "medicinal"),
"symphytum officinale": ("Confrei", "medicinal"),
"ruta graveolens": ("Arruda", "medicinal"),
"artemisia absinthium": ("Losna", "medicinal"),
"tanacetum parthenium": ("Tanaceto", "medicinal"),
"aloe vera": ("Babosa", "medicinal"),
"cymbopogon citratus": ("Capim-limão", "medicinal"),
"althaea officinalis": ("Malva-branca", "medicinal"),
"salvia apiana": ("Sálvia-branca", "medicinal"),
"passiflora incarnata": ("Maracujá-de-flor", "medicinal"),
"verbena officinalis": ("Verbena", "medicinal"),

# --- hortaliças ---
"lactuca sativa": ("Alface", "hortalica"),
"eruca vesicaria": ("Rúcula", "hortalica"),
"diplotaxis tenuifolia": ("Rúcula-selvagem", "hortalica"),
"spinacia oleracea": ("Espinafre", "hortalica"),
"beta vulgaris": ("Beterraba", "hortalica"),
"daucus carota": ("Cenoura", "hortalica"),
"raphanus sativus": ("Rabanete", "hortalica"),
"brassica oleracea": ("Couve", "hortalica"),
"brassica rapa": ("Nabo", "hortalica"),
"brassica juncea": ("Mostarda", "hortalica"),
"solanum lycopersicum": ("Tomate", "hortalica"),
"solanum melongena": ("Berinjela", "hortalica"),
"solanum tuberosum": ("Batata", "hortalica"),
"capsicum annuum": ("Pimentão", "hortalica"),
"capsicum baccatum": ("Pimenta dedo-de-moça", "hortalica"),
"capsicum chinense": ("Pimenta-de-cheiro", "hortalica"),
"capsicum frutescens": ("Pimenta-malagueta", "hortalica"),
"cucumis sativus": ("Pepino", "hortalica"),
"cucurbita pepo": ("Abobrinha", "hortalica"),
"cucurbita moschata": ("Abóbora", "hortalica"),
"cucurbita maxima": ("Moranga", "hortalica"),
"citrullus lanatus": ("Melancia", "hortalica"),
"cucumis melo": ("Melão", "hortalica"),
"phaseolus vulgaris": ("Feijão-vagem", "hortalica"),
"phaseolus lunatus": ("Feijão-fava", "hortalica"),
"vigna unguiculata": ("Feijão-caupi", "hortalica"),
"pisum sativum": ("Ervilha", "hortalica"),
"zea mays": ("Milho", "hortalica"),
"abelmoschus esculentus": ("Quiabo", "hortalica"),
"apium graveolens": ("Aipo", "hortalica"),
"cichorium intybus": ("Chicória", "hortalica"),
"cichorium endivia": ("Escarola", "hortalica"),
"nasturtium officinale": ("Agrião", "hortalica"),
"ipomoea batatas": ("Batata-doce", "hortalica"),
"manihot esculenta": ("Mandioca", "hortalica"),
"colocasia esculenta": ("Inhame", "hortalica"),
"asparagus officinalis": ("Aspargo", "hortalica"),
"cynara cardunculus": ("Alcachofra", "hortalica"),
"pastinaca sativa": ("Pastinaca", "hortalica"),
"allium cepa": ("Cebola", "hortalica"),
"allium sativum": ("Alho", "hortalica"),
"allium fistulosum": ("Cebolinha", "hortalica"),
"allium ampeloprasum": ("Alho-poró", "hortalica"),
"arachis hypogaea": ("Amendoim", "hortalica"),
"helianthus tuberosus": ("Tupinambo", "hortalica"),
"portulaca oleracea": ("Beldroega", "hortalica"),
"basella alba": ("Bertalha", "hortalica"),
"pereskia aculeata": ("Ora-pro-nóbis", "hortalica"),
"sonchus oleraceus": ("Serralha", "hortalica"),
"momordica charantia": ("Melão-de-são-caetano", "hortalica"),
"sechium edule": ("Chuchu", "hortalica"),
"lagenaria siceraria": ("Cabaça", "hortalica"),
"luffa aegyptiaca": ("Bucha-vegetal", "hortalica"),
"vigna radiata": ("Feijão-mungo", "hortalica"),
"lens culinaris": ("Lentilha", "hortalica"),
"cicer arietinum": ("Grão-de-bico", "hortalica"),
"glycine max": ("Soja", "hortalica"),
"hibiscus sabdariffa": ("Vinagreira", "hortalica"),
"rheum rhabarbarum": ("Ruibarbo", "hortalica"),
"valerianella locusta": ("Alface-de-cordeiro", "hortalica"),
"atriplex hortensis": ("Armole", "hortalica"),
"amaranthus tricolor": ("Caruru", "hortalica"),
"xanthosoma sagittifolium": ("Taioba", "hortalica"),

# --- frutíferas ---
"fragaria ananassa": ("Morango", "fruta"),
"fragaria vesca": ("Morango-silvestre", "fruta"),
"rubus idaeus": ("Framboesa", "fruta"),
"rubus fruticosus": ("Amora-silvestre", "fruta"),
"morus nigra": ("Amoreira-preta", "fruta"),
"morus alba": ("Amoreira-branca", "fruta"),
"vaccinium corymbosum": ("Mirtilo", "fruta"),
"ribes rubrum": ("Groselha-vermelha", "fruta"),
"ribes nigrum": ("Cassis", "fruta"),
"vitis vinifera": ("Uva", "fruta"),
"ficus carica": ("Figo", "fruta"),
"punica granatum": ("Romã", "fruta"),
"citrus limon": ("Limão-siciliano", "fruta"),
"citrus latifolia": ("Limão-taiti", "fruta"),
"citrus reticulata": ("Mexerica", "fruta"),
"citrus sinensis": ("Laranja", "fruta"),
"citrus aurantiifolia": ("Limão-galego", "fruta"),
"malus domestica": ("Maçã", "fruta"),
"pyrus communis": ("Pera", "fruta"),
"prunus persica": ("Pêssego", "fruta"),
"prunus avium": ("Cereja", "fruta"),
"prunus domestica": ("Ameixa", "fruta"),
"prunus armeniaca": ("Damasco", "fruta"),
"eriobotrya japonica": ("Nêspera", "fruta"),
"psidium guajava": ("Goiaba", "fruta"),
"eugenia uniflora": ("Pitanga", "fruta"),
"plinia cauliflora": ("Jabuticaba", "fruta"),
"malpighia emarginata": ("Acerola", "fruta"),
"passiflora edulis": ("Maracujá", "fruta"),
"ananas comosus": ("Abacaxi", "fruta"),
"carica papaya": ("Mamão", "fruta"),
"musa acuminata": ("Banana", "fruta"),
"persea americana": ("Abacate", "fruta"),
"mangifera indica": ("Manga", "fruta"),
"annona muricata": ("Graviola", "fruta"),
"annona squamosa": ("Fruta-do-conde", "fruta"),
"averrhoa carambola": ("Carambola", "fruta"),
"physalis peruviana": ("Physalis", "fruta"),
"actinidia deliciosa": ("Kiwi", "fruta"),
"diospyros kaki": ("Caqui", "fruta"),
"cydonia oblonga": ("Marmelo", "fruta"),
"olea europaea": ("Oliveira", "fruta"),
"corylus avellana": ("Avelã", "fruta"),
"juglans regia": ("Noz", "fruta"),

# --- ornamentais ---
"dracaena trifasciata": ("Espada-de-são-jorge", "ornamental"),
"epipremnum aureum": ("Jiboia", "ornamental"),
"zamioculcas zamiifolia": ("Zamioculca", "ornamental"),
"spathiphyllum wallisii": ("Lírio-da-paz", "ornamental"),
"anthurium andraeanum": ("Antúrio", "ornamental"),
"monstera deliciosa": ("Costela-de-adão", "ornamental"),
"philodendron hederaceum": ("Filodendro", "ornamental"),
"maranta leuconeura": ("Maranta", "ornamental"),
"chlorophytum comosum": ("Clorofito", "ornamental"),
"nephrolepis exaltata": ("Samambaia-americana", "ornamental"),
"adiantum raddianum": ("Avenca", "ornamental"),
"aglaonema commutatum": ("Aglaonema", "ornamental"),
"dieffenbachia seguine": ("Comigo-ninguém-pode", "ornamental"),
"ficus lyrata": ("Figueira-lira", "ornamental"),
"ficus elastica": ("Falsa-seringueira", "ornamental"),
"ficus benjamina": ("Ficus-benjamina", "ornamental"),
"hedera helix": ("Hera", "ornamental"),
"tradescantia zebrina": ("Trapoeraba-roxa", "ornamental"),
"peperomia obtusifolia": ("Peperômia", "ornamental"),
"pilea peperomioides": ("Planta-da-moeda", "ornamental"),
"schefflera arboricola": ("Cheflera", "ornamental"),
"rhapis excelsa": ("Palmeira-ráfia", "ornamental"),
"chamaedorea elegans": ("Palmeira-de-salão", "ornamental"),
"dypsis lutescens": ("Areca-bambu", "ornamental"),
"aspidistra elatior": ("Aspidistra", "ornamental"),
"echeveria elegans": ("Echeveria", "ornamental"),
"sedum morganianum": ("Rabo-de-burro", "ornamental"),
"crassula ovata": ("Planta-jade", "ornamental"),
"kalanchoe blossfeldiana": ("Calanchoe", "ornamental"),
"schlumbergera truncata": ("Flor-de-maio", "ornamental"),
"haworthiopsis attenuata": ("Haworthia", "ornamental"),
"opuntia ficus-indica": ("Palma-forrageira", "ornamental"),
"streptocarpus ionanthus": ("Violeta-africana", "ornamental"),
"phalaenopsis amabilis": ("Orquídea-phalaenopsis", "ornamental"),
"begonia semperflorens-cultorum": ("Begônia", "ornamental"),
"impatiens walleriana": ("Beijinho", "ornamental"),
"petunia hybrida": ("Petúnia", "ornamental"),
"viola tricolor": ("Amor-perfeito", "ornamental"),
"viola cornuta": ("Violeta-de-chifre", "ornamental"),
"tagetes patula": ("Cravo-de-defunto", "ornamental"),
"tagetes erecta": ("Cravo-africano", "ornamental"),
"zinnia elegans": ("Zínia", "ornamental"),
"helianthus annuus": ("Girassol", "ornamental"),
"cosmos bipinnatus": ("Cosmos", "ornamental"),
"dianthus caryophyllus": ("Cravo", "ornamental"),
"dianthus barbatus": ("Cravina", "ornamental"),
"hibiscus rosa-sinensis": ("Hibisco", "ornamental"),
"gardenia jasminoides": ("Gardênia", "ornamental"),
"jasminum sambac": ("Jasmim", "ornamental"),
"plumeria rubra": ("Jasmim-manga", "ornamental"),
"bougainvillea glabra": ("Primavera", "ornamental"),
"ixora coccinea": ("Ixora", "ornamental"),
"catharanthus roseus": ("Vinca", "ornamental"),
"pelargonium graveolens": ("Gerânio-cheiroso", "ornamental"),
"pelargonium odoratissimum": ("Gerânio-maçã", "ornamental"),
"salvia splendens": ("Sálvia-vermelha", "ornamental"),
"celosia argentea": ("Crista-de-galo", "ornamental"),
"portulaca grandiflora": ("Onze-horas", "ornamental"),
"antirrhinum majus": ("Boca-de-leão", "ornamental"),
"lobularia maritima": ("Alisso", "ornamental"),
"gomphrena globosa": ("Perpétua", "ornamental"),
"torenia fournieri": ("Amor-perfeito-de-verão", "ornamental"),
"agapanthus africanus": ("Agapanto", "ornamental"),
"clivia miniata": ("Clívia", "ornamental"),
"zantedeschia aethiopica": ("Copo-de-leite", "ornamental"),
"strelitzia reginae": ("Estrelítzia", "ornamental"),
"dracaena fragrans": ("Dracena", "ornamental"),
"cordyline fruticosa": ("Cordiline", "ornamental"),
"neoregelia carolinae": ("Bromélia", "ornamental"),
"lavandula stoechas": ("Lavanda-francesa", "ornamental"),
"rosa chinensis": ("Roseira", "ornamental"),
"hydrangea macrophylla": ("Hortênsia", "ornamental"),
"camellia japonica": ("Camélia", "ornamental"),
"nerium oleander": ("Espirradeira", "ornamental"),
"cyclamen persicum": ("Ciclame", "ornamental"),
"primula obconica": ("Prímula", "ornamental"),
"begonia rex-cultorum": ("Begônia-rex", "ornamental"),
"aeonium arboreum": ("Aeonium", "ornamental"),
"agave americana": ("Agave", "ornamental"),
"yucca elephantipes": ("Iúca", "ornamental"),
"ipomoea tricolor": ("Glória-da-manhã", "ornamental"),
"lathyrus odoratus": ("Ervilha-de-cheiro", "ornamental"),
"papaver rhoeas": ("Papoula", "ornamental"),
"nigella damascena": ("Nigela-ornamental", "ornamental"),
"alcea rosea": ("Malva-rosa", "ornamental"),
"digitalis purpurea": ("Dedaleira", "ornamental"),
"delphinium elatum": ("Esporinha", "ornamental"),
"aquilegia vulgaris": ("Aquilégia", "ornamental"),
"rudbeckia hirta": ("Rudbéquia", "ornamental"),
"gaillardia pulchella": ("Gaillardia", "ornamental"),
"salvia farinacea": ("Sálvia-azul", "ornamental"),
"verbena bonariensis": ("Verbena-roxa", "ornamental"),
"scaevola aemula": ("Leque-azul", "ornamental"),
"lantana camara": ("Lantana", "ornamental"),
"duranta erecta": ("Pingo-de-ouro", "ornamental"),
}


# =============================================================================
# 4. EXEMPLOS DE PREENCHIMENTO
# =============================================================================
# Descrição, dicas, problemas e imagem NÃO existem no banco de dados. É o
# conteúdo escrito por nós.
#
# Abaixo tem um exemplo pronto de cada categoria, só para servir de modelo de
# formato. REESCREVAM COM AS PALAVRAS DE VOCÊS: esses textos foram gerados
# junto com o script.
#
# Vocês podem escrever aqui ou direto no Plantas.json, tanto faz: o script
# preserva os dois. Escrever aqui é melhor se quiserem que fique versionado
# junto do código.

EXEMPLOS = {

    # ---- categoria: erva ----
    "manjericao": {
        "descricao": (
            "Erva anual de folhas largas e muito aromáticas, das mais fáceis "
            "de manter em apartamento. Cresce rápido, aceita vaso pequeno e "
            "responde bem à colheita frequente: quanto mais se colhe, mais "
            "ramifica."
        ),
        "dicas": [
            "Colha as folhas de cima para baixo, sempre acima de um par de folhas",
            "Corte as flores assim que aparecerem: depois de florir, a folha perde sabor",
            "Regue pela manhã e evite molhar as folhas, que mancham com facilidade",
        ],
        "problemasComuns": [
            "Folhas amareladas embaixo: geralmente excesso de água ou vaso sem furo",
            "Caule esticado e folhas pequenas: falta de luz, precisa de mais sol direto",
            "Pontinhos brancos no verso da folha: pulgão, tratar com água e sabão neutro",
        ],
        "imagem": {
            "arquivo": "img/plantas/manjericao.jpg",
            "creditoAutor": "",
            "licenca": "",
            "origem": "",
        },
    },

    # ---- categoria: hortalica ----
    "alface": {
        "descricao": (
            "Folhosa de ciclo curto, pronta para colher em cerca de 45 dias. "
            "Cabe em jardineira rasa e é uma das melhores opções para quem "
            "está começando, porque o resultado aparece rápido."
        ),
        "dicas": [
            "Colha folha a folha, de fora para dentro, e a planta continua produzindo",
            "Prefira o sol da manhã: calor forte da tarde faz a folha amargar",
            "Semeie um vaso novo a cada duas semanas para ter colheita contínua",
        ],
        "problemasComuns": [
            "Planta espigando e ficando amarga: calor demais, mude para local mais fresco",
            "Folhas com furos: lesmas ou lagartas, revistar o verso das folhas à noite",
            "Crescimento parado e folhas pálidas: substrato pobre, falta adubação",
        ],
        "imagem": {
            "arquivo": "img/plantas/alface.jpg",
            "creditoAutor": "",
            "licenca": "",
            "origem": "",
        },
    },

    # ---- categoria: medicinal ----
    "babosa": {
        "descricao": (
            "Suculenta de folhas grossas que armazenam água, o que a torna "
            "quase imune ao esquecimento. Vive bem em vaso pequeno e é "
            "tradicionalmente usada no cuidado da pele."
        ),
        "dicas": [
            "Regue só quando o substrato estiver seco, a cada 15 dias ou mais",
            "Use substrato arenoso: terra que segura água apodrece a raiz",
            "As mudas que nascem ao redor podem ser separadas e replantadas",
        ],
        "problemasComuns": [
            "Folhas moles e escurecidas na base: excesso de água, principal causa de morte",
            "Folhas finas e enrugadas: aí sim está faltando água",
            "Manchas marrons nas pontas: sol forte demais logo após mudança de local",
        ],
        "imagem": {
            "arquivo": "img/plantas/babosa.jpg",
            "creditoAutor": "",
            "licenca": "",
            "origem": "",
        },
    },

    # ---- categoria: ornamental ----
    "jiboia": {
        "descricao": (
            "Trepadeira de folhas em formato de coração, muito usada em vasos "
            "suspensos. Tolera pouca luz e rega irregular, o que a torna a "
            "planta de interior mais indicada para quem nunca cuidou de uma."
        ),
        "dicas": [
            "Um galho cortado enraíza em um copo com água em cerca de duas semanas",
            "Limpe o pó das folhas de vez em quando: é assim que ela respira",
            "Podar os ramos mais longos deixa a planta mais cheia em vez de comprida",
        ],
        "problemasComuns": [
            "Folhas amarelas: quase sempre água demais, deixe o substrato secar",
            "Folhas novas pequenas e sem manchas claras: falta de luz",
            "Pontas marrons e secas: ar muito seco, borrife água nas folhas",
        ],
        "imagem": {
            "arquivo": "img/plantas/jiboia.jpg",
            "creditoAutor": "",
            "licenca": "",
            "origem": "",
        },
    },

    # ---- categoria: fruta ----
    "morango": {
        "descricao": (
            "Frutífera pequena que cabe em jardineira e vai bem em horta "
            "vertical. Produz do segundo mês em diante e se multiplica sozinha "
            "pelos ramos que lança para os lados."
        ),
        "dicas": [
            "Mantenha os frutos longe do contato com a terra para não apodrecerem",
            "Os ramos que a planta lança para os lados viram mudas novas",
            "Precisa de pelo menos cinco horas de sol direto para dar fruto",
        ],
        "problemasComuns": [
            "Frutos mofados antes de amadurecer: umidade demais e pouca ventilação",
            "Muita folha e nenhum fruto: excesso de adubo com nitrogênio",
            "Frutos pequenos e deformados: falta de polinização ou planta velha demais",
        ],
        "imagem": {
            "arquivo": "img/plantas/morango.jpg",
            "creditoAutor": "",
            "licenca": "",
            "origem": "",
        },
    },
}


# =============================================================================
# 5. FUNÇÕES AUXILIARES
# =============================================================================

def so_o_nome_da_especie(nome_cientifico):
    """'Ocimum basilicum Genovese' vira 'ocimum basilicum'.

    Serve para juntar todas as variedades de uma mesma espécie.
    """
    texto = (nome_cientifico or "").lower()
    texto = re.sub(r"['\"].*?['\"]", " ", texto)          # tira 'Genovese'
    texto = re.sub(r"\b(var|subsp|ssp|cv)\.?\b", " ", texto)
    texto = re.sub(r"[^a-z- ]", " ", texto)
    return " ".join(texto.split()[:2])                     # gênero + espécie


def virar_id(nome):
    """'Açafrão-da-terra' vira 'acafrao-da-terra'."""
    texto = nome.lower()
    for acentuada, simples in [("á","a"),("â","a"),("ã","a"),("à","a"),
                               ("é","e"),("ê","e"),("í","i"),("ó","o"),
                               ("ô","o"),("õ","o"),("ú","u"),("ç","c")]:
        texto = texto.replace(acentuada, simples)
    return re.sub(r"[^a-z0-9]+", "-", texto).strip("-")


def valor_mais_comum(valores):
    """De ['sol-pleno', 'sol-pleno', 'meia-sombra'] devolve 'sol-pleno'."""
    valores = [v for v in valores if v]
    if not valores:
        return None
    return Counter(valores).most_common(1)[0][0]


def numero_do_meio(valores):
    """A mediana. Menos sensível a valor extremo que a média."""
    valores = [v for v in valores if isinstance(v, (int, float)) and v > 0]
    if not valores:
        return None
    return int(statistics.median(valores))


def polegadas_para_cm(valor):
    return round(valor * 2.54) if valor else None


# =============================================================================
# 6. OS DOIS CAMPOS CALCULADOS
# =============================================================================
# Não existem no banco. São regras nossas, escritas aqui para poderem ser
# explicadas e conferidas.

def calcular_dificuldade(agua, ciclo, dias_ate_colher, altura_cm):
    """Cada condição vale 1 ponto: 0 = facil, 1 = media, 2 ou mais = dificil.

      + rega alta          -> exige constância, é o que mais mata planta
      + anual demorada     -> mais de 100 dias até colher
      + planta grande      -> acima de 3 m, pede espaço e poda

    Plantas perenes não são penalizadas pelo tempo até a primeira colheita:
    numa fruteira esse tempo é longo por natureza e não mede dificuldade.
    """
    pontos = 0
    if agua == "alta":
        pontos += 1
    if ciclo == "anual" and dias_ate_colher and dias_ate_colher > 100:
        pontos += 1
    if altura_cm and altura_cm > 300:
        pontos += 1

    if pontos == 0:
        return "facil"
    if pontos == 1:
        return "media"
    return "dificil"


def calcular_ambiente(categoria, luz, altura_cm, largura_cm):
    """Onde a planta cabe, calculado pelo tamanho dela.

    Valores possíveis: vaso, jardineira, varanda, horta-vertical, canteiro,
    interior.
    """
    altura = altura_cm or 100
    largura = largura_cm or 60

    # ornamental de sombra é planta de dentro de casa, não vai para canteiro
    if categoria == "ornamental" and luz in ("sombra", "meia-sombra"):
        return ["interior", "vaso"]

    if altura <= 60 and largura <= 50:
        lugares = ["vaso", "jardineira", "varanda"]
    elif altura <= 130:
        lugares = ["vaso", "canteiro"]
    else:
        lugares = ["canteiro"]

    # folhosa pequena também cabe em horta vertical
    if altura <= 40 and categoria in ("hortalica", "erva"):
        lugares.append("horta-vertical")

    return sorted(set(lugares))


# =============================================================================
# 7. LER O QUE JÁ FOI ESCRITO (para não apagar nada)
# =============================================================================

def ler_plantas_ja_existentes():
    """Devolve o que já está no Plantas.json, indexado por id."""
    if not ARQUIVO_SAIDA.exists():
        return {}
    try:
        conteudo = json.loads(ARQUIVO_SAIDA.read_text(encoding="utf-8"))
        lista = conteudo.get("plantas", [])
        return {planta["id"]: planta for planta in lista}
    except Exception as erro:
        print(f"  aviso: não consegui ler o {ARQUIVO_SAIDA.name} ({erro})")
        return {}


def primeiro_preenchido(*valores):
    """Devolve o primeiro valor que não está vazio."""
    for valor in valores:
        if valor:
            return valor
    return None


# =============================================================================
# 8. O PROGRAMA
# =============================================================================

def main():
    caminho_banco = achar_ou_baixar_banco()
    if caminho_banco is None:
        return

    registros = json.loads(caminho_banco.read_text(encoding="utf-8"))

    # agrupa as 21.926 linhas por espécie
    por_especie = defaultdict(list)
    for registro in registros:
        por_especie[so_o_nome_da_especie(registro.get("scientific_name"))].append(registro)

    ja_escrito = ler_plantas_ja_existentes()
    plantas = []
    nao_encontradas = []

    for nome_cientifico, (nome_portugues, categoria) in NOMES.items():
        variedades = por_especie.get(nome_cientifico)
        if not variedades:
            nao_encontradas.append(f"{nome_portugues} ({nome_cientifico})")
            continue

        planta_id = virar_id(nome_portugues)
        antes = ja_escrito.get(planta_id, {})       # o que já estava no arquivo
        exemplo = EXEMPLOS.get(planta_id, {})       # o modelo, se for uma das 5

        # --- resume as variedades numa ficha só ---
        luz = valor_mais_comum([LUZ.get(v.get("sun")) for v in variedades])
        agua = valor_mais_comum([AGUA.get(v.get("water")) for v in variedades])
        estacao = valor_mais_comum([v.get("season") for v in variedades])
        ciclo = "perene" if estacao == "perennial" else "anual"

        dias_ate_colher = numero_do_meio(
            [(v.get("days_to_maturity") or {}).get("min") for v in variedades])
        dias_para_germinar = numero_do_meio(
            [(v.get("days_to_germination") or {}).get("min") for v in variedades])
        altura = polegadas_para_cm(numero_do_meio(
            [(v.get("height_in") or {}).get("max") for v in variedades]))
        largura = polegadas_para_cm(numero_do_meio(
            [(v.get("spread_in") or {}).get("max") for v in variedades]))
        espacamento = polegadas_para_cm(numero_do_meio(
            [(v.get("spacing_in") or {}).get("min") for v in variedades]))

        plantas.append({
            "id": planta_id,
            "nomePopular": nome_portugues,
            "nomeCientifico": (variedades[0].get("scientific_name") or "").split("'")[0].strip(),
            "categoria": categoria,
            "familia": antes.get("familia", ""),
            "origem": antes.get("origem", ""),

            "cultivo": {
                "luz": luz,
                "rega": agua,
                "ciclo": ciclo,
                "dificuldade": calcular_dificuldade(agua, ciclo, dias_ate_colher, altura),
                "ambiente": calcular_ambiente(categoria, luz, altura, largura),
                "maturidadeDias": dias_ate_colher,
                "germinacaoDias": dias_para_germinar,
                "alturaCm": altura,
                "espacamentoCm": espacamento,
                "solo": (antes.get("cultivo") or {}).get("solo", ""),
            },

            # escrito por nós: o que já estava no arquivo vem primeiro
            "descricao": primeiro_preenchido(
                antes.get("descricao"), exemplo.get("descricao")) or "",
            "dicas": primeiro_preenchido(
                antes.get("dicas"), exemplo.get("dicas")) or [],
            "problemasComuns": primeiro_preenchido(
                antes.get("problemasComuns"), exemplo.get("problemasComuns")) or [],
            "imagem": primeiro_preenchido(
                antes.get("imagem"), exemplo.get("imagem")),

            "registrosAgregados": len(variedades),
            "fonte": {
                "referencia": "OpenPlantDB",
                "url": "https://github.com/cwfrazier1/openplantdb",
                "licenca": "CC0 1.0 (domínio público)",
                "dataConsulta": date.today().isoformat(),
            },
        })

    # planta que saiu da curadoria mas está no arquivo: fica, não some
    ids_gerados = {p["id"] for p in plantas}
    herdadas = [p for pid, p in ja_escrito.items() if pid not in ids_gerados]
    plantas.extend(herdadas)
    plantas.sort(key=lambda p: p.get("nomePopular", ""))

    arquivo = {
        "meta": {
            "projeto": "Cultiva.me",
            "geradoEm": date.today().isoformat(),
            "totalPlantas": len(plantas),
            "fonte": {
                "nome": "OpenPlantDB",
                "url": "https://github.com/cwfrazier1/openplantdb",
                "licenca": "CC0 1.0 (domínio público)",
            },
            "camposDoBanco": ["luz", "rega", "ciclo", "maturidadeDias",
                              "germinacaoDias", "alturaCm", "espacamentoCm"],
            "camposCalculados": {
                "dificuldade": "a partir da rega, do ciclo e da altura",
                "ambiente": "a partir da altura e da largura da planta",
            },
            "camposEscritosPorNos": ["descricao", "dicas", "problemasComuns",
                                     "imagem", "familia", "origem", "solo"],
            "notaMaturidade": ("maturidadeDias é o tempo até a primeira colheita "
                               "nas comestíveis e até a primeira floração nas "
                               "ornamentais."),
            "ressalva": ("O OpenPlantDB é norte-americano. Os valores são faixas "
                         "publicadas e variam com a variedade, a região e o "
                         "microclima."),
        },
        "plantas": plantas,
    }

    ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO_SAIDA.write_text(
        json.dumps(arquivo, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- relatório ---
    print(f"{len(plantas)} plantas -> {ARQUIVO_SAIDA}")
    for categoria, quantas in Counter(p["categoria"] for p in plantas).most_common():
        print(f"  {categoria:12} {quantas:3}")

    com_texto = sum(1 for p in plantas if p.get("descricao"))
    print(f"\n  com descrição escrita: {com_texto} de {len(plantas)}")
    if herdadas:
        print(f"  mantidas do arquivo anterior: {len(herdadas)}")
    if nao_encontradas:
        print("\n  sem correspondência no banco:")
        for nome in nao_encontradas:
            print(f"    - {nome}")


if __name__ == "__main__":
    main()