# Libraries imports
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd

# Model imports
from camada_model.ctrl_fluxo import CtrlFluxo
from camada_model.ctrl_info_loader import CtrlInfoLoader
from camada_model.ctrl_atributos_cidade import CtrlAtributosCidade


# Visualizações imports
import visualizacao.vis_mapa as vis
import visualizacao.vis_mapa_2 as vis_2

# Carregando Model classes
ctrlFluxo = CtrlFluxo()
ctrlInfoLoader = CtrlInfoLoader()
ctrlAtrCidade = CtrlAtributosCidade()

# Carregando dados iniciais
dicEstados = ctrlInfoLoader.dfEstados.to_dict('records')
dicCidades = ctrlInfoLoader.carregarCidadesPorEstado(dicEstados[0]['cod_uf']).to_dict('records')

#Variáveis de estado
tabSelecionada = "fluxo_geral"

# Inicializando aplicacao
app = Dash(__name__)


##############################################
#######    Componetes do Layout     ##########
##############################################

#Componente RadioButtons do tipos de Fluxo
radioBtnFluxoTrans = dcc.RadioItems(
        options={
        'fluxo_geral': 'Fluxo Rodoviário + Aéreo',
        'fluxo_aereo': 'Fluxo Aéreo',
        'fluxo_rodo': 'Fluxo Rodoviário'
        },
        value='fluxo_geral', id='radio-fluxo')

radioBtnFluxoSaude = dcc.RadioItems(
        options={
        'saude_alta': 'Alta complexidade',
        'saude_baixa_media': 'Baixa e média complexidade',
        },
        value='saude_alta', id='radio-fluxo')

#Dropdown com atributos variados
dropdownAtributos = dcc.Dropdown(
                options=[
                {"label":"PIB", "value":"pib"},
                {"label":"Densidade populacional", "value":"densidade_2021"},
                {"label":"Hierarquia", "value":"hierarquia"},
                {"label":"Índice de atração", "value":"indice_atracao"}, 
                {"label":"IA saúde Baixa/Média", "value":"ia_saude_bm"},
                {"label":"IA saúde Alta", "value":"ia_saude_a"},
                {"label":"IA aeroportos", "value":"ia_aeroporto"},
                {"label":"IA transportes", "value":"ia_transporte"},
                {"label":"Leitos/mil hab.", "value":"num_leitos"}
                ],
                id='dropdown-atributos',
                multi=True
            )

#Componente do drop de Estados
dropDownsFluxo= html.Div([
        # Dropdown-Estado
        html.Div([
            dcc.Dropdown(
                options=[{'label': i['nome_uf'], 'value': i['cod_uf']}
                        for i in dicEstados],
                value=dicEstados[0]['cod_uf'],
                id='dropdown-estado'   
            )
        ], className="menu__dropdown"),

         # Dropdown-Analise
        html.Div([
            dcc.Dropdown(
                options=[
                {"label":"Cidade", "value":"cidade"},
                {"label":"Região de Saúde", "value":"regiao"}
                ],
                value="cidade",
                id='dropdown-analise'
            )
        ], className="menu__dropdown"),

        # Dropdown-Dinâmico
        html.Div(
        id="div-dropdown-dinamico", className="menu__dropdown")
], id='menu')

#Componente que contem a visualização do mapa
containerMapa = dcc.Graph(id='visualizacao')
containerMapa_2 = dcc.Graph(id='visualizacao_2')

#TODO: Remover após testes
containerDf = html.Div(id='my-output')
containerDf_2 = html.Div(id='my-output-2')

#Componente da tab de Fluxo Transporte
tabFluxoTransporte = html.Div([
        dropDownsFluxo,
        dropdownAtributos,  
        radioBtnFluxoTrans, 
        containerMapa,
        containerDf
])

#Componente da tab de Fluxo Saude
tabFluxoSaude = html.Div([
        dropDownsFluxo,
        dropdownAtributos, 
        radioBtnFluxoSaude, 
        containerMapa,
        containerDf
])

#Componente da tab de Atributos 
tabAtributos = html.Div([
        dropdownAtributos, 
        containerMapa_2,
        containerDf_2
])


##############################################
#######     Application Layout      ##########
##############################################

app.layout = html.Div(children=[
    #Título da aplicacao
    html.H1(children='Alerta Epidemia'),

    #Tabs da aplicação 
    dcc.Tabs(id="tabs-vis", value='tab-fluxo-transporte', children=[
        dcc.Tab(label='Fluxo de transporte', value='tab-fluxo-transporte'),
        dcc.Tab(label='Fluxo serviços de saúde', value='tab-fluxo-saude'),
        dcc.Tab(label='Atributos gerais', value='tab-atributos')
    ]),

    #Container das tabs da aplicação
    html.Div(id='tabs-content')
]
)


#TODO: Remover essa funcao depois, isso eh so para TESTES
def generate_table(dataframe, max_rows=10):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])


##############################################
############     Callbacks      ##############
##############################################

############     Callbacks: Geral      ##############

# Callback - Carregar conteúdo de cada tab
@app.callback(Output('tabs-content', 'children'),
              Input('tabs-vis', 'value'))
def render_content(tab):
    global tabSelecionada
    tabSelecionada = tab
    
    if(tab == "tab-fluxo-transporte"):
        return tabFluxoTransporte
    elif(tab == "tab-fluxo-saude"):
        return tabFluxoSaude    
    elif(tab == "tab-atributos"):
        return tabAtributos  

############     Callbacks: Tab Fluxo de Transporte + Tab Saúde     ##############

# Callback - Update dropdown dinamico
@app.callback(
    Output('div-dropdown-dinamico', 'children'),
    Input('dropdown-estado', 'value'), 
    Input('dropdown-analise', 'value'))
def updateDropdownCidade(idEstado, tipoDropdown):
    if tipoDropdown == "cidade":
        return carregarDropdownCidades(idEstado)
    elif tipoDropdown == "regiao":
        return carregarDropdownRegiao(idEstado)

#Funcao de apoio de carregamento de dropdown
def carregarDropdownCidades(idEstado):
    dicCidades = ctrlInfoLoader.carregarCidadesPorEstado(idEstado).to_dict('records')
    return dcc.Dropdown(
        options=[{'label': i['nome_mun'], 'value': i['cod_mun']} for i in dicCidades],
        value=dicCidades[0]['cod_mun'],
        id='dropdown-cidade'
    )

#Funcao de apoio de carregamento de dropdown
def carregarDropdownRegiao(idEstado):
    dicRegiao = ctrlInfoLoader.carregarRegioesPorEstado(idEstado).to_dict('records')
    return  dcc.Dropdown(
        options=[{'label': i['nome_reg_saude'], 'value': i['cod_reg_saude']} for i in dicRegiao],
        value=dicRegiao[0]['cod_reg_saude'],
        id='dropdown-regiao'
    )


# Callback - Renderiza fluxo de transporte da cidade
@app.callback(
    Output('visualizacao', 'figure'),
    Input('dropdown-cidade', 'value'),
    Input('radio-fluxo', 'value')
    # Input('radio-fluxo-saude', 'value') 
    )
def updateFluxoCidade(idCidade, tipoFluxo):
    print(tipoFluxo)
    #Funcao com as infos da cidade de origem 
    infoCidade, dfFluxo = ctrlFluxo.percentualFluxo(idCidade, tipoFluxo)
    return vis.carregarMapa(dfFluxo)


############     Callbacks: Tab Atributos     ##############

# Callback - Renderiza diversos atributos da cidade
@app.callback(
    Output('visualizacao_2', 'figure'),
    Input(tabAtributos, 'children'))
def updateAtributosCidades(tabvalue):
    #Funcao com as infos da cidade de origem 
    atributoCidade = ctrlAtrCidade.carregarTodasCidades()
    df_filtrado = atributoCidade[atributoCidade['indice_atracao'].notna()]
    return vis_2.carregarMapa(df_filtrado)



############     Callbacks: Testes --> REMOVER DEPOIS     ##############
#TODO: Remover depois dos testes --> Callback print Dataframe
#Callback - Seleção de Fluxo - Rodoviário/Aéreo
@app.callback(
    Output('my-output', 'children'),
    Input('dropdown-cidade', 'value'),
    Input('radio-fluxo', 'value'))
def updateRecomendacaoCidade(idCidade, tipoFluxo):
    print(tipoFluxo)

    infoCidade, dfFluxo = ctrlFluxo.percentualFluxo(idCidade, tipoFluxo)
    return generate_table(dfFluxo)

#TODO: Remover depois dos testes --> Callback print Dataframe
@app.callback(
    Output('my-output-2', 'children'),
    Input(tabAtributos, 'children'))
def updateAtributosCidades(tabvalue):
    #Funcao com as infos da cidade de origem 
    atributoCidade = ctrlAtrCidade.carregarTodasCidades()
    df_filtrado = atributoCidade[atributoCidade['rede_sentinela'].notna()]
    print(df_filtrado['rede_sentinela'].apply(type))
    return generate_table(df_filtrado)


# def updateupdateAtributosCidades(idCidade):
#     dfAtributosCidades = ctrlAtrCidade.carregarTodasCidades()
#     return generate_table(dfAtributosCidades)    

if __name__ == '__main__':
    app.run_server(debug=True)
