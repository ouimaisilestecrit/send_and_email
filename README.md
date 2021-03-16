# Comment faire ?

## Première utilisation :

### S'assurer que Chrome soit votre navigateur par défaut

### Déplacer l'utilitaire Chromedriver dans Program Files

* ouvrir le répertoire "utils" se trouvant dans le dossier principal
* puis faire un clic droit sur "chromedriver.exe" et choisir copier
* aller dans le répertoire "C:\Program Files (x86)\"
* puis faire un clic droit dans ce répertoire et choisir coller

## Comment ajouter un nouveau destinataire

* ouvrir le fichier `users_info.inf` du répertoire conf
* éditer une nouvelle ligne selon le format : `Prénom=email`
  Exemple: `David=davidnabais7@gmail.com`
* enregistrer et quitter le fichier `users_info.inf`

## Comment mettre à jour Chrome

* ouvrir le navigateur Chrome, puis dans le menu d'options (icône en 3 points - "Personnaliser et contrôler Google Chrome") choisir `Aide > À propos de Chrome` ;
* constater la mention `Google Chrome est à jour`, sinon mettre à jour le navigateur, puis relever la version à jour :
    Exemple : `Version 88.0.4324.104 (Build officiel) (64 bits)`

## Comment mettre à jour Webdriver de Chrome

* aller sur internet, au site de téléchargement de Webdriver : `https://chromedriver.chromium.org/downloads`,
* puis télécharger une version correspondant à celle de votre navigateur Chrome :
    Exemple : `Si le numéro de la version de Chrome est 88, alors veuillez télécharger la version de ChromeDriver 88.0.4324.96`
* ouvrir le répertoire de téléchargement, faire un clic droit sur "chromedriver.exe" et choisir copier
* ouvrir le répertoire "C:\Program Files (x86)\" où est installé l'ancienne version
* puis faire un clic droit dans ce répertoire et choisir coller
* dans la fenêtre "Remplacer ou ignorer les fichiers", cliquer sur "Remplacer le fichier dans la destination"
