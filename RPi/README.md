# urban_monitoring

Software di monitoraggio del traffico stradale.

## Kafka

Per loggare i dati con kafka è necessario abilitarlo e configurarlo nell'apposita sezione del file config.ini.

## Raspberry PI

### Installazione

```bash
sudo apt-get update

sudo apt-get install python3-opencv python3-numpy

echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
sudo apt-get update
sudo apt-get install python3-tflite-runtime
pip3 install kafka-python

git clone https://gitlab.com/plumake/urban_monitoring.git

# Installazione e avvio del daemon
cd urban_monitoring/daemon
chmod +x install.sh
sudo ./install.sh
```

### Comandi

Dalla directory principale del progetto eseguire lo script *./startMonitoring.sh*.
Se non sono specivficati parametri verrà avviato il normale monitoring nel terminale corrente.
Parametri:

- **gate**: avvia il programma di disegno dei gate. Da eseguire con l'interfaccia grafica attiva.
  
- **debug**: avvia il monotoring in modalità debug. Tutte le immagini elaborate verranno salvate nella directory predefinita. Da eseguire con l'interfaccia grafica attiva.

- **gui**: avvia il monitoring con la visualizzazione del frame in finestra.

- **daemon**: parametro riservato per il daemon.

```bash
# Esempio
./startMonitoring.sh debug
```

### Gestione del daemon

Nel caso si voglia gestire manualemente il daemon si può utilizzare il comando *./daemon/daemonCmq.sh* con il parametro *start*, *stop*, *status per avviare, fermare e visualizzare lo stato corrente.
Alternativamente è sempre possibile utilizzare direttamente i comandi systemd.

### Utilità

Monitoraggio temperatura raspberry pi

```bash
watch -n 1 /opt/vc/bin/vcgencmd measure_temp
```

## Link utili

- https://www.youtube.com/watch?v=tPYj3fFJGjk&ab_channel=freeCodeCamp.org

- https://github.com/PacktPublishing/Tensorflow-2.0-Quick-Start-Guide/blob/master/Chapter01/Chapter1_TF2_alpha.ipynb

- https://github.com/google-coral/example-object-tracker

- https://github.com/bendidi/sort/blob/master/sort.py
