# inPeDF

[Português](#português) · [English](#english)

## Português

Leitor de PDFs para Linux, desenvolvido em Python com GTK 4, Libadwaita e Poppler. O inPeDF oferece leitura contínua por padrão e controles para navegar, pesquisar e apresentar documentos.

### Recursos

- Visualização contínua ou de página única, com zoom e ajuste à largura ou à página.
- Restauração da última página e do zoom de cada documento.
- Barra lateral com miniaturas clicáveis, sumário navegável e consulta de anotações incorporadas.
- Busca de texto com destaque, navegação entre resultados e cancelamento.
- Seleção e cópia de texto, com rolagem automática durante o arraste.
- Links internos e externos clicáveis.
- Histórico para voltar e avançar entre pontos de leitura.
- Rotação da visualização em incrementos de 90°.
- Abertura de PDFs protegidos por senha.
- Impressão pela janela do sistema.
- Apresentação em tela cheia, com tela de encerramento.
- Propriedades do documento, incluindo metadados, tamanho e permissões.
- Lista de arquivos recentes, preferências e interface traduzível.
- Abertura por caminho ou URI, inclusive quando o aplicativo já está em execução.

### Como executar

Requisitos principais: Python 3, GTK 4.10 ou superior, Libadwaita 1.5 ou superior, Poppler, PyGObject e Pycairo.

Em um Ubuntu com essas versões disponíveis, instale as dependências e as ferramentas para compilar as preferências e traduções.

```bash
sudo apt-get update
sudo apt-get install git python3 python3-gi python3-cairo python3-gi-cairo \
  gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-poppler-0.18 libglib2.0-bin gettext
```

Obtenha o código e prepare os arquivos usados pela aplicação.

```bash
git clone https://github.com/hederdorneles/inPeDF.git
cd inPeDF
glib-compile-schemas data
mkdir -p locale/pt_BR/LC_MESSAGES
msgfmt po/pt_BR.po -o locale/pt_BR/LC_MESSAGES/inpedf.mo
python3 main.py
```

Para abrir um PDF diretamente, informe o caminho entre aspas quando contiver espaços.

```bash
python3 main.py "/caminho/meu documento.pdf"
```

### Atalhos

| Atalho | Ação |
| --- | --- |
| Ctrl+O | Abrir PDF |
| Ctrl+F | Buscar texto |
| Ctrl+C | Copiar seleção |
| Ctrl+P | Imprimir |
| Setas | Rolar a visualização |
| Page Up / Page Down | Página anterior / seguinte |
| Home / End | Primeira / última página |
| Alt+← / Alt+→ | Voltar / avançar no histórico |
| Ctrl+[ / Ctrl+] | Girar à esquerda / direita |
| Alt+Enter | Propriedades do documento |
| F5 | Apresentar desde a primeira página |
| Shift+F5 | Apresentar desde a página atual |
| Esc | Sair da apresentação ou limpar a seleção |
| Ctrl+? | Consultar atalhos de teclado |
| Ctrl+Q | Sair do aplicativo |

Na apresentação, use as setas, Espaço, Backspace ou Page Up / Page Down para navegar. Depois da última página, uma tela preta indica o fim. Clique ou avance novamente para sair, ou volte para rever a última página.

### Licença

Copyright © 2026 Heder Dorneles Soares. Distribuído sob a [GNU GPL versão 2, exclusivamente](LICENSE).

## English

A PDF reader for Linux, built with Python, GTK 4, Libadwaita and Poppler. inPeDF opens documents in continuous view by default and provides controls for navigation, search and presentations.

### Features

- Continuous and single-page layouts, with zoom, fit-to-width and fit-to-page controls.
- Restoration of each document’s last page and zoom level.
- Sidebar with clickable thumbnails, a navigable outline and embedded annotation viewing.
- Text search with highlighting, result navigation and cancellation.
- Text selection and copying, with automatic scrolling while dragging.
- Clickable internal and external links.
- Back and forward history between reading positions.
- View rotation in 90° increments.
- Password-protected PDF opening.
- Printing through the system dialog.
- Fullscreen presentations with an end-of-presentation screen.
- Document properties, including metadata, size and permissions.
- Recent files, preferences and a translatable interface.
- Opening by file path or URI, including when the application is already running.

### Running from source

Main requirements: Python 3, GTK 4.10 or later, Libadwaita 1.5 or later, Poppler, PyGObject and Pycairo.

On an Ubuntu installation providing these versions, install the dependencies and tools for compiling settings and translations.

```bash
sudo apt-get update
sudo apt-get install git python3 python3-gi python3-cairo python3-gi-cairo \
  gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-poppler-0.18 libglib2.0-bin gettext
```

Get the source and prepare the application files.

```bash
git clone https://github.com/hederdorneles/inPeDF.git
cd inPeDF
glib-compile-schemas data
mkdir -p locale/pt_BR/LC_MESSAGES
msgfmt po/pt_BR.po -o locale/pt_BR/LC_MESSAGES/inpedf.mo
python3 main.py
```

To open a PDF directly, pass its path, using quotes if it contains spaces.

```bash
python3 main.py "/path/my document.pdf"
```

### Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| Ctrl+O | Open a PDF |
| Ctrl+F | Find text |
| Ctrl+C | Copy selection |
| Ctrl+P | Print |
| Arrow keys | Scroll the view |
| Page Up / Page Down | Previous / next page |
| Home / End | First / last page |
| Alt+← / Alt+→ | Back / forward in history |
| Ctrl+[ / Ctrl+] | Rotate left / right |
| Alt+Enter | Document properties |
| F5 | Present from the first page |
| Shift+F5 | Present from the current page |
| Esc | Leave the presentation or clear the selection |
| Ctrl+? | Show keyboard shortcuts |
| Ctrl+Q | Quit the application |

During presentations, use the arrow keys, Space, Backspace or Page Up / Page Down to navigate. A black screen appears after the last page. Click or advance again to exit, or go back to revisit the last page.

### License

Copyright © 2026 Heder Dorneles Soares. Distributed under the [GNU GPL version 2 only](LICENSE).
