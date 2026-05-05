# 🏋️ GreenFit - Sistema de Catraca de Academia

API para gerenciamento de acesso de alunos em academia com controle de catraca por CPF.

## ✨ Funcionalidades

- ✅ Cadastro de alunos (nome, CPF, status)
- 🔍 Consulta de alunos por CPF (para catraca)
- 📊 Sistema de status: **Ativo**, **Inativo**, **Pendente**
- 🔐 Autenticação de administrador com JWT
- 🎯 Contador automático de alunos cadastrados
- 📱 API documentada com Swagger
- 🌐 Deploy na Vercel

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Descrição |
|------------|-----------|
| **Flask** | Framework web em Python |
| **Firebase Firestore** | Banco de dados NoSQL na nuvem |
| **JWT** | Autenticação de administrador |
| **Flask-CORS** | Liberação de acesso para o front-end |
| **Flasgger** | Documentação da API (Swagger) |
| **Vercel** | Hospedagem do back-end |

## 📋 Rotas da API

### 🌐 Rotas Públicas (não exigem token)

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/cadastro` | Cadastrar novo aluno |
| GET | `/consulta` | Listar todos os alunos |
| GET | `/consulta/<cpf>` | Consultar aluno por CPF (catraca) |
| POST | `/login` | Login do administrador |

### 🔒 Rotas Privadas (exigem token)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Mensagem de boas-vindas |
| GET | `/contador` | Ver total de alunos cadastrados |
| PATCH | `/editar/<cpf>` | Editar nome do aluno |
| PATCH | `/alterar-status/<cpf>` | Alterar status (Ativo/Inativo/Pendente) |
| PUT | `/substituir/<cpf>` | Substituir todos os dados |
| DELETE | `/excluir/<cpf>` | Excluir aluno |
| POST | `/resetar-contador` | Resetar contador (admin) |

## 🎯 Status do Aluno

| Status | Descrição | Acesso na Catraca |
|--------|-----------|-------------------|
| **Ativo** | Aluno com mensalidade em dia | ✅ **Liberado** |
| **Inativo** | Aluno com mensalidade atrasada | ❌ Negado |
| **Pendente** | Cadastro aguardando ativação | ❌ Negado |

## Autora: 
Ana Clara Mendes - SENAI DS

E-mail: ana.mendes.senai@gmail.com

Link da vercel do Projeto: https://academia-limpo.vercel.app/


Autora: NicollyOliveiraS
API FrontEnd Cliente: https://github.com/NicollyOliveiraS/academia
API FrontEnd Admin: https://github.com/NicollyOliveiraS/adm_gym



## 🚀 Como Executar o Projeto

### 1. Clone o repositório

```bash
git clone https://github.com/AnaClaraMendes399/Academia-Limpo.git
cd Academia-Limpo

