<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel - Grupo Covem</title>
    <style>
        :root {
            --bg-dark: #0f1117;
            --card-dark: #161922;
            --border-dark: #2a2e3d;
            --text-main: #ffffff;
            --text-muted: #9a9ea7;
            
            /* Paleta de Cores do Funil */
            --funil-1: #c000c0; /* Contatado */
            --funil-2: #d99b00; /* Conversando */
            --funil-3: #e65100; /* Reunião Agendada */
            --funil-4: #0083a8; /* Proposta Enviada */
            --funil-5: #10a345; /* Fechado */
            --funil-6: #d32f2f; /* Perdido */
        }

        body {
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 24px;
        }

        /* 1. TOPO: GRUPO COVEM */
        .header-section {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-dark);
        }

        .header-title {
            font-size: 28px;
            font-weight: 800;
            letter-spacing: 1px;
            margin: 0;
        }

        .btn-novo-cadastro {
            background-color: #2563eb;
            color: #fff;
            border: none;
            padding: 10px 18px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }

        .btn-novo-cadastro:hover {
            background-color: #1d4ed8;
        }

        /* 2. CENTRAL DE ALERTAS */
        .alertas-section {
            background-color: var(--card-dark);
            border: 1px solid var(--border-dark);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 28px;
        }

        .section-title {
            font-size: 18px;
            font-weight: 700;
            margin-top: 0;
            margin-bottom: 14px;
        }

        .alertas-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
        }

        .alerta-card {
            background-color: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-dark);
            padding: 12px;
            border-radius: 6px;
            cursor: pointer;
            transition: border-color 0.2s;
        }

        .alerta-card:hover {
            border-color: #3b82f6;
        }

        /* 3. FUNIL DE VENDAS */
        .funil-section {
            margin-bottom: 28px;
        }

        .funil-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 12px;
            overflow-x: auto;
        }

        /* ABAS COLORIDAS: Fonte aumentada e em negrito */
        .funil-aba {
            padding: 12px 8px;
            border-radius: 6px;
            font-size: 16px; /* Aumentado para melhor leitura */
            font-weight: 700; /* Bold */
            text-align: center;
            color: #ffffff;
            margin-bottom: 12px;
            white-space: nowrap;
        }

        .aba-1 { background-color: var(--funil-1); }
        .aba-2 { background-color: var(--funil-2); }
        .aba-3 { background-color: var(--funil-3); }
        .aba-4 { background-color: var(--funil-4); }
        .aba-5 { background-color: var(--funil-5); }
        .aba-6 { background-color: var(--funil-6); }

        /* CARDS DOS CLIENTES: Visual original mantido */
        .cliente-card {
            background-color: var(--card-dark);
            border: 1px solid var(--border-dark);
            border-radius: 6px;
            padding: 10px;
            margin-bottom: 8px;
            font-size: 13px;
            color: var(--text-main);
            cursor: pointer;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            transition: border-color 0.2s;
        }

        .cliente-card:hover {
            border-color: #4b5563;
        }

        /* 4. GERENCIADOR DE TAREFAS */
        .tarefas-section {
            background-color: var(--card-dark);
            border: 1px solid var(--border-dark);
            border-radius: 8px;
            padding: 16px;
        }

        /* MODAL / ABA DE DETALHES DO CLIENTE */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }

        .modal-content {
            background-color: var(--card-dark);
            border: 1px solid var(--border-dark);
            border-radius: 8px;
            width: 400px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-dark);
            padding-bottom: 10px;
            margin-bottom: 16px;
        }

        .modal-header h3 { margin: 0; font-size: 18px; }
        .close-btn { cursor: pointer; font-size: 20px; color: var(--text-muted); }

        .info-row {
            margin-bottom: 12px;
            font-size: 14px;
        }

        .info-label {
            color: var(--text-muted);
            font-size: 12px;
            display: block;
            margin-bottom: 2px;
        }

        /* Status por Cores */
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-weight: 600;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 13px;
        }
        .status-verde { background: rgba(16, 163, 69, 0.2); color: #2ecc71; }
        .status-amarelo { background: rgba(217, 155, 0, 0.2); color: #f1c40f; }
        .status-vermelho { background: rgba(211, 47, 47, 0.2); color: #e74c3c; }
    </style>
</head>
<body>

    <!-- 1. TOPO: GRUPO COVEM -->
    <header class="header-section">
        <h1 class="header-title">GRUPO COVEM</h1>
        <button class="btn-novo-cadastro">➕ Novo Cadastro</button>
    </header>

    <!-- 2. CENTRAL DE ALERTAS -->
    <section class="alertas-section">
        <h2 class="section-title">Central de Alertas</h2>
        <div class="alertas-grid">
            <div class="alerta-card">
                <span class="info-label">Tarefas Atrasadas</span>
                <strong>3 tarefas</strong>
            </div>
            <div class="alerta-card">
                <span class="info-label">Tarefas do Dia</span>
                <strong>5 tarefas</strong>
            </div>
            <div class="alerta-card">
                <span class="info-label">Follow-ups Pendentes</span>
                <strong>2 clientes</strong>
            </div>
        </div>
    </section>

    <!-- 3. FUNIL DE VENDAS -->
    <section class="funil-section">
        <h2 class="section-title">Funil de Vendas</h2>
        <div class="funil-grid">
            <!-- Coluna 1 -->
            <div>
                <div class="funil-aba aba-1">1. Contatado</div>
                <div class="cliente-card" onclick="abrirDetalhes('Grupo Delta', 'Carlos Silva', 'Gerente de Compras', '(16) 99999-0001', 'Amanhã', 'verde')">
                    Grupo Delta (Follow-up)
                </div>
                <div class="cliente-card" onclick="abrirDetalhes('Sistemas Sigma', 'Ana Paula', 'Diretora de TI', '(16) 99999-0002', 'Hoje às 16h', 'amarelo')">
                    Sistemas Sigma (Follow-up)
                </div>
            </div>

            <!-- Coluna 2 -->
            <div>
                <div class="funil-aba aba-2">2. Conversando</div>
                <div class="cliente-card" onclick="abrirDetalhes('Indústria Omega', 'Roberto Alves', 'Supervisão', '(16) 99999-0003', 'Ontem (Atrasado)', 'vermelho')">
                    Indústria Omega (Follow-up)
                </div>
            </div>

            <!-- Coluna 3 -->
            <div>
                <div class="funil-aba aba-3">3. Reunião Agendada</div>
            </div>

            <!-- Coluna 4 -->
            <div>
                <div class="funil-aba aba-4">4. Proposta Enviada</div>
            </div>

            <!-- Coluna 5 -->
            <div>
                <div class="funil-aba aba-5">5. Fechado</div>
            </div>

            <!-- Coluna 6 -->
            <div>
                <div class="funil-aba aba-6">6. Perdido</div>
                <div class="cliente-card" onclick="abrirDetalhes('Tecnologia Beta', 'Lucas Prado', 'CEO', '(16) 99999-0004', 'Sem Ação', 'vermelho')">
                    Tecnologia Beta (Sem Ação)
                </div>
            </div>
        </div>
    </section>

    <!-- 4. GERENCIADOR DE TAREFAS -->
    <section class="tarefas-section">
        <h2 class="section-title">Gerenciador de Tarefas</h2>
        <p style="color: var(--text-muted); font-size: 14px;">Lista e controle operacional de tarefas do dia a dia.</p>
    </section>

    <!-- MODAL DE DETALHES DO CLIENTE (EXPANSÃO AO CLICAR) -->
    <div id="modalCliente" class="modal-overlay" onclick="fecharModalFora(event)">
        <div class="modal-content">
            <div class="modal-header">
                <h3 id="modalEmpresa">Nome da Empresa</h3>
                <span class="close-btn" onclick="fecharModal()">&times;</span>
            </div>
            <div class="info-row">
                <span class="info-label">Responsável</span>
                <strong id="modalContato">-</strong>
            </div>
            <div class="info-row">
                <span class="info-label">Cargo</span>
                <span id="modalCargo">-</span>
            </div>
            <div class="info-row">
                <span class="info-label">Telefone</span>
                <span id="modalTelefone">-</span>
            </div>
            <div class="info-row">
                <span class="info-label">Próximo Follow-up</span>
                <div id="modalStatusContainer">
                    <!-- Badge injetado dinamicamente -->
                </div>
            </div>
        </div>
    </div>

    <script>
        function abrirDetalhes(empresa, contato, cargo, telefone, followup, statusCor) {
            document.getElementById('modalEmpresa').innerText = empresa;
            document.getElementById('modalContato').innerText = contato;
            document.getElementById('modalCargo').innerText = cargo;
            document.getElementById('modalTelefone').innerText = telefone;

            const container = document.getElementById('modalStatusContainer');
            
            let corClasse = 'status-verde';
            let icone = '🟢';
            
            if (statusCor === 'amarelo') {
                corClasse = 'status-amarelo';
                icone = '🟡';
            } else if (statusCor === 'vermelho') {
                corClasse = 'status-vermelho';
                icone = '🔴';
            }

            container.innerHTML = `<span class="status-badge ${corClasse}">${icone} ${followup}</span>`;
            document.getElementById('modalCliente').style.display = 'flex';
        }

        function fecharModal() {
            document.getElementById('modalCliente').style.display = 'none';
        }

        function fecharModalFora(event) {
            if (event.target.id === 'modalCliente') {
                fecharModal();
            }
        }
    </script>
</body>
</html>
