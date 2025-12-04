# elenie
code de http://meteoflow.plumegeo.fr

Cette application a été développée comme un petit prototype pour réfléchir à des idées de géovisualisation liée à la dynamique du camp de réfugiés à Grande-Synthe, développé en 2023 avec des données d'observation de l'été 2022. 
Conception  : Elenie Sarciat et Christine Plumejeaud-Perreau, UMR 7301 Migrinter

> Elenie SARCIAT (elenie.sarciat@ulb.be)
 Doctorante en socio-anthropologie à l'Université Libre de Bruxelles (ULB)
 Laboratoire d'Anthropologie des Mondes Contemporain (LAMC)
 Co-animatrice séminaire Anthropologie Bruxelles/ Brussels Anthropology (ABBA)

> Christine Plumejeaud-Perreau (christine.perreau@univ-poitiers.fr)
 Ingénieure de recherche, https://orcid.org/0000-0001-9271-3355
 Migrations internationales, Espaces et Sociétés, (MIGRINTER), UMR 7301
 TSA n°21103,
 Bat A5, 0.13
 5, rue Théodore Lefebvre
 86073 POITIERS CEDEX 9

Un article cite ce travail et recontextualise le camp. 
```
Thomas Lacroix, « L’usage politique de l’environnement dans la fabrique des frontières : l’écotone migratoire de Calais », e-Migrinter [En ligne], 25 | 2025, mis en ligne le 01 avril 2025, consulté le 04 décembre 2025. URL : http://journals.openedition.org/e-migrinter/4956 ; DOI : https://doi.org/10.4000/13r3d
```

## Installation sur un serveur (VM sur Ubuntu Noble)

Copié sur le serveur via WinSCP (connexion SSH sur port 22)
Code dans /home/cperreau/elenie

Structure du répertoire : 

- requirements_venv.txt
- elenie.conf : à installer dans /etc/apache2/sites-available/elenie.conf
- meteoflow/
  - ressources/
  - templates/
  - elenie.py
  - meteoflow.wsgi

### Config Python et WSGI

Installation d'un environnement virtuel pour python 3.10 dans ce répertoire
`cd ~`
`python3.10  -m venv elenie/py310-venv`

Environnement virtuel dans : 
- /home/cperreau/elenie/py310-venv

- **Ajout du path python dans le programme elenie.py**
```py
if platform == "linux" or platform == "linux2":
    # linux
    #sys.path.append('/opt/tljh/user/lib/python3.7/site-packages')
    sys.path.append('/home/cperreau/elenie/py310-venv/lib/python3.10/site-packages/')
```

**lancer le programme depuis l'environnement virtuel à la main**

`cd ~/elenie/meteoflow`

**entrer**

`source py310-venv/bin/activate`

**installer des packages listés dans un fichier requirements_venv.txt**

`pip3 install -r ../requirements_venv.txt`

**intaller le module WSGI**

Il requiert python3.10-dev (`sudo apt-get install python3.10-dev`)

`pip install mod_wsgi --use-pep517` renvoie "Successfully installed **mod_wsgi-5.0.2**"

Une vérification s'impose : pour apache2, quel WSGI va s'exécuter ? Utiliser cette information pour adapter ensuite le fichier elenie.conf qui configure la webapp pour Apache.

`mod_wsgi-express module-config`
```sh
LoadModule wsgi_module "/home/cperreau/elenie/py310-venv/lib/python3.10/site-packages/mod_wsgi/server/mod_wsgi-py310.cpython-310-x86_64-linux-gnu.so"
WSGIPythonHome "/home/cperreau/elenie/py310-venv"
```

**lancer la webapp depuis venv**

python3 /home/cperreau/elenie/meteoflow/elenie.py

**sortir** : `deactivate`

### Vérifier que Flask marche bien (sans Apache2)

**lancer la webapp en dehors de venv avec nohup**

Il faut démarrer le site à la main : port 8086
`nohup /home/cperreau/elenie/py310-venv/bin/python3.10 /home/cperreau/elenie/meteoflow/elenie.py > out.txt &`

**tester avec wget**

Se placer dans un répertoire de test 
`cd /home/cperreau/elenie/test`

`wget http://localhost:8086`

Bonne réponse
```sh
  cperreau@romarin:~/elenie/test$ wget http://localhost:8086
  --2025-12-04 16:15:05--  http://localhost:8086/
  Resolving localhost (localhost)... 127.0.0.1
  Connecting to localhost (localhost)|127.0.0.1|:8086... connected.
  HTTP request sent, awaiting response... 200 OK
  Length: 4032720 (3,8M) [text/html]
  Saving to: ‘index.html.1’
  
  index.html.1                             100%[===============================================================================>]   3,85M  --.-KB/s    in 0,003s
  
  2025-12-04 16:15:05 (1,31 GB/s) - ‘index.html.1’ saved [4032720/4032720]
```

Mauvaise réponse
```sh
--2025-12-02 18:06:52--  http://localhost:8086/
Resolving localhost (localhost)... 127.0.0.1
Connecting to localhost (localhost)|127.0.0.1|:8086... connected.
HTTP request sent, awaiting response... 500 INTERNAL SERVER ERROR
2025-12-02 18:06:52 ERROR 500: INTERNAL SERVER ERROR.
```

Examiner les logs
`tail -f out.txt`

Le serveur écoute bien sur le port 8086 ? **netstat**

`netstat -na | grep 8086`
```sh
tcp        0      0 127.0.0.1:8086          0.0.0.0:*               LISTEN
```

**tuer un processus si nécessaire**

Si vous voulez relancer le serveur sans avoir supprimé cette instance qui tourne encore, vous allez à l'échec.

`nohup /home/cperreau/elenie/py310-venv/bin/python3.10 /home/cperreau/elenie/meteoflow/elenie.py > out.txt &`
```sh
Address already in use
Port 8086 is in use by another program. Either identify and stop that program, or start the server with a different port.
```
Si vous avez ce message, c'est que l'ancien processus qui exécute votre code tourne encore. Il faut le killer. 

Trouver le numéro du processus : 47013 (père de 38362)

`ps -ef | grep elenie.py` cherche le processus qui contient elenie.py dans son nom (avec `grep`) après avoir listé tous les processus (`ps -ef`)
```sh
cperreau   38362       1  0 déc.02 ?      00:00:00 /home/cperreau/elenie/py37-venv/bin/python3.7 elenie.py
cperreau   47013   38362  4 08:48 ?        00:00:15 /home/cperreau/elenie/py37-venv/bin/python3.7 /home/cperreau/elenie/meteoflow/elenie.py
cperreau   47792   46859  0 08:55 pts/0    00:00:00 grep --color=auto elenie.py
```

Tuer le processus père : 
`kill -9 38362`: tue le processus numéro 38362

### configurer Apache2 et la webapp

Supprimer mes Ctrl^M génants de Windows parfois
```sh
for fic in $(find /home/cperreau/elenie/meteoflow -type f -name "*.py"); do sudo dos2unix $fic; done
```

Attention, il faut qu'Apache2 (user :www-data) ait accès à votre environnement virtuel (en lecture et exécution, r+x)

```sh
sudo chown :www-data /home/cperreau/elenie/ -R
sudo chmod 755 /home/cperreau/elenie/ -R
sudo chmod 755 /home/cperreau
```

Lier les sources à un répertoire fictif apache

`sudo ln -s  /home/cperreau/elenie/meteoflow /var/www/elenie`

DNS : meteoflow.plumegeo.fr - créer un mapping sur votre fournisseurs de DNS  : CNAME avec 	`romarin.huma-num.fr.`

Copier et adapter le fichier de config de l'environnement virtuel (elenie.conf) dans /etc/apache2/sites-available

`sudo a2ensite elenie` Pour démarrer la webapp

`sudo a2dissite elenie` Pour retirer la webapp

`sudo systemctl reload apache2` pour recharger la config et le code de la Webapp

`sudo systemctl restart apache2.service` pour stopper/redémarrer apache2

`sudo systemctl status apache2.service` : état du service Apache2

`sudo vi /var/log/apache2/error.log` : debugger et regarder les traces de la webapp
