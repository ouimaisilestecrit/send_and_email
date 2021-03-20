# Comment faire ?

## Première utilisation :

### S'assurer que Chrome soit votre navigateur par défaut

### Déplacer l'utilitaire Chromedriver dans Program Files

* ouvrir le répertoire "utils" se trouvant dans le dossier principal
* puis faire un clic droit sur "chromedriver.exe" et choisir copier
* aller dans le répertoire "C:\Program Files (x86)\"
* puis faire un clic droit dans ce répertoire et choisir coller

## Comment ajouter un nouveau destinataire :

* ouvrir le fichier `users_info.inf` du répertoire conf
* éditer une nouvelle ligne selon le format : `Prénom=email`
  Exemple: `David=davidnabais7@gmail.com`
* enregistrer et quitter le fichier `users_info.inf`

## Comment mettre à jour Chrome :

* ouvrir le navigateur Chrome, puis dans le menu d'options (icône en 3 points - "Personnaliser et contrôler Google Chrome") choisir `Aide > À propos de Chrome` ;
* constater la mention `Google Chrome est à jour`, sinon mettre à jour le navigateur, puis relever la version à jour :
    Exemple : `Version 88.0.4324.104 (Build officiel) (64 bits)`

## Comment mettre à jour Webdriver de Chrome :

* aller sur internet, au site de téléchargement de Webdriver : `https://chromedriver.chromium.org/downloads`,
* puis télécharger une version correspondant à celle de votre navigateur Chrome :
    Exemple : `Si le numéro de la version de Chrome est 88, alors veuillez télécharger la version de ChromeDriver 88.0.4324.96`
* ouvrir le répertoire de téléchargement, faire un clic droit sur "chromedriver.exe" et choisir copier
* ouvrir le répertoire "C:\Program Files (x86)\" où est installé l'ancienne version
* puis faire un clic droit dans ce répertoire et choisir coller
* dans la fenêtre "Remplacer ou ignorer les fichiers", cliquer sur "Remplacer le fichier dans la destination"

## Comment ajouter un créneau d'exécution :

Le créneau est formé de deux paramètres : le jour et l'heure d'exécution.

* ouvrir le fichier `execution_time.inf` du répertoire conf :

    - pour ajouter le jour d'exécution, repérer la ligne commençant par `jour=`, et saisir des jours parmi les sept jours de la semaine en les séparant par une virgule.
        Ex. : jour=lundi,mardi,jeudi
    - pour ajouter l'heure d'exécution, repérer la ligne commençant par `heure=`, et saisir une heure dans le format suivant `hh:mm`.
        Ex. : heure=06:15,12:00,17:09

* enregistrer et quitter le fichier `execution_time.inf`

# Conseils pratiques ?

* l'accumulation des logs peut causer un ralentissement, vider les périodiquement, en supprimant dans le répertoire log, le fichier se terminant par ".log", ce dernier est créé à chaque lancement de l'outil.
