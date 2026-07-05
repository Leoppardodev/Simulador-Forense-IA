import sys
import os
import json
import requests
from google import genai
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QComboBox, QTextBrowser, QRadioButton, 
                             QButtonGroup, QMessageBox, QLabel, QHBoxLayout, 
                             QSizePolicy, QLineEdit, QGroupBox, QGridLayout, 
                             QFrame, QStackedWidget, QDialog)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QFont, QPixmap

# ====================================================================
# FUNÇÃO PARA ENCONTRAR ARQUIVOS (Imagens e Assets)
# ====================================================================
def resolver_caminho(nome_arquivo):
    if getattr(sys, 'frozen', False):
        diretorio = os.path.dirname(sys.executable)
    else:
        diretorio = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(diretorio, nome_arquivo)

# ====================================================================
# CLASSES DE INTERFACE CUSTOMIZADAS
# ====================================================================
class ClickableLabel(QLabel):
    def __init__(self, radio_button, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.radio_button = radio_button
        self.setWordWrap(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    def mousePressEvent(self, event):
        self.radio_button.setChecked(True)

class JanelaExplicacao(QDialog):
    def __init__(self, parent=None, html_content=""):
        super().__init__(parent)
        self.setWindowTitle("Parecer Técnico da Banca")
        self.setMinimumSize(750, 500) 
        
        if parent:
            self.setStyleSheet(parent.styleSheet())
            
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        self.text_browser = QTextBrowser()
        self.text_browser.setObjectName("Explicacao")
        self.text_browser.setHtml(html_content)
        self.text_browser.setOpenExternalLinks(True)
        layout.addWidget(self.text_browser)
        
        self.btn_fechar = QPushButton("Fechar Análise")
        self.btn_fechar.setObjectName("BtnSecundario")
        self.btn_fechar.setMinimumHeight(45)
        self.btn_fechar.clicked.connect(self.accept)
        layout.addWidget(self.btn_fechar)

# ====================================================================
# APLICAÇÃO PRINCIPAL - PERITO CRIMINAL
# ====================================================================
class GeradorQuestoesApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulador Forense - Perito Criminal PCPE/PCPB")
        self.setMinimumSize(1050, 750)
        
        self.settings = QSettings("LeonardoAguiar", "SimuladorPeritoMVP")
        self.questao_atual = None
        
        self.initUI()
        self.aplicar_tema_moderno()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --------------------------------------------------------------------
        # 1. BARRA LATERAL (SIDEBAR)
        # --------------------------------------------------------------------
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(15)

        lbl_titulo_app = QLabel("🔬 Pol. Científica<br><span style='font-size: 11px; color: #ef4444;'>Perito Criminal</span>")
        lbl_titulo_app.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        sidebar_layout.addWidget(lbl_titulo_app)
        sidebar_layout.addSpacing(30)

        self.btn_nav_dashboard = QPushButton("🏠 QG do Concurseiro")
        self.btn_nav_dashboard.setObjectName("NavBtnActive")
        self.btn_nav_dashboard.clicked.connect(lambda: self.mudar_pagina(0))
        sidebar_layout.addWidget(self.btn_nav_dashboard)

        self.btn_nav_config = QPushButton("⚙️ Configurações (API)")
        self.btn_nav_config.setObjectName("NavBtn")
        self.btn_nav_config.clicked.connect(lambda: self.mudar_pagina(1))
        sidebar_layout.addWidget(self.btn_nav_config)

        sidebar_layout.addStretch()

        logos_layout = QHBoxLayout()
        lbl_logo_pcpe = QLabel()
        caminho_pcpe = resolver_caminho("logo_pcpe.png")
        if os.path.exists(caminho_pcpe):
            lbl_logo_pcpe.setPixmap(QPixmap(caminho_pcpe).scaled(45, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            lbl_logo_pcpe.setText("🛡️ PCPE")
            lbl_logo_pcpe.setStyleSheet("color: #475569; font-weight: bold;")
        
        lbl_logo_pcpb = QLabel()
        caminho_pcpb = resolver_caminho("logo_pcpb.png")
        if os.path.exists(caminho_pcpb):
            lbl_logo_pcpb.setPixmap(QPixmap(caminho_pcpb).scaled(45, 45, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            lbl_logo_pcpb.setText("🛡️ PCPB")
            lbl_logo_pcpb.setStyleSheet("color: #475569; font-weight: bold;")
            
        logos_layout.addWidget(lbl_logo_pcpe)
        logos_layout.addWidget(lbl_logo_pcpb)
        sidebar_layout.addLayout(logos_layout)
        
        lbl_user = QLabel("👤 Investigador\nPlano Básico")
        lbl_user.setStyleSheet("color: #94a3b8; font-size: 11px;")
        sidebar_layout.addWidget(lbl_user)

        main_layout.addWidget(sidebar)

        # --------------------------------------------------------------------
        # 2. ÁREA CENTRAL (QStackedWidget)
        # --------------------------------------------------------------------
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("Conteudo")
        main_layout.addWidget(self.stacked_widget)

        # PÁGINA 0: DASHBOARD (Gerador)
        page_dashboard = QWidget()
        conteudo_layout = QVBoxLayout(page_dashboard)
        conteudo_layout.setContentsMargins(40, 30, 40, 20)
        conteudo_layout.setSpacing(20)

        header_layout = QHBoxLayout()
        header_text = QLabel("<h2>Gerar Nova Questão de Perícia</h2><p style='color: #94a3b8;'>Foco na doutrina e jurisprudência aplicadas ao local de crime.</p>")
        header_layout.addWidget(header_text)
        self.lbl_status_api = QLabel("")
        self.lbl_status_api.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic;")
        header_layout.addWidget(self.lbl_status_api, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        conteudo_layout.addLayout(header_layout)

        controles_frame = QFrame()
        controles_frame.setObjectName("Card")
        controles_layout = QVBoxLayout(controles_frame)
        filtros_layout = QHBoxLayout()
        
        filtros_layout.addWidget(QLabel("Banca Exame:"))
        self.combo_banca = QComboBox()
        self.combo_banca.addItems(["Cebraspe (Múltipla Escolha)", "Instituto AOCP", "FGV", "IBFC"])
        filtros_layout.addWidget(self.combo_banca)

        filtros_layout.addWidget(QLabel("Disciplina Especializada:"))
        self.combo_disciplina = QComboBox()
        self.combo_disciplina.addItems([
            "Criminalística (Cadeia de Custódia e Vestígios)", 
            "Medicina Legal (Traumatologia e Tanatologia)",
            "Direito Processual Penal (Provas e Inquérito)", 
            "Direito Penal", 
            "Língua Portuguesa"
        ])
        filtros_layout.addWidget(self.combo_disciplina)

        self.btn_gerar = QPushButton("✨ Gerar Questão")
        self.btn_gerar.setObjectName("BtnGerarPrimario")
        self.btn_gerar.setMinimumHeight(45)
        self.btn_gerar.clicked.connect(self.gerar_questao)
        filtros_layout.addWidget(self.btn_gerar)
        
        controles_layout.addLayout(filtros_layout)
        conteudo_layout.addWidget(controles_frame)

        questao_frame = QFrame()
        questao_frame.setObjectName("Card")
        questao_layout = QVBoxLayout(questao_frame)

        self.display_enunciado = QTextBrowser()
        self.display_enunciado.setObjectName("Enunciado")
        self.display_enunciado.setFont(QFont("Segoe UI", 12))
        self.display_enunciado.setText("Aguardando solicitação para gerar a situação hipotética...")
        questao_layout.addWidget(self.display_enunciado)

        self.grupo_alternativas = QButtonGroup(self)
        self.layout_alternativas = QVBoxLayout()
        self.alternativas_ui = []
        
        for i in range(5):
            container = QFrame()
            container.setObjectName("AlternativaContainer")
            h_layout = QHBoxLayout(container)
            h_layout.setContentsMargins(15, 10, 15, 10)
            rb = QRadioButton()
            rb.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed) 
            lbl = ClickableLabel(rb)
            lbl.setFont(QFont("Segoe UI", 11))
            h_layout.addWidget(rb, alignment=Qt.AlignmentFlag.AlignTop)
            h_layout.addWidget(lbl)
            self.grupo_alternativas.addButton(rb, i)
            self.layout_alternativas.addWidget(container)
            container.hide()
            self.alternativas_ui.append({'radio': rb, 'label': lbl, 'container': container})
            
        questao_layout.addLayout(self.layout_alternativas)

        self.btn_responder = QPushButton("Verificar Parecer Técnico")
        self.btn_responder.setObjectName("BtnSecundario")
        self.btn_responder.setMinimumHeight(40)
        self.btn_responder.clicked.connect(self.verificar_resposta)
        self.btn_responder.hide()
        questao_layout.addWidget(self.btn_responder)

        conteudo_layout.addWidget(questao_frame)
        conteudo_layout.addStretch()

        # Rodapé (Doações e Créditos)
        footer_layout = QHBoxLayout()
        lbl_creditos = QLabel("Desenvolvido por <b>Leonardo Aguiar</b> | Versão 1.0 MVP (Perícia)")
        lbl_creditos.setStyleSheet("color: #64748b; font-size: 11px;")
        footer_layout.addWidget(lbl_creditos, alignment=Qt.AlignmentFlag.AlignLeft)
        
        lbl_doacao = QLabel("<a href='https://link.mercadopago.com.br/geradordequestoesbb' style='color: #009ee3; text-decoration: none;'>🤝 Apoie este projeto (Doar via Mercado Pago)</a>")
        lbl_doacao.setOpenExternalLinks(True)
        lbl_doacao.setStyleSheet("font-size: 11px; font-weight: bold;")
        footer_layout.addWidget(lbl_doacao, alignment=Qt.AlignmentFlag.AlignRight)
        conteudo_layout.addLayout(footer_layout)

        self.stacked_widget.addWidget(page_dashboard)

        # PÁGINA 1: CONFIGURAÇÕES DE API
        page_settings = QWidget()
        settings_layout = QVBoxLayout(page_settings)
        settings_layout.setContentsMargins(40, 30, 40, 20)
        settings_layout.addWidget(QLabel("<h2>Sistemas de Inteligência Artificial</h2><p style='color: #94a3b8;'>Gerencie as chaves de comunicação (APIs) da ferramenta.</p>"))
        
        grupo_api = QGroupBox("🔑 Chaves de API (Salvas Automaticamente)")
        grupo_api.setObjectName("GrupoConfig")
        layout_api = QGridLayout(grupo_api)
        layout_api.setVerticalSpacing(20)
        
        layout_api.addWidget(QLabel("Chave Principal (Gemini):"), 0, 0)
        self.input_gemini = QLineEdit()
        self.input_gemini.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_gemini.setText(self.settings.value("api_gemini", ""))
        self.input_gemini.textChanged.connect(lambda: self.settings.setValue("api_gemini", self.input_gemini.text()))
        layout_api.addWidget(self.input_gemini, 0, 1)

        layout_api.addWidget(QLabel("Provedor Redundância:"), 1, 0)
        box_secundario = QHBoxLayout()
        self.combo_provedor = QComboBox()
        self.combo_provedor.addItems(["OpenRouter", "OpenAI", "DeepSeek"])
        self.combo_provedor.setCurrentText(self.settings.value("api_provedor", "OpenRouter"))
        self.combo_provedor.currentTextChanged.connect(lambda: self.settings.setValue("api_provedor", self.combo_provedor.currentText()))
        box_secundario.addWidget(self.combo_provedor)

        self.input_secundaria = QLineEdit()
        self.input_secundaria.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_secundaria.setPlaceholderText("Cole a chave de redundância aqui...")
        self.input_secundaria.setText(self.settings.value("api_secundaria", ""))
        self.input_secundaria.textChanged.connect(lambda: self.settings.setValue("api_secundaria", self.input_secundaria.text()))
        box_secundario.addWidget(self.input_secundaria)
        layout_api.addLayout(box_secundario, 1, 1)
        
        settings_layout.addWidget(grupo_api)
        settings_layout.addStretch()
        self.stacked_widget.addWidget(page_settings)

    def mudar_pagina(self, index):
        self.stacked_widget.setCurrentIndex(index)
        if index == 0:
            self.btn_nav_dashboard.setObjectName("NavBtnActive")
            self.btn_nav_config.setObjectName("NavBtn")
        else:
            self.btn_nav_dashboard.setObjectName("NavBtn")
            self.btn_nav_config.setObjectName("NavBtnActive")
        self.btn_nav_dashboard.style().unpolish(self.btn_nav_dashboard)
        self.btn_nav_dashboard.style().polish(self.btn_nav_dashboard)
        self.btn_nav_config.style().unpolish(self.btn_nav_config)
        self.btn_nav_config.style().polish(self.btn_nav_config)

    def aplicar_tema_moderno(self):
        # NOTA: Ajustei o gradiente do botão principal para tons de "Vermelho/Escuro" mais policiais/forenses
        estilo = """
        QMainWindow, QDialog { background-color: #0f111a; }
        #Sidebar { background-color: #09090b; border-right: 1px solid #1f2937; }
        #Conteudo { background-color: #0f111a; }
        
        #NavBtn { background-color: transparent; color: #94a3b8; text-align: left; padding: 12px; border-radius: 6px; font-weight: bold; border: none; font-size: 13px;}
        #NavBtn:hover { background-color: #1e293b; color: white; }
        #NavBtnActive { background-color: #1e293b; color: white; text-align: left; padding: 12px; border-radius: 6px; font-weight: bold; border: 1px solid #334155; font-size: 13px;}
        
        #Card { background-color: #18181b; border: 1px solid #27272a; border-radius: 10px; }
        #GrupoConfig { color: #ef4444; font-weight: bold; border: 1px solid #27272a; border-radius: 10px; margin-top: 15px; background-color: #18181b;}
        #GrupoConfig::title { subcontrol-origin: margin; left: 15px; padding: 0 5px; }
        
        QLabel { color: #e2e8f0; font-family: "Segoe UI"; }
        
        QComboBox, QLineEdit { background-color: #27272a; color: white; border: 1px solid #3f3f46; border-radius: 5px; padding: 8px 10px; }
        QComboBox::drop-down { border: none; }
        
        QTextBrowser { background-color: transparent; border: none; color: #e2e8f0; }
        
        #BtnGerarPrimario { 
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ef4444, stop:1 #b91c1c); 
            color: white; font-weight: bold; font-size: 13px; border-radius: 6px; padding: 0 20px;
        }
        #BtnGerarPrimario:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #dc2626, stop:1 #991b1b); }
        #BtnGerarPrimario:disabled { background: #475569; color: #94a3b8; }
        
        #BtnSecundario { background-color: #27272a; color: white; border: 1px solid #3f3f46; font-weight: bold; border-radius: 6px; font-size: 13px;}
        #BtnSecundario:hover { background-color: #3f3f46; }
        
        #AlternativaContainer { background-color: #18181b; border: 1px solid #27272a; border-radius: 8px; margin-bottom: 5px; }
        #AlternativaContainer:hover { border: 1px solid #ef4444; background-color: #201b2b; }
        QRadioButton { color: #e2e8f0; }
        
        #Explicacao { background-color: #1e293b; color: #f8fafc; border: 1px solid #334155; border-radius: 8px; padding: 25px; font-size: 14px; }
        """
        self.setStyleSheet(estilo)

    def _chamar_gemini_nativo(self, prompt, api_key):
        if not api_key: raise ValueError("Chave Gemini vazia.")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return response.text

    def _chamar_secundaria(self, prompt, provedor, api_key):
        if not api_key: raise ValueError("Chave Secundária vazia.")
        if provedor == "OpenAI":
            url, modelo = "https://api.openai.com/v1/chat/completions", "gpt-4o-mini"
        elif provedor == "DeepSeek":
            url, modelo = "https://api.deepseek.com/chat/completions", "deepseek-chat"
        else:
            url, modelo = "https://openrouter.ai/api/v1/chat/completions", "google/gemini-2.5-flash" 

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {"model": modelo, "messages": [{"role": "user", "content": prompt}]}
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status() 
        return response.json()['choices'][0]['message']['content']

    def gerar_questao(self):
        chave_gemini = self.settings.value("api_gemini", "").strip()
        chave_sec = self.settings.value("api_secundaria", "").strip()
        provedor_sec = self.settings.value("api_provedor", "OpenRouter")

        if not chave_gemini and not chave_sec:
            QMessageBox.warning(self, "Aviso", "Acesse a aba 'Configurações (API)' no menu lateral e insira pelo menos uma chave para começar.")
            self.mudar_pagina(1)
            return

        disciplina = self.combo_disciplina.currentText()
        banca = self.combo_banca.currentText()
        self.btn_gerar.setText("Analisando Local de Crime...")
        self.btn_gerar.setEnabled(False)
        self.lbl_status_api.setText("Processando...")
        QApplication.processEvents()

        prompt = f"""
        Você é um examinador sênior de Inteligência Policial, especialista na elaboração de provas para o cargo de PERITO CRIMINAL das Polícias Civis (foco na doutrina exigida pela {banca} para a PCPE e PCPB).
        Gere UMA questão inédita e de altíssimo nível (nível superior) de múltipla escolha (com 5 alternativas: a, b, c, d, e) sobre a disciplina: {disciplina}.
        
        REGRAS RIGOROSAS:
        1. ADERÊNCIA: O assunto DEVE refletir o grau de exigência dos últimos editais de Perito Criminal da PCPE e PCPB. Foco em provas, cadeia de custódia, vestígios, balística, asfixiologia, traumatologia forense ou jurisprudência aplicada aos crimes.
        2. ESTILO: Simule questões complexas, elaborando um curto caso concreto ou "situação hipotética" de local de crime, seguida da pergunta técnica.
        3. DIFICULDADE: Nível avançado. Cobre a letra da lei atualizada (Pacote Anticrime) ou o entendimento dos tribunais superiores.
        
        Retorne EXCLUSIVAMENTE em formato JSON (sem markdown de formatação), com a estrutura:
        {{
            "enunciado": "Texto da questão",
            "alternativas": ["a) texto", "b) texto", "c) texto", "d) texto", "e) texto"],
            "resposta_correta_index": 2, 
            "explicacao": "Explicação técnica, baseada na lei, doutrina ou jurisprudência.",
            "local_apostila": "Indique a lei ou doutrinador de referência (Ex: CPP Art. 158-A, ou França, Genival Veloso)",
            "termo_pesquisa_youtube": "Termo exato sugerido para pesquisar aula no YouTube"
        }}
        """
        texto_bruto, origem_api = "", ""
        try:
            texto_bruto = self._chamar_gemini_nativo(prompt, chave_gemini)
            origem_api = "Gerado via: Google Gemini Nativo"
        except Exception as erro_primario:
            print(f"[LOG] Falha no Gemini: {erro_primario}.")
            self.lbl_status_api.setText(f"Gemini falhou. Acionando {provedor_sec}...")
            QApplication.processEvents()
            try:
                texto_bruto = self._chamar_secundaria(prompt, provedor_sec, chave_sec)
                origem_api = f"Gerado via: {provedor_sec} (Redundância)"
            except Exception as erro_secundario:
                QMessageBox.critical(self, "Falha Geral", "Ambas as APIs falharam. Verifique suas chaves e o pacote de internet.")
                self.btn_gerar.setText("✨ Gerar Questão")
                self.btn_gerar.setEnabled(True)
                self.lbl_status_api.setText("Falha na geração.")
                return

        try:
            texto_limpo = texto_bruto.replace('```json', '').replace('```', '').strip()
            self.questao_atual = json.loads(texto_limpo)
            self.lbl_status_api.setText(origem_api)
            self.exibir_questao()
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Erro", "A IA não retornou um formato válido. Clique em gerar novamente.")
            self.lbl_status_api.setText("Erro de formatação (JSON).")
        finally:
            self.btn_gerar.setText("✨ Gerar Questão")
            self.btn_gerar.setEnabled(True)

    def exibir_questao(self):
        self.grupo_alternativas.setExclusive(False)
        alts_originais = self.questao_atual['alternativas']
        
        for i, alt in enumerate(self.alternativas_ui):
            alt['radio'].setChecked(False)
            alt['container'].setStyleSheet("#AlternativaContainer { border: 1px solid #27272a; background-color: #18181b; }")
            if i < len(alts_originais):
                alt['label'].setText(alts_originais[i])
                alt['container'].show()
            else:
                alt['container'].hide()
                
        self.grupo_alternativas.setExclusive(True)
        self.display_enunciado.setHtml(f"<div style='line-height: 1.5;'>{self.questao_atual['enunciado']}</div>")
        self.btn_responder.show()

    def verificar_resposta(self):
        if self.grupo_alternativas.checkedId() == -1:
            QMessageBox.warning(self, "Atenção", "Selecione uma alternativa antes de analisar os vestígios!")
            return

        id_selecionado = self.grupo_alternativas.checkedId()
        id_correto = self.questao_atual['resposta_correta_index']
        letras = ['A', 'B', 'C', 'D', 'E']

        for i, alt in enumerate(self.alternativas_ui):
            texto_base = self.questao_atual['alternativas'][i]
            if i == id_correto:
                alt['label'].setText(f"✅ {texto_base}")
                alt['container'].setStyleSheet("#AlternativaContainer { border: 1px solid #10b981; background-color: #064e3b; }")
            elif i == id_selecionado and id_selecionado != id_correto:
                alt['label'].setText(f"❌ {texto_base}")
                alt['container'].setStyleSheet("#AlternativaContainer { border: 1px solid #ef4444; background-color: #7f1d1d; }")

        if id_selecionado == id_correto:
            prefixo = "✅ <b style='color: #10b981; font-size: 16px;'>EXCELENTE! Análise Correta!</b><br><br>"
        else:
            prefixo = f"❌ <b style='color: #ef4444; font-size: 16px;'>INCORRETO.</b> O parecer correto correspondia à letra <b>{letras[id_correto]}</b>.<br><br>"

        termo_yt = self.questao_atual['termo_pesquisa_youtube'].replace(' ', '+')
        link_yt = f"https://www.youtube.com/results?search_query={termo_yt}"
        
        html_explicacao = f"""
        <div style="line-height: 1.6;">
            {prefixo}
            <b style='color: #ef4444; font-size: 15px;'>Fundamentação Técnica (Banca):</b><br>
            {self.questao_atual['explicacao']}<br><br>
            <b>⚖️ Base Legal/Doutrinária:</b> {self.questao_atual['local_apostila']}<br>
            <b>📺 Aprofunde no YouTube:</b> <a href="{link_yt}" style="color: #60a5fa;">Pesquisar jurisprudência/aula sobre: "{self.questao_atual['termo_pesquisa_youtube']}"</a>
        </div>
        """
        
        dialog = JanelaExplicacao(self, html_explicacao)
        dialog.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = GeradorQuestoesApp()
    janela.show()
    sys.exit(app.exec())