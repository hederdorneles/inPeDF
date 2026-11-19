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
- Comandos no menu para copiar o caminho do documento e abrir sua pasta.
- Marcadores pessoais por documento, com acesso pelo botão Marcadores na barra inferior.
- Abertura de um PDF ao arrastar e soltar o arquivo sobre a janela.
- Lista de arquivos recentes, preferências e interface traduzível, com suporte a créditos de tradutores.
- Abertura por caminho ou URI, inclusive quando o aplicativo já está em execução.

### Instalação pelo PPA (Ubuntu 24.04)

Adicione o PPA e instale o inPeDF pelo gerenciador de pacotes.

```bash
sudo add-apt-repository ppa:heder-to/inpedf
sudo apt update
sudo apt install inpedf
```

Depois, abra pelo menu de aplicativos ou execute **inpedf** no terminal. As atualizações publicadas no PPA chegam pelo gerenciador de atualizações do Ubuntu.

### Executar pelo código-fonte

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

### Exportação para IA

Consulte a ajuda geral ou todas as opções de exportação sem abrir a interface gráfica.

~~~bash
python3 main.py --help
python3 main.py --usage
python3 main.py --version
python3 main.py export --help
~~~

No menu **Exportar…**, escolha Markdown, TXT ou JSON, o documento inteiro, a página atual ou um intervalo e a pasta de destino. A exportação mostra o progresso e permite cancelar.

Também é possível converter vários PDFs pelo terminal, sem sessão gráfica.

~~~bash
python3 main.py export ./documentos/*.pdf --format md,txt,json --output-dir ./convertidos --jobs 4 --report ./relatorio.json
~~~

Com o aplicativo instalado, use **inpedf export** no lugar de **python3 main.py export**.

- **--pages 1,3-5** escolhe páginas, numeradas a partir de 1.
- **--jobs** limita os PDFs simultâneos. O padrão é 2.
- **--quiet** mostra apenas erros. **--verbose** inclui opções de conversão, processos e arquivos gerados. Escolha uma das opções.
- **--overwrite** permite substituir arquivos. Por padrão, arquivos existentes são preservados.
- **--password-file caminho** lê de um arquivo UTF-8 uma senha comum aos PDFs protegidos.
- **--report caminho.json** grava os resultados por arquivo, incluindo falhas e páginas sem texto.
- **Ctrl+C** cancela as tarefas ativas e limpa as saídas incompletas. Os arquivos já concluídos são preservados.

A conversão continua quando um arquivo falha. PDFs de pastas diferentes com o mesmo nome recebem um sufixo para distinguir as saídas. Os códigos de saída são 0 para sucesso, 1 para falha de conversão ou gravação, 2 para opções inválidas e 130 para cancelamento.

O Markdown contém texto literal separado por páginas. O JSON inclui metadados, número e dimensões de cada página e o texto extraído. A ordem de leitura depende do texto disponível no PDF. OCR, reconstrução de títulos, tabelas, fórmulas e descrição de imagens ficam para uma etapa posterior. Páginas sem texto extraível geram um aviso.

Ao executar o comando instalado **inpedf**, a janela abre em segundo plano e libera o terminal. Mensagens de diagnóstico ficam em **$XDG_STATE_HOME/inpedf/inpedf.log**, ou **~/.local/state/inpedf/inpedf.log** por padrão. A exportação e os comandos de ajuda continuam em primeiro plano. A execução direta com **python3 main.py** também abre a interface em segundo plano e libera o terminal.

### Atalhos

| Atalho | Ação |
| --- | --- |
| Ctrl+O | Abrir PDF |
| Ctrl+F | Buscar texto |
| Ctrl+C | Copiar seleção |
| Ctrl+P | Imprimir |
| Ctrl+0 | Zoom de 100% |
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
- Menu commands to copy the document path and open its containing folder.
- Personal bookmarks per document, accessible through the Bookmarks button in the bottom bar.
- Opening a PDF by dragging and dropping a file onto the window.
- Recent files, preferences and a translatable interface with translator credit support.
- Opening by file path or URI, including when the application is already running.

### Install from the PPA (Ubuntu 24.04)

Add the PPA and install inPeDF using the package manager.

```bash
sudo add-apt-repository ppa:heder-to/inpedf
sudo apt update
sudo apt install inpedf
```

Then open it from the application menu or run **inpedf** in a terminal. Updates published in the PPA are delivered through Ubuntu's update manager.

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

### Exporting for AI

View general help or all export options without opening the graphical interface.

~~~bash
python3 main.py --help
python3 main.py --usage
python3 main.py --version
python3 main.py export --help
~~~

Use **Export…** in the menu to select Markdown, TXT or JSON, all pages, the current page or a range, and an output folder. Export includes progress and cancellation.

Batch conversion also works from the terminal without a graphical session.

~~~bash
python3 main.py export ./documents/*.pdf --format md,txt,json --output-dir ./converted --jobs 4 --report ./report.json
~~~

With the application installed, use **inpedf export** instead of **python3 main.py export**.

- **--pages 1,3-5** selects pages using 1-based numbering.
- **--jobs** limits concurrent PDFs. The default is 2.
- **--quiet** shows errors only. **--verbose** adds conversion settings, worker IDs and generated files. Choose one of these options.
- **--overwrite** allows replacing files. Existing files are preserved by default.
- **--password-file path** reads a password shared by encrypted PDFs from a UTF-8 file.
- **--report path.json** records per-file results, including failures and pages without text.
- **Ctrl+C** cancels active tasks and cleans up incomplete outputs. Completed files are preserved.

Conversion continues when a file fails. Same-named PDFs from different folders receive a suffix to distinguish their outputs. Exit codes are 0 for success, 1 for conversion or write failures, 2 for invalid options and 130 for cancellation.

Markdown contains literal text separated by page headings. JSON includes metadata, each page's number and dimensions, and extracted text. Reading order depends on the PDF's available text. OCR, heading reconstruction, tables, formulas and image descriptions are planned for a later stage. Pages without extractable text produce a warning.

The installed **inpedf** command opens the window in the background and releases the terminal. Diagnostic messages are written to **$XDG_STATE_HOME/inpedf/inpedf.log**, or **~/.local/state/inpedf/inpedf.log** by default. Export and help commands run in the foreground. Running **python3 main.py** directly also opens the interface in the background and releases the terminal.

### Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| Ctrl+O | Open a PDF |
| Ctrl+F | Find text |
| Ctrl+C | Copy selection |
| Ctrl+P | Print |
| Ctrl+0 | Zoom 100% |
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
