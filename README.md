# Dashboard de Produtividade Logística

## Como rodar

1. Instale as dependências:
   pip install -r requirements.txt

2. Rode o app:
   streamlit run dashboard_produtividade.py

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
