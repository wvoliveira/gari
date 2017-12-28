[![build status](https://travis-ci.org/wvoliveira/gari.svg?branch=master)](https://travis-ci.org/wvoliveira/gari)

Gari
----

Aplicação para remover snapshots há mais de N dias do VCenter ou AWS

Problema conhecido
---

Quando vamos realizar alguma tarefa que precisa atualizar o sistema operacional/aplicação e corre o risco de parar o serviço, temos que tirar snapshot para caso de problemas pós atualização termos como voltar no tempo, normalizar o serviço e pensar melhor no processo de atualização dessa VM.
Nisso, esquecemos de remover e só percebemos quando precisamos, mas a remoção desses snapshots é muito lenta, então caso seja necessário certa urgencia, teremos que esperar ~20 minutos (imagem pequena).

Ideias
---

- Script parametrizado;
- Arquivo de configuração;
- Verifica se existe snapshots há mais de N dias no VCenter ou AWS;
- Envia notificação caso haja alguma ação.

"Announcing your plans is a good way to hear god laugh." - Al Swearengen 

Done v1.0
---

Testado no python2.7 

```
./gari.py --help
  
usage: gari.py [-h] -d -c -w [-f]
  
Remove snapshots da AWS e do VCenter
https://github.com/wvoliveira/gari.git
  
optional arguments:
  -h, --help            show this help message and exit
  -d, --datacenter      vcenter or aws
  -c, --config          config file
  -w, --whitelist       whitelist file
  -f, --force           force remove

```

Parâmetros:

-d ou --datacenter: A listagem dos snapshots no VCenter demora muito, então tive que parametrizar o datacenter também. Então você terá que escolher VCenter ou AWs.  
-c ou --config: Arquivo de configuracao. Terá que ter os mesmos parâmetros do exemplo do projeto (env-example.ini).  
-w ou --whitelist: Arquivo que conterá os nomes das máquinas ou os ids dos snapshots da AWS. `Atenção aqui`: Se for VMs do VCENTER, deverá colocar os nomes delas, se for snapshots da AWS, deverá colocar os IDs dos mesmos, pois na AWS é aceitável deixar snapshots sem ter a VM que a originou.  
-f ou --force: Força a exclusão dos snapshots. Sem ele só irá mostrar a mensagem que 'removeria'.  


Exemplo:

```
pip2.7 -r requirements.txt
python2.7 gari.py -d vcenter -c configuracao_vcenter.ini -w whitelist_vcenter.txt
python2.7 gari.py -d aws -c configuracao_aws.ini -w whitelist_aws.txt
```
