# Dashboard de Produtividade Logística

## Como rodar

1. Instale as dependências:
   pip install -r requirements.txt

2. Rode o app:
   streamlit run dashboard_produtividade (1).py

3. O navegador abrirá automaticamente em http://localhost:8501

## Fonte de dados

Por padrão, o app lê uma planilha pública do Google Sheets (aba "Página1").
Você pode trocar o link na barra lateral, em "🔗 Fonte de Dados".
A planilha precisa estar com permissão de compartilhamento "Qualquer pessoa com o link pode visualizar".

Colunas esperadas (o app detecta variações no nome automaticamente):
- Nome
- tipo Tarefa (deve conter "SEPARA" para picking ou "CONF" para conferência)
- Qt Produtos
- Unidades
- Peso
- Volume
- Duração (formato HH:MM ou HH:MM:SS)
- Data
- Rua (opcional)

## Filtros salvos automaticamente

O app grava o período selecionado, as exclusões de colaboradores (por ambiente)
e as metas manuais de UPH/PPH em um arquivo local (`filtros_salvos.json`),
gerado automaticamente na mesma pasta do app. Assim, da próxima vez que
alguém abrir o app, os filtros já vêm preenchidos como estavam.

Use o botão **"🗑️ Limpar Filtros Salvos"** na barra lateral para apagar os
filtros salvos e voltar aos padrões (período completo e metas sugeridas
automaticamente).

**Importante:** esse salvamento é feito em um arquivo no servidor onde o
app está rodando, não no navegador do usuário. Ou seja, os filtros ficam
compartilhados entre todas as pessoas que acessam o mesmo link do app —
não é uma preferência individual por usuário. Além disso, no Streamlit
Community Cloud, se o app for reiniciado ou redeployado (por exemplo, após
uma atualização de código), esse arquivo pode ser perdido, pois o
armazenamento em disco lá é temporário.
