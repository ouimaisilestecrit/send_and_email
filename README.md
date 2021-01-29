# Comment faire ?

## Comment ajouter un nouveau destinataire

* ouvrir le fichier `users_info.inf` du répertoire conf
* éditer une nouvelle ligne au format : `Prénom=email`
  Exemple: `David=davidnabais7@gmail.com`
* enregistrer et quitter le fichier `users_info.inf`

## Comment mettre à jour Chrome et Webdriver

* ouvrir le navigateur Chrome, puis dans le menu d'options (icône en 3 points - "Personnaliser et contrôler Google Chrome") choisir `Aide > À propos de Chrome` ;
* constater la mention `Google Chrome est à jour`, sinon mettre à jour le navigateur, puis relever la version à jour :
    Exemple : `Version 88.0.4324.104 (Build officiel) (64 bits)`
* aller sur le site de téléchargement de Webdriver : `https://chromedriver.chromium.org/downloads`, puis télécharger la version correspondant à la version du navigateur Chrome :
    Exemple : `If you are using Chrome version 88, please download ChromeDriver 88.0.4324.96`
* ouvrir le répertoire `C:\Program Files (x86)\chromedriver.exe` où est installé l'ancienne, et remplacer cette version par celle nouvellement téléchargée.
