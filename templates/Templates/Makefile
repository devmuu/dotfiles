# ==============================================================================
# Program:          Makefile
# Description:      Compilando modelo LaTeX
# Software/Tool:    TeX Live 2026
# ==============================================================================

# Arquivo principal.
FILENAME = main
# Compilador.
ENGINE = lualatex
# Ferramenta para bibliografia.
BIB = biber

# Extensões dos arquivos auxiliares.
AUX_FILES := *.acn *.acr *.alg *.aux *.bbl* *.bcf* *.blg *.brf *.dvi *.fls *.fdb_*
AUX_FILES += *.glg *.glo *.gls *.glsdefs *.idx *.ilg *.ind *.ist *.loa *.loalg
AUX_FILES += *.locf *.lof *.log *.lol *.lop *.loq *.lot *.lsg *.maf *.mtc*
AUX_FILES += *.nav *.nlo *.nls *.not *.ntn *.out *.snm *.soc *.spl *.tdo
AUX_FILES += *.toc *.tuc *.vrb *.xdy *.xml *.xwm *~

# Alvo padrão.
all: compile clean

# compila arquivo principal com pdflatex sem referências.
compile:
	@echo "Compilando..."
	$(ENGINE) -draftmode -interaction=nonstopmode -halt-on-error -file-line-error $(FILENAME).tex
	$(ENGINE) -interaction=batchmode $(FILENAME).tex
	@echo "Documento gerado com sucesso!"

# compila arquivo principal com pdflatex e biber.
biber:
	$(ENGINE) -draftmode -interaction=nonstopmode -file-line-error $(FILENAME).tex
	${BIB} $(FILENAME)
	$(ENGINE) -draftmode -interaction=batchmode $(FILENAME).tex
	$(ENGINE) $(FILENAME).tex
	@rm -f $(AUX_FILES)
	@echo "Documento gerado com sucesso!"

check: clean
	@echo "Compilando (modo diagnóstico)..."
	@texfot latexmk \
		-pdf \
		-pdflatex="$(ENGINE) %O %S" \
		-file-line-error \
		-interaction=nonstopmode \
		$(FILENAME).tex
	@echo "Verificação concluída!"

lint:
	@echo "Analisando o projeto..."
	@texfot $(ENGINE) \
		-draftmode \
		-interaction=nonstopmode \
		-file-line-error \
		$(FILENAME).tex

# Compila o arquivo principal com pdflatex e bibtex gerando o arquivo
# synctex para utilização em leitores de pdf compatíveis
synctex:
	$(ENGINE) -draftmode -interaction=nonstopmode -file-line-error $(FILENAME).tex
	# ${BIB} $(FILENAME)
	$(ENGINE) -draftmode -interaction=batchmode $(FILENAME).tex
	$(ENGINE) -synctex=15 -interaction=batchmode $(FILENAME).tex
	@echo "Processo finalizado com sucesso!"
	@echo "Arquivos synctex gerados."

# Limpa arquivos auxiliares.
clean:
	@echo -n "Limpando arquivos auxiliares..."
	@rm -f $(AUX_FILES)
	@echo "Limpeza concluída!"

