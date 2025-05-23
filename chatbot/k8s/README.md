# Implantação no Kubernetes

Este diretório contém os manifestos Kubernetes necessários para implantar o chatbot e o MongoDB no Minikube.

## Pré-requisitos

1. Minikube instalado e rodando
2. Docker instalado
3. kubectl configurado

## Passos para Implantação

### Windows (PowerShell)

1. Inicie o Minikube:
   ```powershell
   minikube start
   ```

2. Configure o Docker para usar o daemon do Minikube:
   ```powershell
   minikube docker-env | Invoke-Expression
   ```

3. Construa a imagem do chatbot:
   ```powershell
   docker build -t cnj-chatbot:latest .
   ```

4. Aplique os manifestos Kubernetes:
   ```powershell
   kubectl apply -f mongodb-deployment.yaml
   kubectl apply -f chatbot-deployment.yaml
   ```

5. Verifique o status dos pods:
   ```powershell
   kubectl get pods
   ```

6. Obtenha a URL do serviço:
   ```powershell
   minikube service chatbot --url
   ```

### Linux

1. Inicie o Minikube:
   ```bash
   minikube start
   ```

2. Configure o Docker para usar o daemon do Minikube:
   ```bash
   eval $(minikube docker-env)
   ```

3. Construa a imagem do chatbot:
   ```bash
   docker build -t cnj-chatbot:latest .
   ```

4. Aplique os manifestos Kubernetes:
   ```bash
   kubectl apply -f mongodb-deployment.yaml
   kubectl apply -f chatbot-deployment.yaml
   ```

5. Verifique o status dos pods:
   ```bash
   kubectl get pods
   ```

6. Obtenha a URL do serviço:
   ```bash
   minikube service chatbot --url
   ```

## Testando o Chatbot

Após a implantação, você pode testar o chatbot usando port-forward:

1. Em um terminal, execute o port-forward:
   ```bash
   kubectl port-forward service/chatbot 8000:80
   ```

2. Em outro terminal, você pode testar o chatbot usando curl:
   ```bash
   # Windows (PowerShell)
   curl -X POST "http://localhost:8000/chat" `
        -H "Content-Type: application/json" `
        -d '{\"message\": \"Quero consultar um processo\"}'

   # Linux
   curl -X POST "http://localhost:8000/chat" \
        -H "Content-Type: application/json" \
        -d '{"message": "Quero consultar um processo"}'
   ```

3. Para testar outras mensagens, basta alterar o texto dentro do campo "message".

## Solução de Problemas Comuns

### Erro de Pull da Imagem

Se você encontrar o erro:
```
Failed to pull image "cnj-chatbot:latest": Error response from daemon: pull access denied
```

Siga estes passos:

1. Certifique-se de que o Minikube está rodando:
   ```bash
   minikube status
   ```

2. Configure o ambiente Docker do Minikube:
   ```bash
   # Windows
   minikube docker-env | Invoke-Expression
   
   # Linux
   eval $(minikube docker-env)
   ```

3. Verifique se a imagem existe localmente:
   ```bash
   docker images | grep cnj-chatbot
   ```

4. Se a imagem não existir, reconstrua-a:
   ```bash
   docker build -t cnj-chatbot:latest .
   ```

5. Delete o pod do chatbot para forçar uma nova criação:
   ```bash
   kubectl delete pod -l app=chatbot
   ```

## Acessando o Dashboard do Kubernetes

O Minikube inclui um dashboard web que permite visualizar e gerenciar seus recursos Kubernetes de forma gráfica.

### Windows (PowerShell)

1. Inicie o dashboard:
   ```powershell
   minikube dashboard
   ```
   Isso abrirá automaticamente seu navegador padrão com o dashboard.

2. Se o navegador não abrir automaticamente, você pode obter a URL:
   ```powershell
   minikube dashboard --url
   ```

### Linux

1. Inicie o dashboard:
   ```bash
   minikube dashboard
   ```
   Isso abrirá automaticamente seu navegador padrão com o dashboard.

2. Se o navegador não abrir automaticamente, você pode obter a URL:
   ```bash
   minikube dashboard --url
   ```

### Recursos Disponíveis no Dashboard

No dashboard, você pode:
- Visualizar todos os pods, deployments e serviços
- Ver logs dos pods
- Executar comandos em shells dos pods
- Monitorar recursos (CPU, memória)
- Gerenciar configurações
- Visualizar eventos do cluster

## Estrutura dos Manifestos

- `mongodb-deployment.yaml`: Contém a configuração do MongoDB, incluindo:
  - Deployment do MongoDB
  - Service do MongoDB
  - PersistentVolumeClaim para armazenamento

- `chatbot-deployment.yaml`: Contém a configuração do chatbot, incluindo:
  - Deployment do chatbot
  - Service do chatbot (LoadBalancer)

## Notas Importantes

1. O MongoDB está configurado para usar um PersistentVolumeClaim para manter os dados entre reinicializações.
2. O chatbot está configurado para se conectar ao MongoDB usando o nome do serviço `mongodb`.
3. O serviço do chatbot está configurado como LoadBalancer para permitir acesso externo.
4. As variáveis de ambiente do chatbot estão configuradas para apontar para o MongoDB.

## Solução de Problemas

Se encontrar problemas:

1. Verifique os logs dos pods:
   ```bash
   # Windows
   kubectl logs -f <pod-name>
   
   # Linux
   kubectl logs -f <pod-name>
   ```

2. Verifique o status dos serviços:
   ```bash
   # Windows
   kubectl get services
   
   # Linux
   kubectl get services
   ```

3. Verifique os eventos do cluster:
   ```bash
   # Windows
   kubectl get events
   
   # Linux
   kubectl get events
   ```

4. Se precisar reiniciar o Minikube:
   ```bash
   # Windows
   minikube stop
   minikube start
   
   # Linux
   minikube stop
   minikube start
   ```

5. Para limpar tudo e começar do zero:
   ```bash
   # Windows
   minikube delete
   minikube start
   
   # Linux
   minikube delete
   minikube start
   ``` 