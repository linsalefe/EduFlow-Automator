# 🚀 EduFlow Automator

Sistema de automação de conteúdo para Instagram da **[EduFlow IA](https://eduflowia.com/)** - empresa especializada em agentes de IA para faculdades, escolas e instituições de ensino.

## 🎯 Objetivo

Gerar automaticamente posts educativos e de alta conversão para:
- Educar o mercado sobre agentes de IA na educação
- Demonstrar autoridade e expertise
- Captar leads de instituições de ensino
- Fortalecer a marca EduFlow IA no Instagram

## 📋 Funcionalidades

- ✅ Geração automática de posts usando Gemini AI
- ✅ Design profissional alinhado à identidade visual EduFlow
- ✅ Integração com Pexels para backgrounds premium
- ✅ Publicação automática no Instagram (@eduflow.ia)
- ✅ Detecção de conteúdo duplicado
- ✅ Sistema de agendamento (3 posts/dia)
- ✅ Logging estruturado com rotação de arquivos
- 🚧 Geração de carrosséis (em desenvolvimento)
- 🚧 Vídeos curtos para Reels (planejado)

## 🛠️ Stack

- **Python 3.10+**
- **Gemini 2.0 Flash** (Google AI)
- **Pillow** (geração de imagens)
- **Instagrapi** (publicação Instagram)
- **Pexels API** (banco de imagens)
- **SQLite** (histórico de conteúdo)

## 📦 Instalação
```bash
# Clone o repositório
git clone <seu-repo>
cd EduFlow-Automator

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
# Edite o .env com suas credenciais (Gemini, Instagram, Pexels)

# Inicialize o banco de dados
python database/init_db.py
```

## 🔑 Configuração

### APIs Necessárias

1. **Gemini API**: https://aistudio.google.com/app/apikey
2. **Pexels API**: https://www.pexels.com/api/
3. **Instagram**: credenciais da conta @eduflow.ia

### Estrutura de Pastas
```
EduFlow-Automator/
├── assets/
│   ├── raw/            # Logo EduFlow, fontes Inter, backgrounds
│   ├── processed/      # Posts gerados
│   └── temp/           # Sessões temporárias
├── config/             # Configurações (cores, tamanhos, paths)
├── database/           # SQLite + repositório
├── logs/               # Logs rotacionados
├── prompts/            # Templates de prompts IA
└── src/
    ├── generators/     # Gemini (ideias, legendas), Pexels
    ├── processors/     # ImageEditor (arte dos posts)
    └── publishers/     # Instagram API
```

## 🚀 Uso

### Gerar um post manualmente
```bash
python main.py
```

### Executar scheduler (automação diária)
```bash
# 3 posts/dia nos horários: 09:00, 12:00, 18:00
python scheduler.py
```

### Testar componentes
```bash
# Testar geração de ideia + legenda (Gemini)
python test_gemini.py

# Testar geração de arte visual
python test_image_editor.py

# Testar busca de backgrounds
python test_pexels.py

# Testar upload no Instagram
python test_instagram_upload.py
```

## 📊 Banco de Dados

Histórico de conteúdo em `database/content_history.db`:
- **Previne duplicatas** (hash SHA256)
- **Rastreia status**: created → rendered → published
- **Armazena metadata**: ideia original, legenda, média_id do Instagram

## 🎨 Design System

### Template "Estacio Like" (padrão)
Baseado na identidade visual EduFlow:
- **Header**: Gradiente indigo (#1e1b4b → #4338ca) com logo
- **Card glass**: Fundo translúcido com blur
- **Tipografia**: Inter (ExtraBold para títulos)
- **Cores**: Indigo (#6366f1) como primária, white + accent
- **Logo**: Logo EduFlow sem fundo com glow sutil

### Estrutura do Post
```
┌─────────────────────────────────┐
│  [HEADER: Logo + "EduFlow IA"]  │ ← Branding fixo
├─────────────────────────────────┤
│                                 │
│   [Background Pexels + Blur]    │ ← Imagem contextual
│                                 │
│  ┌───────────────────────────┐  │
│  │  Kicker (angle do tópico) │  │
│  │  TÍTULO PRINCIPAL         │  │ ← Card glass
│  │  Subtítulo explicativo    │  │
│  │  👉 CTA                   │  │
│  └───────────────────────────┘  │
│                                 │
└─────────────────────────────────┘
```

## 📝 Logs

Logs em `logs/eduflow.log`:
- Rotação automática (10MB/arquivo, 5 backups)
- Formato: `timestamp | level | module:line | message`
- Console + arquivo sincronizados

## 🔒 Segurança

- ✅ Credenciais em `.env` (não commitado no Git)
- ✅ Sessão Instagram em cache (evita captchas)
- ✅ Rate limiting em APIs (retry exponencial)
- ✅ Validação de duplicatas antes de publicar

## 🎯 Nichos de Conteúdo

Foco em tópicos que convertem para o público B2B educacional:
- Desafios de gestão em instituições de ensino
- Benefícios de IA na educação
- Cases de sucesso de automação
- Dicas práticas para coordenadores/diretores
- Desmistificação de tecnologias educacionais

## 🏢 Sobre a EduFlow IA

**EduFlow IA** desenvolve agentes de inteligência artificial especializados para instituições de ensino:
- Atendimento automatizado 24/7
- Captação de leads qualificados
- Suporte acadêmico via WhatsApp/chat
- Integração com CRMs e sistemas acadêmicos

🌐 **Site**: [eduflowia.com](https://eduflowia.com/)  
📱 **Instagram**: [@eduflow.ia](https://instagram.com/eduflow.ia)

## 📄 Licença

© 2025 EduFlow IA - Todos os direitos reservados.  
Projeto proprietário para uso interno.