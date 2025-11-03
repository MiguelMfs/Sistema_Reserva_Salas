# 🧩 Sistema de Reserva de Salas — Arquitetura de Microsserviços

Este projeto implementa um *ecossistema de microsserviços* responsáveis por gerenciar o processo completo de *reserva de salas de aula*, desde a consulta de disponibilidade até o disparo de e-mails e eventos de calendário.

Cada serviço possui *responsabilidade única*, podendo ser executado e escalado de forma independente.

---

## 🗂️ Estrutura de Microsserviços

### 1 - Consulta de Sala de Aula → Responsável: Guilherme
*Objetivo:*  
Gerenciar e disponibilizar os dados de todas as salas cadastradas no sistema.

*Descrição:*  
Este microserviço armazena (em uma lista simulada) e disponibiliza informações como:
- Capacidade da sala;  
- Status de disponibilidade;  
- Identificação única de cada sala.

*Principais endpoints:*
- GET /salas — Lista todas as salas;  
- GET /salas/disponiveis — Retorna apenas as salas livres;  
- GET /salas/{id} — Retorna os detalhes de uma sala específica.

---

### 2 - Verificar Disponibilidade da Sala → Responsável: Hannely
*Objetivo:*  
Determinar se uma sala específica está disponível em um determinado intervalo de tempo.

*Descrição:*  
Este serviço mantém um “banco de dados simulado” com as reservas existentes e realiza verificações de conflito de horários.  
Ao receber uma requisição com o *ID da sala, **data, **hora de início e fim*, ele retorna:
- ✅ Disponível — se não houver sobreposição;  
- ❌ Indisponível — se já existir uma reserva nesse intervalo.

*Endpoint principal:*
- POST /verificar — Verifica a disponibilidade de uma sala com base nos horários enviados.

---

### 3️ - Disparo de Email → Responsável: Maria Antonia
*Objetivo:*  
Simular o envio de e-mails de confirmação de reservas.

*Descrição:*  
O serviço atua como uma “caixa de correio digital”, recebendo dados via POST /email e exibindo no console o conteúdo da mensagem enviada.

*Dados esperados:*
- Nome e e-mail do destinatário;  
- Nome da sala;  
- Data e horário da reserva.

*Comportamento:*  
Após o recebimento, o serviço imprime o conteúdo do e-mail no console e retorna uma mensagem de sucesso.

---

### 4️ - Gateway → Responsável: Rodrigo
*Objetivo:*  
Centralizar o acesso e a comunicação entre todos os microsserviços.

*Descrição:*  
O Gateway atua como *ponto único de entrada* do sistema.  
Ele é responsável por *rotear e orquestrar* as chamadas entre os serviços, simplificando o consumo da API por parte do cliente.

*Funções principais:*
- Roteamento das requisições para os serviços adequados;  
- Coordenação de fluxos complexos (como o processo completo de reserva).

*Fluxo orquestrado de reserva:*
1. Cliente faz POST /reservar no Gateway.  
2. Gateway → chama *Serviço de Consulta de Salas* (verifica dados).  
3. Gateway → chama *Serviço de Disponibilidade* (verifica se está livre).  
4. Gateway → chama *Serviço de Reserva* (registra a reserva).  
5. Gateway → chama *Serviço de E-mail* (envia confirmação).  
6. Gateway → chama *Serviço de Evento* (dispara evento de agenda).

---

### 5️ - Reservar Sala → Responsável: Julia
*Objetivo:*  
Registrar efetivamente a reserva no sistema e acionar o disparo de e-mail.

*Descrição:*  
Este microserviço recebe as informações da reserva (ID da sala, horário e responsável) e as registra internamente.  
Após o registro, ele notifica o *Serviço de E-mail* para enviar a confirmação ao solicitante.

*Endpoint principal:*
- POST /reservar — Registra uma nova reserva (após a confirmação de disponibilidade).

---

### 6️⃣ Disparo de Evento no E-mail → Responsável: Miguel
*Objetivo:*  
Gerar e enviar eventos de calendário (Google, Outlook, etc.) após a confirmação de reserva.

*Descrição:*  
Diferente do serviço de e-mail padrão, este microserviço gera e envia *convites de calendário* no formato .ics (iCalendar).  
Ele recebe os detalhes do evento e executa duas ações principais:

1. Gera um anexo .ics com os dados da reserva;  
2. Simula o envio de um e-mail real utilizando smtplib e MIMEMultipart.

*Endpoint principal:*
- POST /enviar_evento — Envia o e-mail com o evento anexado.

---

## 🔄 Fluxo Completo da Operação

```mermaid
sequenceDiagram
    participant Cliente
    participant Gateway
    participant Consulta as Consulta Sala
    participant Disp as Disponibilidade
    participant Reserva as Reservar Sala
    participant Email as Disparo Email
    participant Evento as Disparo Evento

    Cliente->>Gateway: POST /reservar (dados da reserva)
    Gateway->>Consulta: GET /salas/{id}
    Gateway->>Disp: POST /verificar (id_sala, data, hora)
    Disp-->>Gateway: Disponível
    Gateway->>Reserva: POST /reservar
    Reserva-->>Gateway: Reserva registrada
    Gateway->>Email: POST /email
    Email-->>Gateway: E-mail de confirmação enviado
    Gateway->>Evento: POST /enviar_evento
    Evento-->>Gateway: Evento de agenda enviado
    Gateway-->>Cliente: Confirmação final da reserva
